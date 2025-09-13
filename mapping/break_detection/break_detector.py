# break_detector.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from scipy.stats import f  # for Chow tests


class BreakDetector:
    """Detect structural breaks in time series for hypothesis evaluation.

    Defaults:
      - Forces ICD-based segments at (Oct 1 2015, Oct 1 2016) if they fall in the focus window.
      - Set force_icd_segments=False to use automatic detection.

    Focusing:
      - If focus_start is None, use the dataset's earliest date.
      - If focus_end is None, use the dataset's latest date.
    """

    def __init__(
        self,
        icd_transition_date="2015-10-01",
        focus_start=None,
        focus_end=None,
        force_icd_segments=True,
        max_breaks=2,
    ):
        self.icd_transition = pd.Timestamp(icd_transition_date)
        self.focus_start = None if focus_start is None else pd.Timestamp(focus_start)
        self.focus_end = None if focus_end is None else pd.Timestamp(focus_end)
        self.force_icd_segments = force_icd_segments
        self.max_breaks = max_breaks
        self.last_fig = None

    def detect_breaks(
        self,
        time_series_data,
        date_col="date",
        value_col=None,
        hypothesis_name="",
        plot_results=True,
    ):
        """Main entry: detect breaks (or force ICD segments) within the focus window."""
        # Prepare data
        ts_data = time_series_data.copy()
        ts_data[date_col] = pd.to_datetime(ts_data[date_col])
        ts_data = ts_data.sort_values(date_col).reset_index(drop=True)

        # Auto-detect value column if not provided
        if value_col is None:
            value_cols = [
                col
                for col in ts_data.columns
                if "rolling" in col.lower() or "count" in col.lower()
            ]
            if value_cols:
                value_col = value_cols[0]
            else:
                numeric_cols = ts_data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) == 0:
                    raise ValueError("No numeric column found to use as value_col.")
                value_col = numeric_cols[0]

        if len(ts_data) == 0:
            print("⚠️  No data available.")
            return {
                "break_points": [],
                "break_dates": [],
                "segments": [],
                "total_breaks": 0,
                "break_score": 0,
                "value_column": value_col,
                "icd_transition_alignment": [],
                "focus_range": "n/a",
                "global_fit": None,
                "global_ssr": None,
                "segments_ssr": None,
                "global_chow_F": None,
                "global_chow_p": None,
                "local_chow": [],
            }

        # Resolve focus window to dataset edges when None
        data_min, data_max = ts_data[date_col].min(), ts_data[date_col].max()
        effective_start = data_min if self.focus_start is None else self.focus_start
        effective_end = data_max if self.focus_end is None else self.focus_end

        # Filter to focus range
        mask = (ts_data[date_col] >= effective_start) & (
            ts_data[date_col] <= effective_end
        )
        focused_data = ts_data[mask].copy()

        if len(focused_data) == 0:
            print("⚠️  No data in focus range.")
            return {
                "break_points": [],
                "break_dates": [],
                "segments": [],
                "total_breaks": 0,
                "break_score": 0,
                "value_column": value_col,
                "icd_transition_alignment": [],
                "focus_range": f"{effective_start.date()} to {effective_end.date()}",
                "global_fit": None,
                "global_ssr": None,
                "segments_ssr": None,
                "global_chow_F": None,
                "global_chow_p": None,
                "local_chow": [],
            }

        dates = focused_data[date_col].reset_index(drop=True)
        values = focused_data[value_col].reset_index(drop=True)

        print(
            f"🔍 Analyzing {len(focused_data)} points in focus: {effective_start.date()} → {effective_end.date()}"
        )

        # --- Global (single-line) regression across the focused window ---
        global_fit = self._fit_global(dates, values)
        # Predicted values for global line (used for SSR / plotting)
        date_numeric_all = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
        global_pred = global_fit["model"].predict(date_numeric_all)
        global_ssr = self._ssr(values, global_pred)

        # Decide segmentation mode
        if self.force_icd_segments:
            # Preserve the ICD "middle section" cuts if they fall within the focus window
            forced_cut_dates = [pd.Timestamp("2015-10-01"), pd.Timestamp("2016-10-01")]
            forced_cut_indices = []
            for cut_date in forced_cut_dates:
                if dates.min() <= cut_date <= dates.max():
                    idx = int(dates.searchsorted(cut_date))
                    # searchsorted returns insertion index; keep only interior cuts
                    if 0 < idx < len(dates):
                        forced_cut_indices.append(idx)
            break_indices = sorted(set(forced_cut_indices))
        else:
            # Automatic detection path
            break_indices = self._find_break_points(values)
            if len(break_indices) > self.max_breaks:
                print(
                    f"⚠️  Limiting from {len(break_indices)} detected breaks to {self.max_breaks} most significant."
                )
                break_indices = self._prioritize_breaks(break_indices, dates)
            # ensure valid interior indices
            break_indices = [int(i) for i in break_indices if 0 < i < len(values)]

        # Build segments from indices
        segments = []
        all_indices = [0] + break_indices + [len(values)]
        for i in range(len(all_indices) - 1):
            start_idx = all_indices[i]
            end_idx = all_indices[i + 1]
            if end_idx - start_idx >= 2:  # Need at least 2 points to fit
                seg_stats = self._fit_segment(dates, values, start_idx, end_idx)
                if seg_stats:
                    segments.append(seg_stats)

        # SSR for piecewise segments (sum of each segment's residuals)
        segments_ssr = 0.0
        for seg in segments:
            seg_mask = (dates >= seg["start_date"]) & (dates <= seg["end_date"])
            seg_dates = dates[seg_mask]
            seg_values = values[seg_mask]
            if len(seg_dates) == 0:
                continue
            seg_num = np.array([d.toordinal() for d in seg_dates]).reshape(-1, 1)
            seg_pred = seg["model"].predict(seg_num)
            segments_ssr += self._ssr(seg_values, seg_pred)

        # Score and package results
        break_dates = [dates.iloc[i] for i in break_indices if 0 <= i < len(dates)]
        break_score = self._calculate_break_score(segments, dates)

        # --- Chow tests ---
        # (A) Global multi-break Chow: one line vs s segment-specific lines
        n = len(values)
        k = 2  # intercept + slope for simple linear regression
        s = max(1, len(segments))  # number of segments (>=1)
        global_F, global_p = self._chow_test_multi(
            n=n, k=k, s=s, ssr_restricted=global_ssr, ssr_unrestricted=segments_ssr
        )

        # (B) Local per-break Chow: for each break, fit two lines around that cut
        local_chow = []
        for b_idx in break_indices:
            F_loc, p_loc = self._local_chow_for_break(dates, values, b_idx, k=2)
            if F_loc is not None:
                local_chow.append(
                    {
                        "break_index": int(b_idx),
                        "break_date": dates.iloc[b_idx],
                        "F": F_loc,
                        "p": p_loc,
                    }
                )

        results = {
            "break_points": break_indices,
            "break_dates": break_dates,
            "segments": segments,
            "total_breaks": len(break_indices),
            "break_score": break_score,
            "value_column": value_col,
            "icd_transition_alignment": self._check_icd_transition_alignment(
                break_dates
            ),
            "focus_range": f"{effective_start.date()} to {effective_end.date()}",
            "global_fit": global_fit,
            "global_ssr": global_ssr,
            "segments_ssr": segments_ssr,
            "global_chow_F": global_F,
            "global_chow_p": global_p,
            "local_chow": local_chow,
        }

        # Output and plot (unchanged) — BUT now we capture & remember the Figure
        if plot_results:
            fig = self._plot_results(
                dates,
                values,
                results,
                hypothesis_name,
                value_col,
                effective_start,
                effective_end,
            )
            self.last_fig = fig
        else:
            self.last_fig = None

        return results

    # ---------- Helpers ----------

    def _find_break_points(self, values):
        """Conservative change detection using large relative jumps."""
        if len(values) <= 4:
            return []
        changes = np.abs(np.diff(values) / (np.array(values[:-1]) + 1e-10))
        threshold = np.mean(changes) + 3 * np.std(changes)
        return [i + 1 for i, change in enumerate(changes) if change > threshold]

    def _prioritize_breaks(self, break_indices, dates):
        """Keep the most relevant breaks (closest to ICD transition and spaced apart)."""
        if not break_indices:
            return []
        break_dates = []
        for i in break_indices:
            if 0 <= i < len(dates):
                break_dates.append(dates.iloc[i])
            else:
                break_dates.append(None)
        distances = [
            abs((d - self.icd_transition).days) if d is not None else np.inf
            for d in break_dates
        ]
        closest_idx = int(np.argmin(distances))
        prioritized = [break_indices[closest_idx]]
        for i, b_idx in enumerate(break_indices):
            if i == closest_idx:
                continue
            if 0 <= b_idx < len(dates):
                days_diff = abs((dates.iloc[b_idx] - dates.iloc[prioritized[0]]).days)
                if days_diff > 90:
                    prioritized.append(b_idx)
                    break
        return prioritized[: self.max_breaks]

    def _fit_segment(self, dates, values, start_idx, end_idx):
        """Fit linear regression to [start_idx, end_idx) using date ordinals -> slope per year."""
        segment_dates = dates.iloc[start_idx:end_idx]
        segment_values = values.iloc[start_idx:end_idx]
        if len(segment_values) < 2:
            return None
        date_numeric = np.array([d.toordinal() for d in segment_dates]).reshape(-1, 1)
        model = LinearRegression()
        model.fit(date_numeric, segment_values)
        predictions = model.predict(date_numeric)
        slope_per_year = float(model.coef_[0]) * 365.25
        r2 = float(r2_score(segment_values, predictions))
        return {
            "start_date": segment_dates.iloc[0],
            "end_date": segment_dates.iloc[-1],
            "slope": slope_per_year,
            "r_squared": r2,
            "length": len(segment_dates),
            "mean_value": float(segment_values.mean()),
            "std_value": float(segment_values.std(ddof=0)),
            "model": model,
            "start_idx": int(start_idx),
            "end_idx": int(end_idx),
        }

    def _fit_global(self, dates, values):
        """Fit a single OLS line across the entire focused window."""
        return self._fit_segment(dates, values, 0, len(values))

    def _ssr(self, y_true, y_hat):
        err = np.asarray(y_true) - np.asarray(y_hat)
        return float(np.sum(err**2))

    def _calculate_break_score(self, segments, all_dates):
        """Quality metric: weighted variance of segments normalized by overall date variance."""
        if len(segments) <= 1:
            return 0.0
        total_variance = 0.0
        total_length = 0
        for seg in segments:
            seg_var = seg["std_value"] ** 2
            total_variance += seg_var * seg["length"]
            total_length += seg["length"]
        if total_length == 0:
            return float("inf")
        overall_variance = np.array([d.toordinal() for d in all_dates]).var()
        return float((total_variance / total_length) / (overall_variance + 1e-10))

    def _check_icd_transition_alignment(self, break_dates):
        """Return an alignment score (0..1) indicating closeness to ICD transition (6-month window)."""
        alignments = []
        for bd in break_dates:
            days_diff = abs((bd - self.icd_transition).days)
            alignments.append(max(0.0, 1.0 - (days_diff / 180.0)))
        return alignments

    # ---------- Chow tests ----------

    def _chow_test_multi(self, n, k, s, ssr_restricted, ssr_unrestricted):
        """
        Generalized Chow test for multiple breaks (s segments).
        Restricted model: single regression over all data (k params).
        Unrestricted model: s segment-specific regressions (s*k params).
        F = ((SSR_r - SSR_ur) / ((s-1)*k)) / (SSR_ur / (n - s*k))
        """
        if s <= 1 or n <= s * k:
            return None, None
        num_df = (s - 1) * k
        den_df = n - s * k
        num = (ssr_restricted - ssr_unrestricted) / max(num_df, 1)
        den = ssr_unrestricted / max(den_df, 1)
        if den <= 0:
            return np.inf, 0.0
        F_stat = num / den
        p_val = 1 - f.cdf(F_stat, dfn=num_df, dfd=den_df)
        return F_stat, p_val

    def _local_chow_for_break(self, dates, values, break_idx, k=2):
        """
        Classic Chow at a single break index (two-segment comparison).
        Returns (F, p). If not enough points on either side, returns (None, None).
        """
        n = len(values)
        if not (0 < break_idx < n - 1):
            return None, None
        # Need at least k+1 points per side to fit (be conservative)
        left_n = break_idx
        right_n = n - break_idx
        if left_n < (k + 1) or right_n < (k + 1):
            return None, None

        # Build X, y
        X = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
        y = values.values

        # Split
        X1, y1 = X[:break_idx], y[:break_idx]
        X2, y2 = X[break_idx:], y[break_idx:]

        # Fit OLS
        m_full = LinearRegression().fit(X, y)
        m1 = LinearRegression().fit(X1, y1)
        m2 = LinearRegression().fit(X2, y2)

        # SSRs
        ssr_full = np.sum((y - m_full.predict(X)) ** 2)
        ssr1 = np.sum((y1 - m1.predict(X1)) ** 2)
        ssr2 = np.sum((y2 - m2.predict(X2)) ** 2)
        ssr_ur = ssr1 + ssr2

        # Classic Chow for single break (s=2)
        num_df = k  # (s-1)*k with s=2
        den_df = n - 2 * k
        if den_df <= 0:
            return None, None
        num = (ssr_full - ssr_ur) / num_df
        den = ssr_ur / den_df
        if den <= 0:
            return np.inf, 0.0
        F_stat = num / den
        p_val = 1 - f.cdf(F_stat, dfn=num_df, dfd=den_df)
        return float(F_stat), float(p_val)

    # ---------- Output & Plot ----------

    def _print_results(self, results, hypothesis_name):
        """Console-friendly summary of the detection run."""
        print(f"\n🔍 BREAK ANALYSIS: '{hypothesis_name}'")
        print("=" * 60)
        print(f"Focus Range: {results['focus_range']}")
        print(f"Break Score: {results['break_score']:.4f} (lower is better)")
        print(f"Detected {results['total_breaks']} structural break(s)")

        # Global fit block
        gf = results.get("global_fit", None)
        if gf:
            print(f"\n🌐 Global Fit (entire focus window):")
            print(f"  Slope: {gf['slope']:+.2f} units/year")
            print(f"  R²: {gf['r_squared']:.3f}")
            if "global_ssr" in results and "segments_ssr" in results:
                print(f"  SSR (global):   {results['global_ssr']:.2f}")
                print(f"  SSR (segments): {results['segments_ssr']:.2f}")
                delta = results["global_ssr"] - results["segments_ssr"]
                print(f"  ΔSSR (global - segments): {delta:.2f}")
            if results.get("global_chow_F") is not None:
                Fg = results["global_chow_F"]
                pg = results["global_chow_p"]
                print(
                    f"  Chow (one line vs {max(1,len(results['segments']))} segments): "
                    f"F={Fg:.2f}, p={pg:.4g}"
                )

        # Break dates and (optional) local Chow tests
        if results["break_dates"]:
            print("\n🧩 Breakpoints:")
            # Map date -> local Chow if available
            local_by_date = {
                lc["break_date"].date(): lc for lc in results.get("local_chow", [])
            }
            for i, (bd, align) in enumerate(
                zip(results["break_dates"], results["icd_transition_alignment"])
            ):
                icd_info = f" (ICD alignment: {align:.2f})" if align > 0.3 else ""
                line = f"Break {i+1}: {bd.date()}{icd_info}"
                lc = local_by_date.get(bd.date())
                if lc is not None:
                    line += f" | Local Chow: F={lc['F']:.2f}, p={lc['p']:.4g}"
                print(line)
        else:
            print("No break dates to report (forced ICD segments may still be used).")

        print("\n📊 SEGMENT ANALYSIS:")
        for i, seg in enumerate(results["segments"]):
            trend = (
                "↑ INCLINE"
                if seg["slope"] > 0
                else "↓ DECLINE" if seg["slope"] < 0 else "→ FLAT"
            )
            print(
                f"\nSegment {i+1}: {seg['start_date'].date()} to {seg['end_date'].date()} {trend}"
            )
            print(f"  Slope: {seg['slope']:+.2f} units/year")
            print(f"  R²: {seg['r_squared']:.3f}")
            print(f"  Mean: {seg['mean_value']:.2f}")
            print(f"  Length: {seg['length']} data points")
            if i > 0:
                prev = results["segments"][i - 1]
                slope_change = seg["slope"] - prev["slope"]
                mean_change = seg["mean_value"] - prev["mean_value"]
                print(
                    f"  Change from previous: Slope Δ={slope_change:+.2f}, Mean Δ={mean_change:+.2f}"
                )

    def _plot_results(
        self,
        dates,
        values,
        results,
        hypothesis_name,
        value_col,
        effective_start,
        effective_end,
    ):
        """Plot data and segment regressions for the focus window; return Figure for logging."""
        fig, ax = plt.subplots(figsize=(12, 6))  # CHANGED: capture fig/ax
        ax.plot(dates, values, "o-", label=value_col, alpha=0.6, markersize=4)

        # Global line across the entire focus window
        if "global_fit" in results and results["global_fit"] is not None:
            date_numeric_all = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
            global_pred = results["global_fit"]["model"].predict(date_numeric_all)
            ax.plot(
                dates,
                global_pred,
                linestyle="--",
                linewidth=2,
                label=f'Global fit (slope: {results["global_fit"]["slope"]:+.2f}/yr)',
            )

        colors = ["red", "green", "purple", "orange", "brown"]
        for i, seg in enumerate(results["segments"]):
            seg_mask = (dates >= seg["start_date"]) & (dates <= seg["end_date"])
            seg_dates = dates[seg_mask]
            seg_values = values[seg_mask]
            if len(seg_dates) == 0:
                continue
            date_numeric = np.array([d.toordinal() for d in seg_dates]).reshape(-1, 1)
            predicted = seg["model"].predict(date_numeric)
            ax.plot(
                seg_dates,
                predicted,
                color=colors[i % len(colors)],
                linewidth=3,
                label=f'Segment {i+1} (slope: {seg["slope"]:+.2f}/yr)',
            )
            ax.plot(
                seg_dates,
                seg_values,
                "o",
                color=colors[i % len(colors)],
                markersize=3,
                alpha=0.5,
            )

        # Mark break points (vertical lines)
        for bd in results["break_dates"]:
            ax.axvline(x=bd, color="black", linestyle="--", alpha=0.7, linewidth=2)
            ax.text(
                bd,
                ax.get_ylim()[1] * 0.95,
                f"Break\n{bd.date()}",
                ha="center",
                va="top",
                rotation=90,
                backgroundcolor="white",
                fontweight="bold",
            )

        # Mark ICD transition and the one-year middle cut if inside focus
        ax.axvline(
            x=self.icd_transition,
            color="blue",
            linestyle="-",
            alpha=0.6,
            label="ICD-10 Transition",
            linewidth=2,
        )
        middle_cut = pd.Timestamp("2016-10-01")
        if dates.min() <= middle_cut <= dates.max():
            ax.axvline(
                x=middle_cut, color="blue", linestyle="-", alpha=0.4, linewidth=2
            )

        # Focus boundaries
        ax.axvline(x=effective_start, color="gray", linestyle=":", alpha=0.3)
        ax.axvline(x=effective_end, color="gray", linestyle=":", alpha=0.3)

        ax.set_title(
            f"Break Analysis: {hypothesis_name}\nFocus: {effective_start.date()} to {effective_end.date()}"
        )
        ax.set_xlabel("Date")
        ax.set_ylabel(value_col)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        fig.tight_layout()

        plt.show()  
        return fig   


# Global instance: defaults to forcing ICD-based segments; no explicit focus -> full dataset
break_detector = BreakDetector(force_icd_segments=True)

# break_detector.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from scipy import stats

class BreakDetector:
    """Detect structural breaks in time series for hypothesis evaluation.

    By default this instance will force ICD-based segments (Oct 1 2015,
    Oct 1 2016). Set force_icd_segments=False to use automatic detection.
    """

    def __init__(self, icd_transition_date='2015-10-01',
                 focus_start='2014-01-01', focus_end='2017-12-31',
                 force_icd_segments=True, max_breaks=2):
        self.icd_transition = pd.Timestamp(icd_transition_date)
        self.focus_start = pd.Timestamp(focus_start)
        self.focus_end = pd.Timestamp(focus_end)
        self.force_icd_segments = force_icd_segments
        self.max_breaks = max_breaks

    def detect_breaks(self, time_series_data, date_col='date', value_col=None,
                      hypothesis_name="", plot_results=True):
        """Main entry: detect breaks (or force ICD segments) in focus range."""
        # Prepare data
        ts_data = time_series_data.copy()
        ts_data[date_col] = pd.to_datetime(ts_data[date_col])
        ts_data = ts_data.sort_values(date_col).reset_index(drop=True)

        # Auto-detect value column if not provided
        if value_col is None:
            value_cols = [col for col in ts_data.columns if 'rolling' in col.lower() or 'count' in col.lower()]
            if value_cols:
                value_col = value_cols[0]
            else:
                numeric_cols = ts_data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) == 0:
                    raise ValueError("No numeric column found to use as value_col.")
                value_col = numeric_cols[0]

        # Filter to focus range
        mask = (ts_data[date_col] >= self.focus_start) & (ts_data[date_col] <= self.focus_end)
        focused_data = ts_data[mask].copy()

        if len(focused_data) == 0:
            print("⚠️  No data in focus range.")
            return {
                'break_points': [],
                'break_dates': [],
                'segments': [],
                'total_breaks': 0,
                'break_score': 0,
                'value_column': value_col,
                'icd_transition_alignment': [],
                'focus_range': f"{self.focus_start.date()} to {self.focus_end.date()}"
            }

        dates = focused_data[date_col].reset_index(drop=True)
        values = focused_data[value_col].reset_index(drop=True)

        print(f"🔍 Analyzing {len(focused_data)} data points in focus range: {self.focus_start.date()} to {self.focus_end.date()}")

        # Decide segmentation mode
        if self.force_icd_segments:
            # Force the three ICD-related segments
            forced_cut_dates = [pd.Timestamp("2015-10-01"), pd.Timestamp("2016-10-01")]
            # Only include cut dates that fall within the focused data range
            forced_cut_indices = []
            for cut_date in forced_cut_dates:
                if dates.min() <= cut_date <= dates.max():
                    idx = int(dates.searchsorted(cut_date))
                    # searchsorted returns insertion index; ensure it's between 1 and len-1
                    if 0 < idx < len(dates):
                        forced_cut_indices.append(idx)

            break_indices = sorted(set(forced_cut_indices))

        else:
            # Automatic detection path
            break_indices = self._find_break_points(values)
            if len(break_indices) > self.max_breaks:
                print(f"⚠️  Limiting from {len(break_indices)} detected breaks to {self.max_breaks} most significant.")
                break_indices = self._prioritize_breaks(break_indices, dates)
            # ensure indices are valid ints within [1, len(values)-1]
            break_indices = [int(i) for i in break_indices if 0 < i < len(values)]

        # Build segments from indices
        segments = []
        all_indices = [0] + break_indices + [len(values)]
        for i in range(len(all_indices) - 1):
            start_idx = all_indices[i]
            end_idx = all_indices[i + 1]
            # Need at least 2 points to fit
            if end_idx - start_idx >= 2:
                seg_stats = self._fit_segment(dates, values, start_idx, end_idx)
                if seg_stats:
                    segments.append(seg_stats)

        # Score and package results
        break_dates = [dates.iloc[i] for i in break_indices if 0 <= i < len(dates)]
        break_score = self._calculate_break_score(segments, dates)

        results = {
            'break_points': break_indices,
            'break_dates': break_dates,
            'segments': segments,
            'total_breaks': len(break_indices),
            'break_score': break_score,
            'value_column': value_col,
            'icd_transition_alignment': self._check_icd_transition_alignment(break_dates),
            'focus_range': f"{self.focus_start.date()} to {self.focus_end.date()}"
        }

        # Output and plot
        self._print_results(results, hypothesis_name)
        if plot_results:
            self._plot_results(dates, values, results, hypothesis_name, value_col)

        return results

    def _find_break_points(self, values):
        """Conservative change detection using large relative jumps."""
        if len(values) <= 4:
            return []

        # relative changes between consecutive points
        changes = np.abs(np.diff(values) / (np.array(values[:-1]) + 1e-10))

        # threshold: mean + 3*std to avoid over-detection
        threshold = np.mean(changes) + 3 * np.std(changes)
        potential_breaks = [i + 1 for i, change in enumerate(changes) if change > threshold]
        return potential_breaks

    def _prioritize_breaks(self, break_indices, dates):
        """Keep the most relevant breaks (closer to ICD transition and not too close to each other)."""
        if not break_indices:
            return []

        # Convert indices to dates (safely)
        break_dates = []
        for i in break_indices:
            if 0 <= i < len(dates):
                break_dates.append(dates.iloc[i])
            else:
                break_dates.append(None)

        # distance to ICD transition
        distances = [abs((d - self.icd_transition).days) if d is not None else np.inf for d in break_dates]
        closest_idx = int(np.argmin(distances))
        prioritized = [break_indices[closest_idx]]

        # try to add another break that's not within 90 days
        for i, b_idx in enumerate(break_indices):
            if i == closest_idx:
                continue
            if 0 <= b_idx < len(dates):
                days_diff = abs((dates.iloc[b_idx] - dates.iloc[prioritized[0]]).days)
                if days_diff > 90:
                    prioritized.append(b_idx)
                    break

        return prioritized[:self.max_breaks]

    def _fit_segment(self, dates, values, start_idx, end_idx):
        """Fit linear regression to [start_idx, end_idx) using date ordinals -> slope per year."""
        segment_dates = dates.iloc[start_idx:end_idx]
        segment_values = values.iloc[start_idx:end_idx]

        if len(segment_values) < 2:
            return None

        # Convert dates to numeric (ordinal) so slope is interpretable per year
        date_numeric = np.array([d.toordinal() for d in segment_dates]).reshape(-1, 1)
        model = LinearRegression()
        model.fit(date_numeric, segment_values)
        predictions = model.predict(date_numeric)

        slope_per_year = float(model.coef_[0]) * 365.25  # convert per-day coefficient to per-year
        r2 = float(r2_score(segment_values, predictions))

        return {
            'start_date': segment_dates.iloc[0],
            'end_date': segment_dates.iloc[-1],
            'slope': slope_per_year,
            'r_squared': r2,
            'length': len(segment_dates),
            'mean_value': float(segment_values.mean()),
            'std_value': float(segment_values.std(ddof=0)),
            'model': model,
            'start_idx': int(start_idx),
            'end_idx': int(end_idx)
        }

    def _calculate_break_score(self, segments, all_dates):
        """Quality metric: weighted variance of segments normalized by overall date variance."""
        if len(segments) <= 1:
            return 0.0

        total_variance = 0.0
        total_length = 0
        for seg in segments:
            seg_var = (seg['std_value'] ** 2)
            total_variance += seg_var * seg['length']
            total_length += seg['length']

        if total_length == 0:
            return float('inf')

        overall_variance = np.array([d.toordinal() for d in all_dates]).var()
        break_score = (total_variance / total_length) / (overall_variance + 1e-10)
        return float(break_score)

    def _check_icd_transition_alignment(self, break_dates):
        """Return an alignment score (0..1) indicating closeness to ICD transition (6-month window)."""
        alignments = []
        for bd in break_dates:
            days_diff = abs((bd - self.icd_transition).days)
            alignment = max(0.0, 1.0 - (days_diff / 180.0))  # 180 days -> 6 months
            alignments.append(alignment)
        return alignments

    def _print_results(self, results, hypothesis_name):
        """Console-friendly summary of the detection run."""
        print(f"\n🔍 BREAK ANALYSIS: '{hypothesis_name}'")
        print("=" * 60)
        print(f"Focus Range: {results['focus_range']}")
        print(f"Break Score: {results['break_score']:.4f} (lower is better)")
        print(f"Detected {results['total_breaks']} structural break(s)")

        if results['break_dates']:
            for i, (bd, align) in enumerate(zip(results['break_dates'], results['icd_transition_alignment'])):
                icd_info = f" (ICD alignment: {align:.2f})" if align > 0.3 else ""
                print(f"Break {i+1}: {bd.date()}{icd_info}")
        else:
            print("No break dates to report (forced ICD segments may still be used).")

        print("\n📊 SEGMENT ANALYSIS:")
        for i, seg in enumerate(results['segments']):
            trend = "↑ INCLINE" if seg['slope'] > 0 else "↓ DECLINE" if seg['slope'] < 0 else "→ FLAT"
            print(f"\nSegment {i+1}: {seg['start_date'].date()} to {seg['end_date'].date()} {trend}")
            print(f"  Slope: {seg['slope']:+.2f} units/year")
            print(f"  R²: {seg['r_squared']:.3f}")
            print(f"  Mean: {seg['mean_value']:.2f}")
            print(f"  Length: {seg['length']} data points")
            if i > 0:
                prev = results['segments'][i - 1]
                slope_change = seg['slope'] - prev['slope']
                mean_change = seg['mean_value'] - prev['mean_value']
                print(f"  Change from previous: Slope Δ={slope_change:+.2f}, Mean Δ={mean_change:+.2f}")

    def _plot_results(self, dates, values, results, hypothesis_name, value_col):
        """Plot data and segment regressions for the focused range."""
        plt.figure(figsize=(12, 6))
        plt.plot(dates, values, 'o-', label=value_col, alpha=0.6, markersize=4)

        colors = ['red', 'green', 'purple', 'orange', 'brown']
        for i, seg in enumerate(results['segments']):
            seg_mask = (dates >= seg['start_date']) & (dates <= seg['end_date'])
            seg_dates = dates[seg_mask]
            seg_values = values[seg_mask]

            if len(seg_dates) == 0:
                continue

            date_numeric = np.array([d.toordinal() for d in seg_dates]).reshape(-1, 1)
            predicted = seg['model'].predict(date_numeric)

            plt.plot(seg_dates, predicted, color=colors[i % len(colors)],
                     linewidth=3, label=f'Segment {i+1} (slope: {seg["slope"]:+.2f}/yr)')
            plt.plot(seg_dates, seg_values, 'o', color=colors[i % len(colors)], markersize=3, alpha=0.5)

        # Mark break points (vertical lines)
        for bd in results['break_dates']:
            plt.axvline(x=bd, color='black', linestyle='--', alpha=0.7, linewidth=2)
            plt.text(bd, plt.ylim()[1] * 0.95, f'Break\n{bd.date()}',
                     ha='center', va='top', rotation=90, backgroundcolor='white', fontweight='bold')

        # Mark ICD transition
        plt.axvline(x=self.icd_transition, color='blue', linestyle='-', alpha=0.6,
                    label='ICD-10 Transition', linewidth=2)

        # Focus range boundaries
        plt.axvline(x=self.focus_start, color='gray', linestyle=':', alpha=0.3)
        plt.axvline(x=self.focus_end, color='gray', linestyle=':', alpha=0.3)

        plt.title(f'Break Analysis: {hypothesis_name}\nFocus: {self.focus_start.date()} to {self.focus_end.date()}')
        plt.xlabel('Date')
        plt.ylabel(value_col)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


# Global instance: defaults to forcing ICD-based segments
break_detector = BreakDetector(focus_start='2014-01-01', focus_end='2017-12-31', force_icd_segments=True)

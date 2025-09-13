"use client";

import { useCallback } from "react";


type TextBoxProps = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (v: string) => void;
  placeholder?: string;
};

export default function TextBox({
  value,
  onChange,
  onSubmit,
  placeholder = "ICD codes for cocaine addiction.",
}: TextBoxProps) {
    const handleSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();                 // prevent navigation/reload
      const v = value.trim();
      if (v.length > 0) onSubmit(v);
    },
    [onSubmit, value]
  );

    return (
        <form onSubmit={handleSubmit} className="block w-full">
            <label>
                <input
                    id="userInput"    
                    name="userInput"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    className="
                        block w-full rounded-md border border-gray-300 
                        bg-white px-[30px] py-2 text-sm 
                        text-black                   /* <-- actual input text in black */
                        placeholder:font-inherit
                        placeholder:text-black        /* <-- placeholder in black (light mode) */
                        focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50
                        dark:bg-gray-900 dark:border-gray-700 
                        dark:text-white               /* <-- actual input text in white (dark mode) */
                        dark:placeholder:text-gray-500
                    "
                    />
            </label>
            <button type="submit" className="sr-only">Submit</button>
        </form>
    )
}
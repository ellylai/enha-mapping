"use client";

import { useState } from 'react';

export default function TextBox() {
    const [userInput, setUserInput ] = useState('')

    return (
        <label>
            <input
                id="myInput"
                name="myInput"
                value={userInput}
                onChange={e => setUserInput(e.target.value)}
                placeholder="Type your prompt here!"
                className="
                    block w-full rounded-md border border-gray-300 
                    bg-white px-3 py-2 text-sm 
                    placeholder:text-gray-400
                    focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50
                    dark:bg-gray-900 dark:border-gray-700 dark:text-white
                    dark:placeholder:text-gray-500
                    "
            />
        </label>
    )
}
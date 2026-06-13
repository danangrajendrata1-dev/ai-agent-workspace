"use client";

import { useEffect, useState } from "react";

export default function CommandInput({
  notice = "",
  modelOptions = [],
  selectedModel = "model",
  onModelChange,
  onSubmit,
  placeholder = "ask me",
  resetSignal = 0
}) {
  const [value, setValue] = useState("");

  useEffect(() => {
    setValue("");
  }, [resetSignal]);

  function handleAction() {
    onSubmit?.(value);
  }

  return (
    <div className="w-full">
      <div className="rounded-[18px] border border-[rgba(62,54,46,0.16)] bg-[#E5E0D3] p-3 shadow-[0_12px_30px_rgba(62,54,46,0.08)]">
        <div className="flex min-h-[72px] flex-col gap-3 rounded-[14px] sm:flex-row sm:items-center">
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleAction();
              }
            }}
            placeholder={placeholder}
            className="min-w-0 flex-1 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-4 text-left text-[18px] font-medium tracking-[-0.02em] text-[#3E362E] outline-none placeholder:text-[rgba(62,54,46,0.42)]"
          />

          <div className="flex items-center gap-3">
            <select
              value={selectedModel}
              onChange={(event) => onModelChange?.(event.target.value)}
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[14px] text-[#3E362E] outline-none"
            >
              {modelOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={handleAction}
              className="rounded-lg bg-[#A36A58] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#94604f]"
              aria-label="Send"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {notice ? (
        <p className="mt-3 px-2 text-left text-xs text-[rgba(62,54,46,0.64)]">{notice}</p>
      ) : null}
    </div>
  );
}

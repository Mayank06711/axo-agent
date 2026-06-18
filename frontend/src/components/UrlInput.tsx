import { useState } from "react";

interface UrlInputProps {
  onSubmit: (url: string) => void;
  disabled: boolean;
}

export function UrlInput({ onSubmit, disabled }: UrlInputProps) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    // Prepend https:// if missing
    const fullUrl = trimmed.startsWith("http") ? trimmed : `https://${trimmed}`;
    onSubmit(fullUrl);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div
        className={`flex items-center rounded-xl border bg-gray-900 transition-all duration-200 ${
          disabled
            ? "border-gray-800 opacity-60"
            : "border-gray-800 focus-within:border-blue-500/50 focus-within:shadow-[0_0_15px_rgba(59,130,246,0.15)]"
        }`}
      >
        <div className="flex items-center pl-4 text-gray-500">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          disabled={disabled}
          className="flex-1 bg-transparent px-3 py-3 text-sm text-gray-50 placeholder:text-gray-600 outline-none font-mono"
        />
        <button
          type="submit"
          disabled={disabled || !url.trim()}
          className="m-1.5 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {disabled ? "Analyzing..." : "Analyze"}
        </button>
      </div>
    </form>
  );
}

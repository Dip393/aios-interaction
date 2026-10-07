"use client";

import React, {
  FormEvent,
  useEffect,
  useState,
} from "react";

export interface MemorySearchResult {
  id: string;
  content: string;
  type?: string;
  category?: string;
  relevance?: number;
  timestamp?: string;
}

export interface MemorySearchProps {
  apiUrl?: string;
  initialQuery?: string;
  placeholder?: string;
  onSearch?: (
    query: string
  ) =>
    | void
    | Promise<void>
    | Promise<MemorySearchResult[]>;
  onResults?: (
    results: MemorySearchResult[]
  ) => void;
  autoFocus?: boolean;
  className?: string;
}

export default function MemorySearch({
  apiUrl = "/api/memory/semantic/search",
  initialQuery = "",
  placeholder = "Search your memory...",
  onSearch,
  onResults,
  autoFocus = false,
  className = "",
}: MemorySearchProps) {
  const [query, setQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<
    MemorySearchResult[]
  >([]);
  const [error, setError] = useState<string | null>(
    null
  );

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  const executeSearch = async (
    event?: FormEvent
  ) => {
    event?.preventDefault();

    const trimmed = query.trim();

    if (!trimmed || loading) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (onSearch) {
        const response = await onSearch(trimmed);

        if (Array.isArray(response)) {
          setResults(response);
          onResults?.(response);
        }

        return;
      }

      const url = new URL(
        apiUrl,
        window.location.origin
      );

      url.searchParams.set("query", trimmed);

      const response = await fetch(
        url.toString(),
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          `Memory search failed with status ${response.status}`
        );
      }

      const data = await response.json();

      const rawResults =
        Array.isArray(data)
          ? data
          : Array.isArray(data.results)
          ? data.results
          : Array.isArray(data.items)
          ? data.items
          : [];

      const normalized =
        rawResults.map(
          (item: Record<string, unknown>) => ({
            id:
              typeof item.id === "string"
                ? item.id
                : crypto.randomUUID(),
            content:
              typeof item.content === "string"
                ? item.content
                : typeof item.text === "string"
                ? item.text
                : JSON.stringify(item),
            type:
              typeof item.type === "string"
                ? item.type
                : undefined,
            category:
              typeof item.category === "string"
                ? item.category
                : undefined,
            relevance:
              typeof item.relevance === "number"
                ? item.relevance
                : typeof item.score === "number"
                ? item.score
                : undefined,
            timestamp:
              typeof item.timestamp === "string"
                ? item.timestamp
                : undefined,
          })
        );

      setResults(normalized);
      onResults?.(normalized);
    } catch (searchError) {
      const message =
        searchError instanceof Error
          ? searchError.message
          : "Memory search failed.";

      setError(message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${className}`}>
      <form
        onSubmit={executeSearch}
        className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white p-2 focus-within:border-blue-500 dark:border-gray-700 dark:bg-gray-900"
      >
        <span className="px-2 text-gray-400">
          ⌕
        </span>

        <input
          value={query}
          onChange={(event) =>
            setQuery(event.target.value)
          }
          autoFocus={autoFocus}
          placeholder={placeholder}
          className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-white"
        />

        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setResults([]);
              setError(null);
            }}
            className="px-2 text-xs text-gray-400 hover:text-gray-600"
          >
            Clear
          </button>
        )}

        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && (
        <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-3 space-y-2">
          <div className="px-1 text-[10px] text-gray-400">
            {results.length} result
            {results.length === 1 ? "" : "s"}
          </div>

          {results.map((result) => (
            <div
              key={result.id}
              className="rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-950"
            >
              <p className="text-xs leading-relaxed text-gray-700 dark:text-gray-300">
                {result.content}
              </p>

              <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-gray-400">
                {result.type && (
                  <span>{result.type}</span>
                )}

                {result.category && (
                  <span>· {result.category}</span>
                )}

                {typeof result.relevance ===
                  "number" && (
                  <span className="ml-auto">
                    {Math.round(
                      result.relevance * 100
                    )}
                    % match
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
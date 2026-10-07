"use client";

import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import MemoryCard from "./MemoryCard";
import type { MemoryItem } from "@/lib/memory";

import MemorySearch, {
  MemorySearchResult,
} from "./MemorySearch";

export interface MemoryStats {
  shortTerm?: number;
  working?: number;
  longTerm?: number;
  semantic?: number;
  total?: number;
}

export interface MemoryPanelProps {
  memories?: MemoryItem[];
  stats?: MemoryStats;
  selectedMemoryId?: string;

  apiUrl?: string;

  onMemorySelect?: (
    memory: MemoryItem
  ) => void;

  onForget?: (
    memory: MemoryItem
  ) => void | Promise<void>;

  onSearch?: (
    query: string
  ) =>
    | void
    | Promise<void>
    | Promise<MemorySearchResult[]>;

  onRefresh?: () => void | Promise<void>;

  className?: string;
}

type MemoryFilter =
  | "all"
  | "short-term"
  | "working"
  | "long-term"
  | "semantic";

const filters: {
  value: MemoryFilter;
  label: string;
}[] = [
  {
    value: "all",
    label: "All",
  },
  {
    value: "short-term",
    label: "Recent",
  },
  {
    value: "working",
    label: "Working",
  },
  {
    value: "long-term",
    label: "Long-term",
  },
  {
    value: "semantic",
    label: "Semantic",
  },
];

export default function MemoryPanel({
  memories = [],
  stats,
  selectedMemoryId,
  apiUrl = "/api/memory/semantic/search",
  onMemorySelect,
  onForget,
  onSearch,
  onRefresh,
  className = "",
}: MemoryPanelProps) {
  const [filter, setFilter] =
    useState<MemoryFilter>("all");

  const [search, setSearch] =
    useState("");

  const [refreshing, setRefreshing] =
    useState(false);

  const [
    displayedMemories,
    setDisplayedMemories,
  ] = useState<MemoryItem[]>(memories);

  /*
   * Keep local memory state synchronized
   * with the parent component.
   */
  useEffect(() => {
    setDisplayedMemories(memories);
  }, [memories]);

  /*
   * Filter memories by type and search query.
   */
  const filteredMemories = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    return displayedMemories.filter(
      (memory) => {
        const memoryType =
          memory.type?.toLowerCase();

        const typeMatch =
          filter === "all" ||
          memoryType === filter ||
          (filter === "short-term" &&
            memoryType === "recent");

        if (!typeMatch) {
          return false;
        }

        if (!query) {
          return true;
        }

        const content =
          typeof memory.content === "string"
            ? memory.content
            : "";

        const category =
          typeof memory.category === "string"
            ? memory.category
            : "";

        return (
          content
            .toLowerCase()
            .includes(query) ||
          category
            .toLowerCase()
            .includes(query)
        );
      }
    );
  }, [
    displayedMemories,
    filter,
    search,
  ]);

  /*
   * Calculate counts for filter buttons.
   */
  const counts = useMemo(() => {
    const result: Record<
      MemoryFilter,
      number
    > = {
      all: displayedMemories.length,
      "short-term": 0,
      working: 0,
      "long-term": 0,
      semantic: 0,
    };

    for (const memory of displayedMemories) {
      const type =
        memory.type?.toLowerCase();

      if (type === "recent") {
        result["short-term"]++;
      } else if (
        type === "working"
      ) {
        result.working++;
      } else if (
        type === "long-term"
      ) {
        result["long-term"]++;
      } else if (
        type === "semantic"
      ) {
        result.semantic++;
      }
    }

    return result;
  }, [displayedMemories]);

  /*
   * Refresh memories from the parent.
   */
  const handleRefresh = async () => {
    if (
      !onRefresh ||
      refreshing
    ) {
      return;
    }

    setRefreshing(true);

    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  /*
   * Convert search results into the
   * canonical MemoryItem structure.
   */
  const handleSearchResults = (
    results: MemorySearchResult[]
  ) => {
    const mapped: MemoryItem[] =
      results.map((result) => ({
        id: result.id,
        content: result.content,
        type:
          result.type ??
          "semantic",
        category:
          result.category,
        relevance:
          result.relevance,
        timestamp:
          result.timestamp,
      }));

    setDisplayedMemories(mapped);
  };

  /*
   * Prefer server-provided statistics,
   * otherwise calculate them locally.
   */
  const resolvedStats: MemoryStats = {
    shortTerm:
      stats?.shortTerm ??
      counts["short-term"],

    working:
      stats?.working ??
      counts.working,

    longTerm:
      stats?.longTerm ??
      counts["long-term"],

    semantic:
      stats?.semantic ??
      counts.semantic,

    total:
      stats?.total ??
      displayedMemories.length,
  };

  return (
    <section
      className={`flex h-full min-h-0 flex-col rounded-2xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950 ${className}`}
    >
      {/* Header */}
      <header className="shrink-0 border-b border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-950">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Memory
            </h2>

            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              AIOS memory and contextual
              knowledge
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              {resolvedStats.total ?? 0}{" "}
              memories
            </span>

            {onRefresh && (
              <button
                type="button"
                onClick={() =>
                  void handleRefresh()
                }
                disabled={refreshing}
                className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300"
              >
                {refreshing
                  ? "Refreshing..."
                  : "Refresh"}
              </button>
            )}
          </div>
        </div>

        {/* Memory statistics */}
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <MemoryStat
            label="Recent"
            value={
              resolvedStats.shortTerm ??
              0
            }
          />

          <MemoryStat
            label="Working"
            value={
              resolvedStats.working ??
              0
            }
          />

          <MemoryStat
            label="Long-term"
            value={
              resolvedStats.longTerm ??
              0
            }
          />

          <MemoryStat
            label="Semantic"
            value={
              resolvedStats.semantic ??
              0
            }
          />
        </div>

        {/* Search */}
        <div className="mt-4">
          <MemorySearch
            apiUrl={apiUrl}
            onSearch={onSearch}
            onResults={
              handleSearchResults
            }
          />
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {filters.map((item) => {
            const active =
              filter === item.value;

            const count =
              counts[item.value] ?? 0;

            return (
              <button
                key={item.value}
                type="button"
                onClick={() =>
                  setFilter(item.value)
                }
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  active
                    ? "bg-blue-600 text-white"
                    : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-900"
                }`}
              >
                {item.label}

                <span
                  className={`ml-1 ${
                    active
                      ? "text-blue-100"
                      : "text-gray-400"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Memory list */}
      <div className="min-h-0 flex-1 overflow-auto p-5">
        {filteredMemories.length ===
        0 ? (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-5 py-14 text-center dark:border-gray-700 dark:bg-gray-950">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              ◇
            </div>

            <h3 className="mt-3 text-sm font-semibold text-gray-800 dark:text-gray-200">
              No memories found
            </h3>

            <p className="mt-1 text-xs text-gray-400">
              Try another memory type or
              search query.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {filteredMemories.map(
              (memory) => (
                <div
                  key={memory.id}
                  className={
                    selectedMemoryId ===
                    memory.id
                      ? "rounded-2xl ring-2 ring-blue-500/40"
                      : ""
                  }
                >
                  <MemoryCard
                    memory={memory}
                    onClick={
                      onMemorySelect
                    }
                    onForget={onForget}
                  />
                </div>
              )
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function MemoryStat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 dark:border-gray-800 dark:bg-gray-900">
      <div className="text-[10px] text-gray-400">
        {label}
      </div>

      <div className="mt-0.5 text-lg font-semibold text-gray-900 dark:text-white">
        {value}
      </div>
    </div>
  );
}
"use client";

import React from "react";
import type { MemoryItem } from "@/lib/memory";

export type MemoryType =
  | "short-term"
  | "working"
  | "long-term"
  | "semantic"
  | "recent"
  | "task"
  | string;

export interface MemoryCardProps {
  memory: MemoryItem;
  onClick?: (memory: MemoryItem) => void;
  onForget?: (memory: MemoryItem) => void;
  compact?: boolean;
  showActions?: boolean;
  className?: string;
}

const typeConfig: Record<
  string,
  {
    label: string;
    className: string;
    icon: string;
  }
> = {
  "short-term": {
    label: "Short-term",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
    icon: "◷",
  },

  recent: {
    label: "Recent",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
    icon: "◷",
  },

  working: {
    label: "Working",
    className:
      "bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400",
    icon: "◆",
  },

  "long-term": {
    label: "Long-term",
    className:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
    icon: "▣",
  },

  semantic: {
    label: "Semantic",
    className:
      "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-400",
    icon: "⌁",
  },

  task: {
    label: "Task",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
    icon: "✓",
  },
};

const formatTime = (value?: string) => {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function MemoryCard({
  memory,
  onClick,
  onForget,
  compact = false,
  showActions = true,
  className = "",
}: MemoryCardProps) {
  const type =
    memory.type?.toLowerCase() ?? "long-term";

  const config =
    typeConfig[type] ?? {
      label: type || "Memory",
      className:
        "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
      icon: "●",
    };

  const relevance =
    typeof memory.relevance === "number"
      ? Math.max(
          0,
          Math.min(1, memory.relevance)
        )
      : undefined;

  const importance =
    typeof memory.importance === "number"
      ? Math.max(
          0,
          Math.min(1, memory.importance)
        )
      : undefined;

  const timestamp =
    memory.timestamp ??
    memory.updatedAt ??
    memory.createdAt;

  return (
    <article
      onClick={() => onClick?.(memory)}
      className={`rounded-2xl border border-gray-200 bg-white transition dark:border-gray-800 dark:bg-gray-950 ${
        onClick
          ? "cursor-pointer hover:border-blue-300 hover:shadow-sm dark:hover:border-blue-800"
          : ""
      } ${className}`}
    >
      <div className={compact ? "p-4" : "p-5"}>
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gray-50 text-sm text-gray-500 dark:bg-gray-900 dark:text-gray-400">
            {config.icon}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${config.className}`}
              >
                {config.label}
              </span>

              {memory.category && (
                <span className="text-[10px] text-gray-400">
                  {memory.category}
                </span>
              )}

              {timestamp && (
                <time className="ml-auto text-[10px] text-gray-400">
                  {formatTime(timestamp)}
                </time>
              )}
            </div>

            <p
              className={`mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 dark:text-gray-300 ${
                compact ? "line-clamp-3" : ""
              }`}
            >
              {memory.content}
            </p>

            {(relevance !== undefined ||
              importance !== undefined) && (
              <div className="mt-3 flex flex-wrap gap-3">
                {relevance !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-400">
                      Relevance
                    </span>

                    <span className="text-[10px] font-medium text-gray-600 dark:text-gray-300">
                      {Math.round(
                        relevance * 100
                      )}
                      %
                    </span>
                  </div>
                )}

                {importance !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-400">
                      Importance
                    </span>

                    <span className="text-[10px] font-medium text-gray-600 dark:text-gray-300">
                      {Math.round(
                        importance * 100
                      )}
                      %
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {showActions && (
          <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3 dark:border-gray-800">
            <div className="text-[10px] text-gray-400">
              {memory.id}
            </div>

            {onForget && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onForget(memory);
                }}
                className="rounded-lg px-2.5 py-1.5 text-[10px] font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20"
              >
                Forget
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
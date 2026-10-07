"use client";

import React from "react";

export type ActivityType =
  | "user"
  | "thinking"
  | "assistant"
  | "approval"
  | "success"
  | "warning"
  | "error"
  | "info";

export interface ActivityItem {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp?: string;
}

export interface ActivityStreamProps {
  activities?: ActivityItem[];
  title?: string;
  emptyMessage?: string;
  maxItems?: number;
  className?: string;
}

const typeConfig: Record<
  ActivityType,
  {
    icon: string;
    className: string;
  }
> = {
  user: {
    icon: "→",
    className: "bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400",
  },
  thinking: {
    icon: "⋯",
    className:
      "bg-purple-50 text-purple-600 dark:bg-purple-950/30 dark:text-purple-400",
  },
  assistant: {
    icon: "AI",
    className:
      "bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400",
  },
  approval: {
    icon: "!",
    className:
      "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400",
  },
  success: {
    icon: "✓",
    className:
      "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400",
  },
  warning: {
    icon: "!",
    className:
      "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400",
  },
  error: {
    icon: "×",
    className:
      "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400",
  },
  info: {
    icon: "i",
    className:
      "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  },
};

export default function ActivityStream({
  activities = [],
  title = "Activity",
  emptyMessage = "No activity yet.",
  maxItems = 50,
  className = "",
}: ActivityStreamProps) {
  const visibleActivities = activities.slice(-maxItems);

  return (
    <div
      className={`flex h-full min-h-0 flex-col bg-gray-50/50 dark:bg-gray-950 ${className}`}
    >
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>

          <p className="text-[10px] text-gray-400">
            AIOS execution timeline
          </p>
        </div>

        <span className="rounded-full bg-gray-200 px-2 py-0.5 text-[10px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">
          {visibleActivities.length}
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {visibleActivities.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center">
            <p className="text-xs text-gray-400">
              {emptyMessage}
            </p>
          </div>
        ) : (
          <div className="relative space-y-4">
            <div className="absolute bottom-2 left-[11px] top-2 w-px bg-gray-200 dark:bg-gray-800" />

            {visibleActivities.map((activity) => {
              const config =
                typeConfig[activity.type];

              return (
                <div
                  key={activity.id}
                  className="relative flex gap-3"
                >
                  <div
                    className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[9px] font-semibold ${config.className}`}
                  >
                    {config.icon}
                  </div>

                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-medium text-gray-800 dark:text-gray-200">
                        {activity.title}
                      </p>

                      {activity.timestamp && (
                        <time className="shrink-0 text-[9px] text-gray-400">
                          {new Date(
                            activity.timestamp
                          ).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </time>
                      )}
                    </div>

                    {activity.description && (
                      <p className="mt-0.5 break-words text-[10px] leading-relaxed text-gray-500 dark:text-gray-400">
                        {activity.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
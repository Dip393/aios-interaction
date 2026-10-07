"use client";

import React from "react";
import TaskStatus, {
  TaskStatusValue,
} from "./TaskStatus";

export interface TaskTimelineEvent {
  id: string;
  title: string;
  description?: string;
  status?: TaskStatusValue | string;
  timestamp?: string;
  type?: string;
}

export interface TaskTimelineProps {
  events?: TaskTimelineEvent[];
  emptyMessage?: string;
  className?: string;
}

const formatTime = (timestamp?: string) => {
  if (!timestamp) {
    return "";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getDotClass = (status?: string) => {
  switch (status?.toLowerCase()) {
    case "completed":
      return "bg-emerald-500";

    case "failed":
      return "bg-red-500";

    case "running":
      return "bg-amber-500";

    case "cancelled":
      return "bg-gray-500";

    case "paused":
      return "bg-orange-500";

    default:
      return "bg-blue-500";
  }
};

export default function TaskTimeline({
  events = [],
  emptyMessage = "No task activity yet.",
  className = "",
}: TaskTimelineProps) {
  const sortedEvents = [...events].sort((a, b) => {
    const first = a.timestamp
      ? new Date(a.timestamp).getTime()
      : 0;

    const second = b.timestamp
      ? new Date(b.timestamp).getTime()
      : 0;

    return first - second;
  });

  return (
    <div
      className={`rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 ${className}`}
    >
      <div className="border-b border-gray-200 px-5 py-4 dark:border-gray-800">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          Task Timeline
        </h3>

        <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
          Task execution history
        </p>
      </div>

      <div className="p-5">
        {sortedEvents.length === 0 ? (
          <div className="py-8 text-center text-xs text-gray-400">
            {emptyMessage}
          </div>
        ) : (
          <div className="relative space-y-6">
            <div className="absolute bottom-4 left-[7px] top-4 w-px bg-gray-200 dark:bg-gray-800" />

            {sortedEvents.map((event) => (
              <div
                key={event.id}
                className="relative flex gap-4"
              >
                <div
                  className={`relative z-10 mt-1 h-4 w-4 shrink-0 rounded-full border-2 border-white dark:border-gray-950 ${getDotClass(
                    event.status
                  )}`}
                />

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        {event.title}
                      </h4>

                      {event.type && (
                        <span className="mt-0.5 block text-[10px] text-gray-400">
                          {event.type}
                        </span>
                      )}
                    </div>

                    {event.timestamp && (
                      <time className="text-[10px] text-gray-400">
                        {formatTime(event.timestamp)}
                      </time>
                    )}
                  </div>

                  {event.description && (
                    <p className="mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                      {event.description}
                    </p>
                  )}

                  {event.status && (
                    <div className="mt-2">
                      <TaskStatus
                        status={event.status}
                        size="sm"
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
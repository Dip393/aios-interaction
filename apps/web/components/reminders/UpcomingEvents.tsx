"use client";

import React, { useMemo } from "react";

import type { Reminder } from "@/lib/reminder";

export interface UpcomingEvent {
  id: string;
  title: string;
  description?: string;
  date: string;
  type?:
    | "reminder"
    | "event"
    | "task"
    | "calendar"
    | string;
  status?: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface UpcomingEventsProps {
  events?: UpcomingEvent[];
  reminders?: Reminder[];
  limit?: number;

  onSelect?: (
    event: UpcomingEvent
  ) => void;

  emptyMessage?: string;
  className?: string;
}

const typeIcons: Record<
  string,
  string
> = {
  reminder: "⏰",
  event: "◆",
  task: "✓",
  calendar: "▣",
};

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return {
      day: "--",
      month: "",
      time: value,
    };
  }

  return {
    day: date.toLocaleDateString([], {
      day: "2-digit",
    }),

    month: date.toLocaleDateString([], {
      month: "short",
    }),

    time: date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

function relativeTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const diff =
    date.getTime() - Date.now();

  const minutes = Math.round(
    diff / 60000
  );

  if (minutes < 0) {
    return "Past";
  }

  if (minutes < 1) {
    return "Now";
  }

  if (minutes < 60) {
    return `In ${minutes}m`;
  }

  const hours = Math.round(
    minutes / 60
  );

  if (hours < 24) {
    return `In ${hours}h`;
  }

  const days = Math.round(
    hours / 24
  );

  return `In ${days}d`;
}

export default function UpcomingEvents({
  events = [],
  reminders = [],
  limit = 5,
  onSelect,
  emptyMessage = "No upcoming events.",
  className = "",
}: UpcomingEventsProps) {
  const normalizedEvents = useMemo(() => {
    const reminderEvents: UpcomingEvent[] =
      reminders.map((reminder) => ({
        id: reminder.id,
        title: reminder.title,
        description:
          reminder.description,

        date:
          reminder.reminderAt ??
          reminder.scheduledAt ??
          reminder.dueAt ??
          reminder.createdAt ??
          new Date().toISOString(),

        type: "reminder",
        status: reminder.status,
        category: reminder.category,
        metadata: reminder.metadata,
      }));

    return [
      ...events,
      ...reminderEvents,
    ]
      .filter((event) => {
        const date = new Date(
          event.date
        );

        if (
          Number.isNaN(
            date.getTime()
          )
        ) {
          return false;
        }

        return (
          date.getTime() >=
          Date.now()
        );
      })
      .sort(
        (a, b) =>
          new Date(
            a.date
          ).getTime() -
          new Date(
            b.date
          ).getTime()
      )
      .slice(0, limit);
  }, [
    events,
    reminders,
    limit,
  ]);

  return (
    <section
      className={`rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 ${className}`}
    >
      <div className="border-b border-gray-100 px-5 py-4 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
              Upcoming
            </h2>

            <p className="mt-0.5 text-[11px] text-gray-400">
              Your next scheduled
              activities
            </p>
          </div>

          <span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-medium text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
            {normalizedEvents.length}
          </span>
        </div>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {normalizedEvents.length ===
        0 ? (
          <div className="px-5 py-10 text-center">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-gray-50 text-gray-400 dark:bg-gray-900">
              ◷
            </div>

            <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
              {emptyMessage}
            </p>
          </div>
        ) : (
          normalizedEvents.map(
            (event) => {
              const date =
                formatDate(
                  event.date
                );

              const icon =
                typeIcons[
                  event.type?.toLowerCase() ??
                    "reminder"
                ] ?? "●";

              return (
                <button
                  key={event.id}
                  type="button"
                  onClick={() =>
                    onSelect?.(event)
                  }
                  disabled={!onSelect}
                  className={`flex w-full items-center gap-3 px-5 py-3 text-left transition ${
                    onSelect
                      ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900"
                      : "cursor-default"
                  }`}
                >
                  <div className="flex w-11 shrink-0 flex-col items-center rounded-xl bg-gray-50 px-2 py-1.5 dark:bg-gray-900">
                    <span className="text-[9px] font-medium uppercase text-gray-400">
                      {date.month}
                    </span>

                    <span className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                      {date.day}
                    </span>
                  </div>

                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-xs text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
                    {icon}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-semibold text-gray-800 dark:text-gray-200">
                      {event.title}
                    </div>

                    <div className="mt-0.5 flex items-center gap-2 text-[10px] text-gray-400">
                      <span>
                        {date.time}
                      </span>

                      <span>•</span>

                      <span>
                        {relativeTime(
                          event.date
                        )}
                      </span>
                    </div>

                    {event.description && (
                      <p className="mt-1 truncate text-[10px] text-gray-400">
                        {
                          event.description
                        }
                      </p>
                    )}
                  </div>

                  {event.category && (
                    <span className="hidden rounded-full bg-gray-100 px-2 py-1 text-[9px] text-gray-500 sm:block dark:bg-gray-900 dark:text-gray-400">
                      {event.category}
                    </span>
                  )}
                </button>
              );
            }
          )
        )}
      </div>
    </section>
  );
}
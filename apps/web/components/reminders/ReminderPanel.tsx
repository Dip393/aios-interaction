"use client";

import React, {
  useMemo,
  useState,
} from "react";

import ReminderCard from "./ReminderCard";

import type { Reminder } from "@/lib/reminder";

import UpcomingEvents, {
  UpcomingEvent,
} from "./UpcomingEvents";

export interface ReminderPanelProps {
  reminders?: Reminder[];

  selectedReminderId?: string;

  onReminderSelect?: (
    reminder: Reminder
  ) => void;

  onComplete?: (
    reminder: Reminder
  ) => void | Promise<void>;

  onCancel?: (
    reminder: Reminder
  ) => void | Promise<void>;

  onDelete?: (
    reminder: Reminder
  ) => void | Promise<void>;

  onRefresh?: () => void | Promise<void>;

  showUpcoming?: boolean;

  upcomingEvents?: UpcomingEvent[];

  className?: string;
}

type ReminderFilter =
  | "all"
  | "pending"
  | "scheduled"
  | "completed"
  | "cancelled";

const filters: {
  value: ReminderFilter;
  label: string;
}[] = [
  {
    value: "all",
    label: "All",
  },
  {
    value: "pending",
    label: "Pending",
  },
  {
    value: "scheduled",
    label: "Scheduled",
  },
  {
    value: "completed",
    label: "Completed",
  },
  {
    value: "cancelled",
    label: "Cancelled",
  },
];

function reminderTime(
  reminder: Reminder
) {
  return (
    reminder.reminderAt ??
    reminder.scheduledAt ??
    reminder.dueAt
  );
}

export default function ReminderPanel({
  reminders = [],
  selectedReminderId,
  onReminderSelect,
  onComplete,
  onCancel,
  onDelete,
  onRefresh,
  showUpcoming = true,
  upcomingEvents = [],
  className = "",
}: ReminderPanelProps) {
  const [filter, setFilter] =
    useState<ReminderFilter>("all");

  const [search, setSearch] =
    useState("");

  const [refreshing, setRefreshing] =
    useState(false);

  const filteredReminders =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      return reminders
        .filter((reminder) => {
          const status =
            reminder.status?.toLowerCase() ??
            "pending";

          if (
            filter !== "all" &&
            status !== filter
          ) {
            return false;
          }

          if (!query) {
            return true;
          }

          const title =
            reminder.title?.toLowerCase() ??
            "";

          const description =
            reminder.description?.toLowerCase() ??
            "";

          const category =
            reminder.category?.toLowerCase() ??
            "";

          return (
            title.includes(query) ||
            description.includes(query) ||
            category.includes(query)
          );
        })
        .sort((a, b) => {
          const aTime =
            reminderTime(a);

          const bTime =
            reminderTime(b);

          if (!aTime && !bTime) {
            return 0;
          }

          if (!aTime) {
            return 1;
          }

          if (!bTime) {
            return -1;
          }

          return (
            new Date(aTime).getTime() -
            new Date(bTime).getTime()
          );
        });
    }, [
      reminders,
      filter,
      search,
    ]);

  const counts = useMemo(() => {
    const result: Record<
      ReminderFilter,
      number
    > = {
      all: reminders.length,
      pending: 0,
      scheduled: 0,
      completed: 0,
      cancelled: 0,
    };

    for (const reminder of reminders) {
      const status =
        reminder.status?.toLowerCase();

      if (
        status &&
        result[
          status as ReminderFilter
        ] !== undefined
      ) {
        result[
          status as ReminderFilter
        ]++;
      }
    }

    return result;
  }, [reminders]);

  const upcomingReminders =
    useMemo(
      () =>
        reminders.filter(
          (reminder) => {
            const status =
              reminder.status?.toLowerCase();

            if (
              status === "completed" ||
              status === "cancelled" ||
              status === "expired"
            ) {
              return false;
            }

            const date =
              reminderTime(reminder);

            if (!date) {
              return false;
            }

            const timestamp =
              new Date(date).getTime();

            return (
              !Number.isNaN(timestamp) &&
              timestamp >= Date.now()
            );
          }
        ),
      [reminders]
    );

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

  return (
    <section
      className={`flex h-full min-h-0 flex-col rounded-2xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950 ${className}`}
    >
      <header className="shrink-0 border-b border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-950">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Reminders
            </h2>

            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Manage scheduled reminders
              and upcoming activities
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
              {reminders.length} total
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

        <div className="mt-4">
          <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 focus-within:border-blue-500 dark:border-gray-700 dark:bg-gray-900">
            <span className="text-gray-400">
              ⌕
            </span>

            <input
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
              placeholder="Search reminders..."
              className="min-w-0 flex-1 bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-white"
            />

            {search && (
              <button
                type="button"
                onClick={() =>
                  setSearch("")
                }
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {filters.map((item) => {
            const active =
              filter === item.value;

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
                  {counts[item.value]}
                </span>
              </button>
            );
          })}
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-auto p-5">
        {showUpcoming && (
          <div className="mb-5">
            <UpcomingEvents
              events={upcomingEvents}
              reminders={
                upcomingReminders
              }
              limit={5}
              onSelect={(event) => {
                const reminder =
                  reminders.find(
                    (item) =>
                      item.id === event.id
                  );

                if (reminder) {
                  onReminderSelect?.(
                    reminder
                  );
                }
              }}
            />
          </div>
        )}

        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Reminder List
          </h3>

          <span className="text-[10px] text-gray-400">
            {filteredReminders.length}{" "}
            shown
          </span>
        </div>

        {filteredReminders.length ===
        0 ? (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-5 py-14 text-center dark:border-gray-700 dark:bg-gray-950">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              ⏰
            </div>

            <h3 className="mt-3 text-sm font-semibold text-gray-800 dark:text-gray-200">
              No reminders found
            </h3>

            <p className="mt-1 text-xs text-gray-400">
              Try another filter or
              search query.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {filteredReminders.map(
              (reminder) => (
                <div
                  key={reminder.id}
                  className={
                    selectedReminderId ===
                    reminder.id
                      ? "rounded-2xl ring-2 ring-blue-500/40"
                      : ""
                  }
                >
                  <ReminderCard
                    reminder={reminder}
                    onClick={
                      onReminderSelect
                    }
                    onComplete={
                      onComplete
                    }
                    onCancel={
                      onCancel
                    }
                    onDelete={
                      onDelete
                    }
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
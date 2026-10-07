"use client";

import React from "react";
import type { Reminder } from "@/lib/reminder";

export type ReminderStatus =
  | "pending"
  | "scheduled"
  | "active"
  | "completed"
  | "cancelled"
  | "expired"
  | "failed"
  | string;

export interface ReminderCardProps {
  reminder: Reminder;
  onClick?: (reminder: Reminder) => void;
  onCancel?: (reminder: Reminder) => void;
  onComplete?: (reminder: Reminder) => void;
  onDelete?: (reminder: Reminder) => void;
  compact?: boolean;
  showActions?: boolean;
  className?: string;
}

const statusConfig: Record<
  string,
  {
    label: string;
    className: string;
    dotClassName: string;
  }
> = {
  pending: {
    label: "Pending",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
    dotClassName: "bg-amber-500",
  },

  scheduled: {
    label: "Scheduled",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
    dotClassName: "bg-blue-500",
  },

  active: {
    label: "Active",
    className:
      "bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400",
    dotClassName: "bg-purple-500",
  },

  completed: {
    label: "Completed",
    className:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
    dotClassName: "bg-emerald-500",
  },

  cancelled: {
    label: "Cancelled",
    className:
      "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    dotClassName: "bg-gray-400",
  },

  expired: {
    label: "Expired",
    className:
      "bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400",
    dotClassName: "bg-orange-500",
  },

  failed: {
    label: "Failed",
    className:
      "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
    dotClassName: "bg-red-500",
  },
};

const priorityConfig: Record<
  string,
  string
> = {
  low: "text-gray-400",
  medium: "text-blue-500",
  high: "text-orange-500",
  critical: "text-red-500",
};

function formatDateTime(value?: string) {
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
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isUpcoming(value?: string) {
  if (!value) {
    return false;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return false;
  }

  return date.getTime() > Date.now();
}

export default function ReminderCard({
  reminder,
  onClick,
  onCancel,
  onComplete,
  onDelete,
  compact = false,
  showActions = true,
  className = "",
}: ReminderCardProps) {
  const status =
    reminder.status?.toLowerCase() ?? "pending";

  const config =
    statusConfig[status] ?? {
      label: status || "Pending",
      className:
        "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
      dotClassName: "bg-gray-400",
    };

  const reminderTime =
    reminder.reminderAt ??
    reminder.scheduledAt ??
    reminder.dueAt;

  const canCancel =
    status !== "cancelled" &&
    status !== "completed" &&
    status !== "expired";

  const canComplete =
    status !== "completed" &&
    status !== "cancelled";

  return (
    <article
      onClick={() => onClick?.(reminder)}
      className={`rounded-2xl border border-gray-200 bg-white transition dark:border-gray-800 dark:bg-gray-950 ${
        onClick
          ? "cursor-pointer hover:border-blue-300 hover:shadow-sm dark:hover:border-blue-800"
          : ""
      } ${className}`}
    >
      <div className={compact ? "p-4" : "p-5"}>
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
            ⏰
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium ${config.className}`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${config.dotClassName}`}
                />

                {config.label}
              </span>

              {reminder.recurring && (
                <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-indigo-600 dark:bg-indigo-950/30 dark:text-indigo-400">
                  Recurring
                </span>
              )}

              {reminder.priority && (
                <span
                  className={`text-[10px] font-medium ${
                    priorityConfig[
                      reminder.priority.toLowerCase()
                    ] ?? "text-gray-400"
                  }`}
                >
                  {reminder.priority}
                </span>
              )}
            </div>

            <h3 className="mt-2 truncate text-sm font-semibold text-gray-900 dark:text-white">
              {reminder.title}
            </h3>

            {reminder.description && (
              <p
                className={`mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400 ${
                  compact ? "line-clamp-2" : ""
                }`}
              >
                {reminder.description}
              </p>
            )}

            {reminderTime && (
              <div
                className={`mt-3 flex items-center gap-2 text-xs ${
                  isUpcoming(reminderTime) &&
                  status !== "completed"
                    ? "text-blue-600 dark:text-blue-400"
                    : "text-gray-500 dark:text-gray-400"
                }`}
              >
                <span>◷</span>
                <span>
                  {formatDateTime(reminderTime)}
                </span>
              </div>
            )}

            {reminder.recurrence && (
              <div className="mt-1 text-[10px] text-gray-400">
                Repeats: {reminder.recurrence}
              </div>
            )}

            {reminder.category && (
              <div className="mt-2 text-[10px] text-gray-400">
                {reminder.category}
              </div>
            )}
          </div>
        </div>

        {showActions && (
          <div className="mt-4 flex items-center justify-end gap-2 border-t border-gray-100 pt-3 dark:border-gray-800">
            {onComplete && canComplete && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onComplete(reminder);
                }}
                className="rounded-lg px-2.5 py-1.5 text-[10px] font-medium text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/20"
              >
                Complete
              </button>
            )}

            {onCancel && canCancel && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onCancel(reminder);
                }}
                className="rounded-lg px-2.5 py-1.5 text-[10px] font-medium text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-950/20"
              >
                Cancel
              </button>
            )}

            {onDelete && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onDelete(reminder);
                }}
                className="rounded-lg px-2.5 py-1.5 text-[10px] font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
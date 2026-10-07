"use client";

import React from "react";
import TaskStatus, {
  TaskStatusValue,
} from "./TaskStatus";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatusValue | string;
  priority?: "low" | "medium" | "high" | "critical" | string;
  type?: string;
  environmentId?: string;
  progress?: number;
  createdAt?: string;
  updatedAt?: string;
  startedAt?: string;
  completedAt?: string;
  dueAt?: string;
  error?: string;
  metadata?: Record<string, unknown>;
}

export interface TaskCardProps {
  task: Task;
  onClick?: (task: Task) => void;
  onComplete?: (task: Task) => void;
  onCancel?: (task: Task) => void;
  onPause?: (task: Task) => void;
  onResume?: (task: Task) => void;
  compact?: boolean;
  className?: string;
}

const priorityConfig: Record<
  string,
  {
    label: string;
    className: string;
  }
> = {
  low: {
    label: "Low",
    className: "text-gray-500",
  },
  medium: {
    label: "Medium",
    className: "text-blue-600 dark:text-blue-400",
  },
  high: {
    label: "High",
    className: "text-orange-600 dark:text-orange-400",
  },
  critical: {
    label: "Critical",
    className: "text-red-600 dark:text-red-400",
  },
};

const formatDate = (value?: string) => {
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

export default function TaskCard({
  task,
  onClick,
  onComplete,
  onCancel,
  onPause,
  onResume,
  compact = false,
  className = "",
}: TaskCardProps) {
  const priority =
    priorityConfig[
      task.priority?.toLowerCase() ?? "medium"
    ] ?? priorityConfig.medium;

  const progress = Math.max(
    0,
    Math.min(100, task.progress ?? 0)
  );

  const isRunning =
    task.status.toLowerCase() === "running";

  const isPaused =
    task.status.toLowerCase() === "paused";

  const isCompleted =
    task.status.toLowerCase() === "completed";

  const isCancelled =
    task.status.toLowerCase() === "cancelled";

  return (
    <article
      onClick={() => onClick?.(task)}
      className={`group rounded-2xl border border-gray-200 bg-white transition dark:border-gray-800 dark:bg-gray-950 ${
        onClick
          ? "cursor-pointer hover:border-blue-300 hover:shadow-sm dark:hover:border-blue-800"
          : ""
      } ${className}`}
    >
      <div className={compact ? "p-4" : "p-5"}>
        <div className="flex items-start gap-3">
          <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-sm text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
            {task.type === "coding"
              ? "</>"
              : task.type === "email"
              ? "✉"
              : task.type === "calendar"
              ? "▣"
              : "✓"}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="truncate font-semibold text-gray-900 dark:text-white">
                  {task.title}
                </h3>

                {task.description && (
                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                    {task.description}
                  </p>
                )}
              </div>

              <TaskStatus
                status={task.status}
                size="sm"
              />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[10px]">
              {task.priority && (
                <span className={priority.className}>
                  Priority: {priority.label}
                </span>
              )}

              {task.type && (
                <span className="text-gray-400">
                  {task.type}
                </span>
              )}

              {task.dueAt && (
                <span className="text-gray-400">
                  Due {formatDate(task.dueAt)}
                </span>
              )}
            </div>
          </div>
        </div>

        {isRunning && (
          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between text-[10px] text-gray-400">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
              <div
                className="h-full rounded-full bg-blue-600 transition-all duration-300"
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>
          </div>
        )}

        {task.error && (
          <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600 dark:bg-red-950/20 dark:text-red-400">
            {task.error}
          </div>
        )}

        {!compact && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3 dark:border-gray-800">
            <div className="text-[10px] text-gray-400">
              {task.updatedAt
                ? `Updated ${formatDate(task.updatedAt)}`
                : task.createdAt
                ? `Created ${formatDate(task.createdAt)}`
                : ""}
            </div>

            <div
              className="flex gap-2"
              onClick={(event) =>
                event.stopPropagation()
              }
            >
              {isRunning && onPause && (
                <button
                  type="button"
                  onClick={() => onPause(task)}
                  className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-[10px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900"
                >
                  Pause
                </button>
              )}

              {isPaused && onResume && (
                <button
                  type="button"
                  onClick={() => onResume(task)}
                  className="rounded-lg border border-blue-200 px-2.5 py-1.5 text-[10px] font-medium text-blue-600 hover:bg-blue-50 dark:border-blue-900 dark:text-blue-400 dark:hover:bg-blue-950/30"
                >
                  Resume
                </button>
              )}

              {!isCompleted &&
                !isCancelled &&
                onComplete && (
                  <button
                    type="button"
                    onClick={() => onComplete(task)}
                    className="rounded-lg bg-blue-600 px-2.5 py-1.5 text-[10px] font-medium text-white hover:bg-blue-700"
                  >
                    Complete
                  </button>
                )}

              {!isCompleted &&
                !isCancelled &&
                onCancel && (
                  <button
                    type="button"
                    onClick={() => onCancel(task)}
                    className="rounded-lg border border-red-200 px-2.5 py-1.5 text-[10px] font-medium text-red-600 hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950/20"
                  >
                    Cancel
                  </button>
                )}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
"use client";

import React, { useMemo, useState } from "react";
import TaskCard, {
  Task,
} from "./TaskCard";
import TaskStatus, {
  TaskStatusValue,
} from "./TaskStatus";
import TaskTimeline, {
  TaskTimelineEvent,
} from "./TaskTimeline";

export interface TaskPanelProps {
  tasks?: Task[];
  selectedTaskId?: string;
  onTaskSelect?: (task: Task) => void;
  onComplete?: (task: Task) => void;
  onCancel?: (task: Task) => void;
  onPause?: (task: Task) => void;
  onResume?: (task: Task) => void;
  onRefresh?: () => void | Promise<void>;
  showTimeline?: boolean;
  timelineEvents?: TaskTimelineEvent[];
  className?: string;
}

type FilterValue =
  | "all"
  | TaskStatusValue;

const filters: {
  value: FilterValue;
  label: string;
}[] = [
  {
    value: "all",
    label: "All",
  },
  {
    value: "running",
    label: "Running",
  },
  {
    value: "pending",
    label: "Pending",
  },
  {
    value: "completed",
    label: "Completed",
  },
  {
    value: "failed",
    label: "Failed",
  },
];

export default function TaskPanel({
  tasks = [],
  selectedTaskId,
  onTaskSelect,
  onComplete,
  onCancel,
  onPause,
  onResume,
  onRefresh,
  showTimeline = true,
  timelineEvents = [],
  className = "",
}: TaskPanelProps) {
  const [filter, setFilter] =
    useState<FilterValue>("all");

  const [search, setSearch] = useState("");

  const [refreshing, setRefreshing] =
    useState(false);

  const filteredTasks = useMemo(() => {
    const query = search.trim().toLowerCase();

    return tasks.filter((task) => {
      const statusMatch =
        filter === "all" ||
        task.status.toLowerCase() === filter;

      if (!statusMatch) {
        return false;
      }

      if (!query) {
        return true;
      }

      return (
        task.title.toLowerCase().includes(query) ||
        task.description
          ?.toLowerCase()
          .includes(query) ||
        task.type?.toLowerCase().includes(query)
      );
    });
  }, [tasks, filter, search]);

  const counts = useMemo(() => {
    const result: Record<string, number> = {
      all: tasks.length,
    };

    for (const task of tasks) {
      const status = task.status.toLowerCase();

      result[status] = (result[status] ?? 0) + 1;
    }

    return result;
  }, [tasks]);

  const handleRefresh = async () => {
    if (!onRefresh || refreshing) {
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
              Tasks
            </h2>

            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              AIOS task execution and management
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              {tasks.length} total
            </span>

            {onRefresh && (
              <button
                type="button"
                onClick={() => void handleRefresh()}
                disabled={refreshing}
                className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                {refreshing ? "Refreshing..." : "Refresh"}
              </button>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-1.5">
            {filters.map((item) => {
              const active = filter === item.value;
              const count = counts[item.value] ?? 0;

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

          <div className="relative w-full lg:w-64">
            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search tasks..."
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-800 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
            />
          </div>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-auto p-5">
        <div
          className={
            showTimeline
              ? "grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]"
              : ""
          }
        >
          <div className="min-w-0 space-y-3">
            {filteredTasks.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-5 py-14 text-center dark:border-gray-700 dark:bg-gray-950">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                  ✓
                </div>

                <h3 className="mt-3 text-sm font-semibold text-gray-800 dark:text-gray-200">
                  No tasks found
                </h3>

                <p className="mt-1 text-xs text-gray-400">
                  {search
                    ? "Try a different search term."
                    : "There are no tasks in this view."}
                </p>
              </div>
            ) : (
              filteredTasks.map((task) => (
                <div
                  key={task.id}
                  className={
                    selectedTaskId === task.id
                      ? "rounded-2xl ring-2 ring-blue-500/40"
                      : ""
                  }
                >
                  <TaskCard
                    task={task}
                    onClick={onTaskSelect}
                    onComplete={onComplete}
                    onCancel={onCancel}
                    onPause={onPause}
                    onResume={onResume}
                  />
                </div>
              ))
            )}
          </div>

          {showTimeline && (
            <div className="min-w-0">
              <TaskTimeline
                events={timelineEvents}
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
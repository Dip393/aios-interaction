"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import TaskPanel from "@/components/tasks/TaskPanel";
import {
  taskApi,
  Task,
  TaskStatus,
} from "@/lib/task";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] =
    useState<string>();

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await taskApi.list();

      const data = Array.isArray(response)
        ? response
        : Array.isArray(
            (response as {
              tasks?: Task[];
            }).tasks
          )
        ? (
            response as {
              tasks: Task[];
            }
          ).tasks
        : [];

      setTasks(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load tasks."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  const updateTaskStatus = async (
    taskId: string,
    action:
      | "complete"
      | "cancel"
      | "pause"
      | "resume"
  ) => {
    try {
      setError(null);

      if (action === "complete") {
        await taskApi.complete(taskId);
      } else if (action === "cancel") {
        await taskApi.cancel(taskId);
      } else {
        await taskApi.update(taskId, {
          status:
            action === "pause"
              ? "paused"
              : "running",
        });
      }

      await loadTasks();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update task."
      );
    }
  };

  const timelineEvents = useMemo(() => {
    const selected = tasks.find(
      (task) =>
        task.id === selectedTaskId
    );

    if (!selected) {
      return [];
    }

    const events: Array<{
      id: string;
      title: string;
      description?: string;
      status: TaskStatus;
      timestamp: string;
      type: string;
    }> = [];

    if (selected.createdAt) {
      events.push({
        id: `${selected.id}-created`,
        title: "Task created",
        description: selected.title,
        status: "pending" as TaskStatus,
        timestamp: selected.createdAt,
        type: "created",
      });
    }

    if (selected.startedAt) {
      events.push({
        id: `${selected.id}-started`,
        title: "Task started",
        status: "running" as TaskStatus,
        timestamp: selected.startedAt,
        type: "started",
      });
    }

    if (selected.completedAt) {
      events.push({
        id: `${selected.id}-completed`,
        title: "Task completed",
        status: "completed" as TaskStatus,
        timestamp: selected.completedAt,
        type: "completed",
      });
    }

    if (selected.error) {
      events.push({
        id: `${selected.id}-error`,
        title: "Task failed",
        description: selected.error,
        status: "failed" as TaskStatus,
        timestamp:
          selected.updatedAt ||
          new Date().toISOString(),
        type: "error",
      });
    }

    return events;
  }, [tasks, selectedTaskId]);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-600">
              AIOS
            </p>

            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Tasks
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Monitor and manage AIOS tasks and
              their execution progress.
            </p>
          </div>

          <button
            type="button"
            onClick={() =>
              void loadTasks()
            }
            disabled={loading}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Refreshing..."
              : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <TaskPanel
            tasks={tasks}
            selectedTaskId={selectedTaskId}

            onTaskSelect={(task) =>
              setSelectedTaskId(task.id)
            }

            onComplete={(task) =>
              void updateTaskStatus(
                task.id,
                "complete"
              )
            }

            onCancel={(task) =>
              void updateTaskStatus(
                task.id,
                "cancel"
              )
            }

            onPause={(task) =>
              void updateTaskStatus(
                task.id,
                "pause"
              )
            }

            onResume={(task) =>
              void updateTaskStatus(
                task.id,
                "resume"
              )
            }

            onRefresh={() =>
              void loadTasks()
            }

            showTimeline={Boolean(
              selectedTaskId
            )}

            timelineEvents={timelineEvents}
          />
        </section>
      </div>
    </main>
  );
}
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReminderPanel from "@/components/reminders/ReminderPanel";
import {
  reminderApi,
  Reminder,
} from "@/lib/reminder";

export default function RemindersPage() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [selectedReminderId, setSelectedReminderId] =
    useState<string>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadReminders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await reminderApi.list();

      const data = Array.isArray(response)
        ? response
        : Array.isArray(
              (response as { reminders?: Reminder[] }).reminders
            )
          ? (response as { reminders: Reminder[] }).reminders
          : [];

      setReminders(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load reminders."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReminders();
  }, [loadReminders]);

  const handleComplete = async (reminder: Reminder) => {
    try {
      setError(null);

      const base = reminder.id;

      await fetch(
        `/api/reminders/${encodeURIComponent(base)}/complete`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      await loadReminders();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to complete reminder."
      );
    }
  };

  const handleCancel = async (reminder: Reminder) => {
    try {
      setError(null);
      await reminderApi.cancel(reminder.id);
      await loadReminders();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to cancel reminder."
      );
    }
  };

  const handleDelete = async (reminder: Reminder) => {
    try {
      setError(null);
      await reminderApi.delete(reminder.id);

      if (selectedReminderId === reminder.id) {
        setSelectedReminderId(undefined);
      }

      await loadReminders();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete reminder."
      );
    }
  };

  const upcomingEvents = useMemo(() => {
    return reminders
      .filter((reminder) => {
        const date =
          reminder.reminderAt ||
          reminder.scheduledAt ||
          reminder.dueAt;

        if (!date) {
          return false;
        }

        return new Date(date).getTime() >= Date.now();
      })
      .map((reminder) => ({
        id: reminder.id,
        title: reminder.title,
        description: reminder.description,
        date:
          reminder.reminderAt ||
          reminder.scheduledAt ||
          reminder.dueAt ||
          "",
        type: "reminder",
        status: reminder.status,
        category: reminder.category,
        metadata: reminder.metadata,
      }));
  }, [reminders]);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-600">AIOS</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Reminders
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Manage scheduled reminders and upcoming events.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadReminders()}
            disabled={loading}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <ReminderPanel
            reminders={reminders}
            selectedReminderId={selectedReminderId}
            onReminderSelect={(reminder) =>
              setSelectedReminderId(reminder.id)
            }
            onComplete={(reminder) => void handleComplete(reminder)}
            onCancel={(reminder) => void handleCancel(reminder)}
            onDelete={(reminder) => void handleDelete(reminder)}
            onRefresh={() => void loadReminders()}
            showUpcoming
            upcomingEvents={upcomingEvents}
          />
        </section>
      </div>
    </main>
  );
}
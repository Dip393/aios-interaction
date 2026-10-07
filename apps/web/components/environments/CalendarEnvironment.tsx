"use client";

import React, { useMemo, useState } from "react";
import EnvironmentShell from "./EnvironmentShell";

export interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  startTime?: string;
  endTime?: string;
  description?: string;
  location?: string;
}

export interface CalendarEnvironmentProps {
  environmentId?: string;
  events?: CalendarEvent[];
  onCreateEvent?: (event: Omit<CalendarEvent, "id">) => void | Promise<void>;
  onSelectEvent?: (event: CalendarEvent) => void;
  className?: string;
}

export default function CalendarEnvironment({
  environmentId,
  events = [],
  onCreateEvent,
  onSelectEvent,
  className = "",
}: CalendarEnvironmentProps) {
  const [selectedDate, setSelectedDate] =
    useState(() => {
      const now = new Date();

      return now.toISOString().slice(0, 10);
    });

  const [showCreate, setShowCreate] =
    useState(false);

  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("10:00");
  const [endTime, setEndTime] = useState("11:00");
  const [location, setLocation] = useState("");
  const [description, setDescription] =
    useState("");

  const selectedEvents = useMemo(
    () =>
      events
        .filter((event) => event.date === selectedDate)
        .sort((a, b) =>
          (a.startTime ?? "").localeCompare(
            b.startTime ?? ""
          )
        ),
    [events, selectedDate]
  );

  const handleCreate = async () => {
    if (!title.trim()) {
      return;
    }

    await onCreateEvent?.({
      title: title.trim(),
      date: selectedDate,
      startTime,
      endTime,
      location: location.trim() || undefined,
      description:
        description.trim() || undefined,
    });

    setTitle("");
    setLocation("");
    setDescription("");
    setShowCreate(false);
  };

  return (
    <EnvironmentShell
      title="Calendar"
      subtitle={
        environmentId
          ? `Environment ${environmentId}`
          : "Schedule and manage events"
      }
      icon="▣"
      status="active"
      className={className}
      actions={
        <button
          type="button"
          onClick={() =>
            setShowCreate((value) => !value)
          }
          className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700"
        >
          + New event
        </button>
      }
    >
      <div className="p-5">
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <label className="text-xs font-medium text-gray-500">
            Date
          </label>

          <input
            type="date"
            value={selectedDate}
            onChange={(event) =>
              setSelectedDate(event.target.value)
            }
            className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          />
        </div>

        {showCreate && (
          <div className="mb-6 rounded-2xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
            <h3 className="mb-4 text-sm font-semibold text-gray-900 dark:text-white">
              Create event
            </h3>

            <div className="grid gap-3 md:grid-cols-2">
              <input
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                placeholder="Event title"
                className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950"
              />

              <input
                type="text"
                value={location}
                onChange={(event) =>
                  setLocation(event.target.value)
                }
                placeholder="Location"
                className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950"
              />

              <input
                type="time"
                value={startTime}
                onChange={(event) =>
                  setStartTime(event.target.value)
                }
                className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none dark:border-gray-700 dark:bg-gray-950"
              />

              <input
                type="time"
                value={endTime}
                onChange={(event) =>
                  setEndTime(event.target.value)
                }
                className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none dark:border-gray-700 dark:bg-gray-950"
              />
            </div>

            <textarea
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              placeholder="Description"
              rows={3}
              className="mt-3 w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950"
            />

            <div className="mt-3 flex justify-end gap-2">
              <button
                type="button"
                onClick={() =>
                  setShowCreate(false)
                }
                className="rounded-lg border border-gray-300 px-3 py-2 text-xs dark:border-gray-700"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={() => void handleCreate()}
                className="rounded-lg bg-blue-600 px-4 py-2 text-xs text-white hover:bg-blue-700"
              >
                Create event
              </button>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {selectedEvents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-gray-300 px-5 py-12 text-center dark:border-gray-700">
              <div className="text-2xl">▣</div>

              <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                No events scheduled
              </p>

              <p className="mt-1 text-xs text-gray-400">
                Your schedule is clear for this date.
              </p>
            </div>
          ) : (
            selectedEvents.map((event) => (
              <button
                key={event.id}
                type="button"
                onClick={() =>
                  onSelectEvent?.(event)
                }
                className="block w-full rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-blue-300 hover:shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-800"
              >
                <div className="flex gap-4">
                  <div className="w-20 shrink-0 text-xs font-medium text-blue-600 dark:text-blue-400">
                    {event.startTime ?? "--:--"}
                    {event.endTime && (
                      <>
                        <br />
                        <span className="text-gray-400">
                          {event.endTime}
                        </span>
                      </>
                    )}
                  </div>

                  <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                      {event.title}
                    </h4>

                    {event.location && (
                      <p className="mt-1 text-xs text-gray-500">
                        {event.location}
                      </p>
                    )}

                    {event.description && (
                      <p className="mt-1 text-xs text-gray-400">
                        {event.description}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </EnvironmentShell>
  );
}
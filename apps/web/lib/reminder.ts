/**
 * AIOS Reminder API
 *
 * Current backend reminder routes use an
 * in-memory store. This service abstracts
 * those routes from the UI.
 */

import {
  apiDelete,
  apiGet,
  apiPost,
} from "./api";

export type ReminderStatus =
  | "pending"
  | "scheduled"
  | "active"
  | "completed"
  | "cancelled"
  | "expired"
  | "failed"
  | string;

export interface Reminder {
  id: string;
  title: string;
  description?: string;
  status?: ReminderStatus;
  reminderAt?: string;
  scheduledAt?: string;
  dueAt?: string;
  createdAt?: string;
  updatedAt?: string;
  recurring?: boolean;
  recurrence?: string;
  priority?: string;
  category?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CreateReminderRequest {
  title: string;
  description?: string;
  reminderAt?: string;
  scheduledAt?: string;
  dueAt?: string;
  recurring?: boolean;
  recurrence?: string;
  priority?: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

export const reminderApi = {
  list() {
    return apiGet<Reminder[]>(
      "/reminders"
    );
  },

  get(reminderId: string) {
    return apiGet<Reminder>(
      `/reminders/${encodeURIComponent(
        reminderId
      )}`
    );
  },

  create(
    request: CreateReminderRequest
  ) {
    return apiPost<
      Reminder,
      CreateReminderRequest
    >(
      "/reminders",
      request
    );
  },

  cancel(reminderId: string) {
    return apiPost<Reminder>(
      `/reminders/${encodeURIComponent(
        reminderId
      )}/cancel`
    );
  },

  delete(reminderId: string) {
    return apiDelete(
      `/reminders/${encodeURIComponent(
        reminderId
      )}`
    );
  },
};
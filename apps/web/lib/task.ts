/**
 * AIOS Task API
 *
 * Temporary backend route currently uses an
 * in-memory task store. This service is kept
 * independent so persistence can be changed later.
 */

import {
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
} from "./api";

export type TaskStatus =
  | "pending"
  | "queued"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled"
  | string;

export type TaskPriority =
  | "low"
  | "medium"
  | "high"
  | "critical"
  | string;

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority?: TaskPriority;
  type?: string;
  environmentId?: string;
  environment_id?: string;
  progress?: number;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
  startedAt?: string;
  started_at?: string;
  completedAt?: string;
  completed_at?: string;
  dueAt?: string;
  due_at?: string;
  error?: string;
  metadata?: Record<
    string,
    unknown
  >;
  [key: string]: unknown;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  priority?: TaskPriority;
  type?: string;
  environmentId?: string;
  dueAt?: string;
  metadata?: Record<
    string,
    unknown
  >;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  progress?: number;
  dueAt?: string;
  metadata?: Record<
    string,
    unknown
  >;
}

export const taskApi = {
  list() {
    return apiGet<Task[]>(
      "/tasks"
    );
  },

  get(taskId: string) {
    return apiGet<Task>(
      `/tasks/${encodeURIComponent(
        taskId
      )}`
    );
  },

  create(
    request: CreateTaskRequest
  ) {
    return apiPost<
      Task,
      CreateTaskRequest
    >(
      "/tasks",
      request
    );
  },

  update(
    taskId: string,
    request: UpdateTaskRequest
  ) {
    return apiPatch<
      Task,
      UpdateTaskRequest
    >(
      `/tasks/${encodeURIComponent(
        taskId
      )}`,
      request
    );
  },

  complete(taskId: string) {
    return apiPost<Task>(
      `/tasks/${encodeURIComponent(
        taskId
      )}/complete`
    );
  },

  cancel(taskId: string) {
    return apiPost<Task>(
      `/tasks/${encodeURIComponent(
        taskId
      )}/cancel`
    );
  },

  delete(taskId: string) {
    return apiDelete(
      `/tasks/${encodeURIComponent(
        taskId
      )}`
    );
  },
};
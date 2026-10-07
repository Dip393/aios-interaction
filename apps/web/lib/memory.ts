/**
 * AIOS Memory API
 */

import {
  apiDelete,
  apiGet,
  apiPost,
} from "./api";

export interface MemoryItem {
  id: string;
  content: string;
  type?: string;
  category?: string;
  importance?: number;
  relevance?: number;
  timestamp?: string;
  createdAt?: string;
  updatedAt?: string;
  taskId?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface MemoryStats {
  shortTerm?: number;
  working?: number;
  longTerm?: number;
  semantic?: number;
  total?: number;
  [key: string]: unknown;
}

export interface RememberRequest {
  content: string;
  category?: string;
  importance?: number;
  metadata?: Record<string, unknown>;
}

export interface SemanticMemoryRequest {
  content: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface SemanticSearchResponse {
  results?: MemoryItem[];
  items?: MemoryItem[];
  [key: string]: unknown;
}

export interface TaskMemoryRequest {
  taskId: string;
  variables?: Record<string, unknown>;
  facts?: Record<string, unknown>;
  decisions?: string[];
  pendingActions?: string[];
  completedActions?: string[];
}

export const memoryApi = {
  stats() {
    return apiGet<MemoryStats>(
      "/memory/stats"
    );
  },

  addRecent(
    content: string,
    metadata?: Record<string, unknown>
  ) {
    return apiPost<MemoryItem>(
      "/memory/recent",
      {
        content,
        metadata,
      }
    );
  },

  recent(limit?: number) {
    return apiGet<MemoryItem[]>(
      "/memory/recent",
      {
        limit,
      }
    );
  },

  remember(
    request: RememberRequest
  ) {
    return apiPost<
      MemoryItem,
      RememberRequest
    >(
      "/memory/long-term",
      request
    );
  },

  recall(
    query: string,
    options: {
      category?: string;
      limit?: number;
    } = {}
  ) {
    return apiGet<MemoryItem[]>(
      "/memory/recall",
      {
        query,
        ...options,
      }
    );
  },

  rememberSemantic(
    request: SemanticMemoryRequest
  ) {
    return apiPost<
      MemoryItem,
      SemanticMemoryRequest
    >(
      "/memory/semantic",
      request
    );
  },

  semanticSearch(
    query: string,
    limit?: number
  ) {
    return apiGet<SemanticSearchResponse>(
      "/memory/semantic/search",
      {
        query,
        limit,
      }
    );
  },

  createTaskMemory(
    request: TaskMemoryRequest
  ) {
    return apiPost(
      "/memory/tasks",
      request
    );
  },

  getTaskMemory(
    taskId: string
  ) {
    return apiGet(
      `/memory/tasks/${encodeURIComponent(
        taskId
      )}`
    );
  },

  deleteTaskMemory(
    taskId: string
  ) {
    return apiDelete(
      `/memory/tasks/${encodeURIComponent(
        taskId
      )}`
    );
  },

  /**
   * Forget/delete a long-term memory.
   */
  forget(
    memoryId: string
  ) {
    return apiDelete(
      `/memory/${encodeURIComponent(
        memoryId
      )}`
    );
  },

  consolidate() {
    return apiPost(
      "/memory/consolidate"
    );
  },
};
/**
 * AIOS Frontend API Client
 *
 * Shared HTTP client for all frontend -> backend communication.
 * Domain-specific API helpers live in the other files under /lib.
 */

export interface ApiRequestOptions extends RequestInit {
  query?: Record<
    string,
    string | number | boolean | null | undefined
  >;
}

export interface ApiErrorData {
  detail?: string;
  message?: string;
  error?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  data?: ApiErrorData;

  constructor(
    message: string,
    status: number,
    data?: ApiErrorData
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

const DEFAULT_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "/api";

/**
 * Build the final API URL.
 */
function buildUrl(
  path: string,
  query?: ApiRequestOptions["query"]
): string {
  const base = DEFAULT_API_BASE_URL.replace(/\/+$/, "");

  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  const url = `${base}${normalizedPath}`;

  if (!query) {
    return url;
  }

  const params = new URLSearchParams();

  Object.entries(query).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null
    ) {
      params.set(key, String(value));
    }
  });

  const queryString = params.toString();

  return queryString
    ? `${url}?${queryString}`
    : url;
}

/**
 * Parse an HTTP response.
 */
async function parseResponse(
  response: Response
): Promise<unknown> {
  const contentType =
    response.headers.get("content-type") ?? "";

  if (
    contentType.includes("application/json")
  ) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  const text = await response.text();

  return text || null;
}

/**
 * Extract a useful error message from
 * a backend response.
 */
function extractErrorMessage(
  data: unknown,
  status: number
): string {
  if (
    data &&
    typeof data === "object"
  ) {
    const value = data as ApiErrorData;

    if (
      typeof value.detail === "string"
    ) {
      return value.detail;
    }

    if (
      typeof value.message === "string"
    ) {
      return value.message;
    }

    if (
      typeof value.error === "string"
    ) {
      return value.error;
    }
  }

  return `API request failed with status ${status}.`;
}

/**
 * Generic API request function.
 */
export async function apiRequest<T = unknown>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const {
    query,
    headers,
    body,
    ...requestOptions
  } = options;

  const requestHeaders = new Headers(headers);

  /**
   * Automatically set JSON content type
   * unless the body is FormData or the
   * caller already provided Content-Type.
   */
  if (
    body !== undefined &&
    !(body instanceof FormData) &&
    !requestHeaders.has("Content-Type")
  ) {
    requestHeaders.set(
      "Content-Type",
      "application/json"
    );
  }

  /**
   * Request JSON by default.
   */
  if (!requestHeaders.has("Accept")) {
    requestHeaders.set(
      "Accept",
      "application/json"
    );
  }

  const response = await fetch(
    buildUrl(path, query),
    {
      ...requestOptions,
      headers: requestHeaders,
      body,
    }
  );

  const data =
    await parseResponse(response);

  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(
        data,
        response.status
      ),
      response.status,
      data &&
      typeof data === "object"
        ? (data as ApiErrorData)
        : undefined
    );
  }

  return data as T;
}

/**
 * GET request helper.
 */
export function apiGet<T = unknown>(
  path: string,
  query?: ApiRequestOptions["query"],
  options: Omit<
    ApiRequestOptions,
    "method" | "body" | "query"
  > = {}
) {
  return apiRequest<T>(path, {
    ...options,
    method: "GET",
    query,
  });
}

/**
 * POST request helper.
 */
export function apiPost<
  T = unknown,
  B = unknown
>(
  path: string,
  body?: B,
  options: Omit<
    ApiRequestOptions,
    "method" | "body"
  > = {}
) {
  return apiRequest<T>(path, {
    ...options,
    method: "POST",
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
        ? body
        : JSON.stringify(body),
  });
}

/**
 * PATCH request helper.
 */
export function apiPatch<
  T = unknown,
  B = unknown
>(
  path: string,
  body?: B,
  options: Omit<
    ApiRequestOptions,
    "method" | "body"
  > = {}
) {
  return apiRequest<T>(path, {
    ...options,
    method: "PATCH",
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
        ? body
        : JSON.stringify(body),
  });
}

/**
 * PUT request helper.
 */
export function apiPut<
  T = unknown,
  B = unknown
>(
  path: string,
  body?: B,
  options: Omit<
    ApiRequestOptions,
    "method" | "body"
  > = {}
) {
  return apiRequest<T>(path, {
    ...options,
    method: "PUT",
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
        ? body
        : JSON.stringify(body),
  });
}

/**
 * DELETE request helper.
 */
export function apiDelete<T = unknown>(
  path: string,
  options: Omit<
    ApiRequestOptions,
    "method" | "body"
  > = {}
) {
  return apiRequest<T>(path, {
    ...options,
    method: "DELETE",
  });
}

/**
 * Create a domain-specific API client.
 */
export function createApiClient(
  basePath = ""
) {
  const normalizedBasePath = basePath
    ? basePath.replace(/^\/+|\/+$/g, "")
    : "";

  const prefix = normalizedBasePath
    ? `/${normalizedBasePath}`
    : "";

  const joinPath = (path: string) => {
    if (!path) {
      return prefix || "/";
    }

    return `${prefix}${
      path.startsWith("/") ? path : `/${path}`
    }`;
  };

  return {
    get<T = unknown>(
      path = "",
      query?: ApiRequestOptions["query"]
    ) {
      return apiGet<T>(
        joinPath(path),
        query
      );
    },

    post<T = unknown, B = unknown>(
      path = "",
      body?: B
    ) {
      return apiPost<T, B>(
        joinPath(path),
        body
      );
    },

    patch<T = unknown, B = unknown>(
      path = "",
      body?: B
    ) {
      return apiPatch<T, B>(
        joinPath(path),
        body
      );
    },

    put<T = unknown, B = unknown>(
      path = "",
      body?: B
    ) {
      return apiPut<T, B>(
        joinPath(path),
        body
      );
    },

    delete<T = unknown>(
      path = ""
    ) {
      return apiDelete<T>(
        joinPath(path)
      );
    },
  };
}

/**
 * Default shared API client.
 *
 * Supports:
 *
 * api.get("/tasks")
 * api.post("/tasks", {...})
 *
 * and also:
 *
 * api("/tasks")
 */
const apiClient = createApiClient();

export const api = Object.assign(
  <T = unknown>(
    path: string,
    options: ApiRequestOptions = {}
  ) => apiRequest<T>(path, options),
  apiClient
);
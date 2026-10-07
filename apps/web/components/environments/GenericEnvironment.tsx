"use client";

import React from "react";
import EnvironmentShell from "./EnvironmentShell";

export interface GenericEnvironmentProps {
  environmentId?: string;
  title?: string;
  subtitle?: string;
  type?: string;

  // Environment status can be extended by the AIOS runtime.
  // Examples: active, paused, completed, error, idle, destroyed, etc.
  status?: string;

  data?: Record<string, unknown>;
  children?: React.ReactNode;
  className?: string;
}

export default function GenericEnvironment({
  environmentId,
  title = "AIOS Environment",
  subtitle,
  type = "generic",
  status = "active",
  data = {},
  children,
  className = "",
}: GenericEnvironmentProps) {
  const entries = Object.entries(data);

  return (
    <EnvironmentShell
      title={title}
      subtitle={
        subtitle ??
        `${type}${environmentId ? ` · ${environmentId}` : ""}`
      }
      icon="◇"
      status={status}
      className={className}
    >
      <div className="p-6">
        {children ? (
          children
        ) : (
          <div className="mx-auto max-w-3xl">
            <div className="rounded-2xl border border-dashed border-gray-300 p-10 text-center dark:border-gray-700">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-xl text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
                ◇
              </div>

              <h3 className="mt-4 font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>

              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                This environment does not have a specialized interface yet.
              </p>
            </div>

            {entries.length > 0 && (
              <div className="mt-5 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
                <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 text-xs font-semibold text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
                  Environment Data
                </div>

                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {entries.map(([key, value]) => (
                    <div
                      key={key}
                      className="grid grid-cols-3 gap-4 px-4 py-3 text-xs"
                    >
                      <span className="font-medium text-gray-500">
                        {key}
                      </span>

                      <span className="col-span-2 break-words text-gray-700 dark:text-gray-300">
                        {typeof value === "string"
                          ? value
                          : JSON.stringify(value, null, 2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </EnvironmentShell>
  );
}
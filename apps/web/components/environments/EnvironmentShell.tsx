"use client";

import React, { ReactNode } from "react";

export interface EnvironmentShellProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  status?: string;
  children: ReactNode;
  actions?: ReactNode;
  sidebar?: ReactNode;
  className?: string;
}

const statusConfig = {
  active: {
    label: "Active",
    className:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
  },
  paused: {
    label: "Paused",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
  },
  completed: {
    label: "Completed",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
  },
  error: {
    label: "Error",
    className:
      "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
  },
  idle: {
    label: "Idle",
    className:
      "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  },
} as const;

const defaultStatus = {
  label: "Unknown",
  className:
    "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
};

export default function EnvironmentShell({
  title,
  subtitle,
  icon,
  status = "active",
  children,
  actions,
  sidebar,
  className = "",
}: EnvironmentShellProps) {
  const statusInfo =
    statusConfig[status as keyof typeof statusConfig] ?? defaultStatus;

  return (
    <section
      className={`flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-950 ${className}`}
    >
      <header className="flex shrink-0 items-center justify-between gap-4 border-b border-gray-200 px-5 py-4 dark:border-gray-800">
        <div className="flex min-w-0 items-center gap-3">
          {icon && (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
              {icon}
            </div>
          )}

          <div className="min-w-0">
            <h2 className="truncate font-semibold text-gray-900 dark:text-white">
              {title}
            </h2>

            {subtitle && (
              <p className="truncate text-xs text-gray-500 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>

          <span
            className={`hidden rounded-full px-2.5 py-1 text-[10px] font-medium sm:inline-flex ${statusInfo.className}`}
          >
            {statusInfo.label}
          </span>
        </div>

        {actions && (
          <div className="flex shrink-0 items-center gap-2">
            {actions}
          </div>
        )}
      </header>

      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 overflow-auto">
          {children}
        </main>

        {sidebar && (
          <aside className="hidden w-72 shrink-0 border-l border-gray-200 xl:block dark:border-gray-800">
            {sidebar}
          </aside>
        )}
      </div>
    </section>
  );
}
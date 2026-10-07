"use client";

import React from "react";

export type TaskStatusValue =
  | "pending"
  | "queued"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export interface TaskStatusProps {
  status: TaskStatusValue | string;
  size?: "sm" | "md";
  showLabel?: boolean;
  className?: string;
}

const statusConfig: Record<
  string,
  {
    label: string;
    dot: string;
    badge: string;
  }
> = {
  pending: {
    label: "Pending",
    dot: "bg-gray-400",
    badge:
      "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  },
  queued: {
    label: "Queued",
    dot: "bg-blue-500",
    badge:
      "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
  },
  running: {
    label: "Running",
    dot: "bg-amber-500 animate-pulse",
    badge:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
  },
  paused: {
    label: "Paused",
    dot: "bg-orange-500",
    badge:
      "bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400",
  },
  completed: {
    label: "Completed",
    dot: "bg-emerald-500",
    badge:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
  },
  failed: {
    label: "Failed",
    dot: "bg-red-500",
    badge:
      "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
  },
  cancelled: {
    label: "Cancelled",
    dot: "bg-gray-500",
    badge:
      "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  },
};

export default function TaskStatus({
  status,
  size = "md",
  showLabel = true,
  className = "",
}: TaskStatusProps) {
  const normalizedStatus = status.toLowerCase().trim();

  const config =
    statusConfig[normalizedStatus] ??
    statusConfig.pending;

  const sizeClasses =
    size === "sm"
      ? {
          container: "px-2 py-0.5 text-[10px]",
          dot: "h-1.5 w-1.5",
        }
      : {
          container: "px-2.5 py-1 text-xs",
          dot: "h-2 w-2",
        };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sizeClasses.container} ${config.badge} ${className}`}
    >
      <span
        className={`rounded-full ${sizeClasses.dot} ${config.dot}`}
      />

      {showLabel && config.label}
    </span>
  );
}
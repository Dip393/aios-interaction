"use client";

import React from "react";

export interface ApprovalAction {
  id: string;
  title: string;
  description?: string;
  action?: string;
  risk?: "low" | "medium" | "high" | "critical";
  details?: Record<string, unknown>;
}

export interface ActionApprovalProps {
  action: ApprovalAction;
  onApprove: () => void;
  onReject: () => void;
  disabled?: boolean;
  className?: string;
}

const riskConfig = {
  low: {
    label: "Low risk",
    className:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
  },
  medium: {
    label: "Medium risk",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
  },
  high: {
    label: "High risk",
    className:
      "bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400",
  },
  critical: {
    label: "Critical risk",
    className:
      "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
  },
};

export default function ActionApproval({
  action,
  onApprove,
  onReject,
  disabled = false,
  className = "",
}: ActionApprovalProps) {
  const risk = action.risk ?? "medium";
  const riskInfo = riskConfig[risk];

  return (
    <div
      className={`rounded-2xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/50 dark:bg-amber-950/10 ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400">
          !
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {action.title}
            </h3>

            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskInfo.className}`}
            >
              {riskInfo.label}
            </span>
          </div>

          {action.description && (
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {action.description}
            </p>
          )}

          {action.action && (
            <div className="mt-3 rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-gray-800 dark:bg-gray-900">
              <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-gray-400">
                Action
              </p>

              <code className="break-all text-xs text-gray-700 dark:text-gray-300">
                {action.action}
              </code>
            </div>
          )}

          {action.details &&
            Object.keys(action.details).length > 0 && (
              <div className="mt-3 space-y-1">
                {Object.entries(action.details).map(
                  ([key, value]) => (
                    <div
                      key={key}
                      className="flex gap-2 text-xs"
                    >
                      <span className="font-medium text-gray-500">
                        {key}:
                      </span>

                      <span className="break-all text-gray-700 dark:text-gray-300">
                        {typeof value === "string"
                          ? value
                          : JSON.stringify(value)}
                      </span>
                    </div>
                  )
                )}
              </div>
            )}

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onApprove}
              disabled={disabled}
              className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Approve
            </button>

            <button
              type="button"
              onClick={onReject}
              disabled={disabled}
              className="rounded-xl border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
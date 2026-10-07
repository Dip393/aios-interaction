"use client";

import React from "react";

export interface ThinkingStatusProps {
  message?: string;
  steps?: string[];
  currentStep?: number;
  className?: string;
}

export default function ThinkingStatus({
  message = "AIOS is thinking...",
  steps = [
    "Understanding request",
    "Planning actions",
    "Checking permissions",
    "Preparing response",
  ],
  currentStep,
  className = "",
}: ThinkingStatusProps) {
  return (
    <div
      className={`flex justify-start ${className}`}
      aria-live="polite"
    >
      <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500" />
          </div>

          <span className="text-sm text-gray-600 dark:text-gray-300">
            {message}
          </span>
        </div>

        {steps.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {steps.map((step, index) => {
              const active =
                currentStep === undefined
                  ? index === 0
                  : index === currentStep;

              const completed =
                currentStep !== undefined &&
                index < currentStep;

              return (
                <div
                  key={`${step}-${index}`}
                  className="flex items-center gap-2 text-xs"
                >
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] ${
                      completed
                        ? "bg-emerald-500 text-white"
                        : active
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400"
                    }`}
                  >
                    {completed ? "✓" : index + 1}
                  </span>

                  <span
                    className={
                      active
                        ? "text-blue-600 dark:text-blue-400"
                        : "text-gray-400"
                    }
                  >
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
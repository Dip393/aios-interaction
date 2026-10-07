"use client";

import React, { useState } from "react";
import EnvironmentShell from "./EnvironmentShell";

export interface CodingEnvironmentProps {
  environmentId?: string;
  initialFileName?: string;
  initialCode?: string;
  language?: string;
  onRun?: (code: string) => void | Promise<void>;
  onSave?: (data: {
    fileName: string;
    code: string;
    language: string;
  }) => void | Promise<void>;
  className?: string;
}

export default function CodingEnvironment({
  environmentId,
  initialFileName = "main.py",
  initialCode = "",
  language = "python",
  onRun,
  onSave,
  className = "",
}: CodingEnvironmentProps) {
  const [fileName, setFileName] = useState(initialFileName);
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    setOutput("Running...");

    try {
      await onRun?.(code);

      if (!onRun) {
        setOutput(
          "Execution handler is not connected yet."
        );
      } else {
        setOutput("Execution completed.");
      }
    } catch (error) {
      setOutput(
        error instanceof Error
          ? error.message
          : "Execution failed."
      );
    } finally {
      setRunning(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      await onSave?.({
        fileName,
        code,
        language,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <EnvironmentShell
      title="Coding Environment"
      subtitle={
        environmentId
          ? `Environment ${environmentId}`
          : "AI-assisted development workspace"
      }
      icon="</>"
      status="active"
      className={className}
      actions={
        <>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900"
          >
            {saving ? "Saving..." : "Save"}
          </button>

          <button
            type="button"
            onClick={handleRun}
            disabled={running}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? "Running..." : "Run"}
          </button>
        </>
      }
    >
      <div className="flex h-full min-h-[600px] flex-col bg-gray-950 text-gray-200">
        <div className="flex items-center gap-2 border-b border-gray-800 bg-gray-900 px-4 py-2">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
          </div>

          <input
            value={fileName}
            onChange={(event) =>
              setFileName(event.target.value)
            }
            className="ml-3 w-48 bg-transparent text-xs text-gray-400 outline-none"
          />

          <span className="ml-auto text-[10px] uppercase tracking-wider text-gray-500">
            {language}
          </span>
        </div>

        <div className="flex min-h-0 flex-1">
          <div className="hidden w-12 shrink-0 border-r border-gray-800 bg-gray-950 py-4 text-right text-xs leading-6 text-gray-600 sm:block">
            {code.split("\n").map((_, index) => (
              <div
                key={index}
                className="px-2"
              >
                {index + 1}
              </div>
            ))}
          </div>

          <textarea
            value={code}
            onChange={(event) =>
              setCode(event.target.value)
            }
            spellCheck={false}
            className="min-h-[420px] min-w-0 flex-1 resize-none bg-gray-950 p-4 font-mono text-sm leading-6 text-gray-200 outline-none"
            placeholder={`# Start coding in ${language}...`}
          />
        </div>

        <div className="border-t border-gray-800 bg-black/30">
          <div className="border-b border-gray-800 px-4 py-2 text-[10px] font-medium uppercase tracking-wider text-gray-500">
            Output
          </div>

          <pre className="min-h-[100px] whitespace-pre-wrap px-4 py-3 font-mono text-xs text-gray-400">
            {output || "No output yet."}
          </pre>
        </div>
      </div>
    </EnvironmentShell>
  );
}
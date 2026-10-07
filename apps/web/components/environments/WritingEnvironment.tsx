"use client";

import React, { useMemo, useState } from "react";
import EnvironmentShell from "./EnvironmentShell";

export interface WritingEnvironmentProps {
  environmentId?: string;
  initialTitle?: string;
  initialContent?: string;
  onChange?: (data: {
    title: string;
    content: string;
  }) => void;
  onSave?: (data: {
    title: string;
    content: string;
  }) => void | Promise<void>;
  className?: string;
}

export default function WritingEnvironment({
  environmentId,
  initialTitle = "",
  initialContent = "",
  onChange,
  onSave,
  className = "",
}: WritingEnvironmentProps) {
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const [saving, setSaving] = useState(false);

  const wordCount = useMemo(() => {
    const trimmed = content.trim();

    if (!trimmed) {
      return 0;
    }

    return trimmed.split(/\s+/).length;
  }, [content]);

  const updateTitle = (value: string) => {
    setTitle(value);
    onChange?.({
      title: value,
      content,
    });
  };

  const updateContent = (value: string) => {
    setContent(value);
    onChange?.({
      title,
      content: value,
    });
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      await onSave?.({
        title,
        content,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <EnvironmentShell
      title="Writing Environment"
      subtitle={
        environmentId
          ? `Environment ${environmentId}`
          : "AI-assisted document workspace"
      }
      icon="✎"
      status="active"
      className={className}
      actions={
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      }
    >
      <div className="flex h-full flex-col">
        <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
          <input
            value={title}
            onChange={(event) =>
              updateTitle(event.target.value)
            }
            placeholder="Untitled document"
            className="w-full bg-transparent text-2xl font-semibold text-gray-900 outline-none placeholder:text-gray-300 dark:text-white dark:placeholder:text-gray-700"
          />
        </div>

        <div className="flex-1 px-6 py-5">
          <textarea
            value={content}
            onChange={(event) =>
              updateContent(event.target.value)
            }
            placeholder="Start writing..."
            className="h-full min-h-[500px] w-full resize-none bg-transparent text-base leading-8 text-gray-800 outline-none placeholder:text-gray-400 dark:text-gray-200"
          />
        </div>

        <footer className="flex items-center justify-between border-t border-gray-200 px-6 py-2 text-[10px] text-gray-400 dark:border-gray-800">
          <span>{wordCount} words</span>

          <span>
            {content.length} characters
          </span>
        </footer>
      </div>
    </EnvironmentShell>
  );
}
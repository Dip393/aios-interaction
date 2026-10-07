"use client";

import React, { FormEvent, useState } from "react";
import EnvironmentShell from "./EnvironmentShell";

export interface EmailEnvironmentProps {
  environmentId?: string;
  initialTo?: string;
  initialSubject?: string;
  initialBody?: string;
  onSend?: (data: {
    to: string;
    cc: string;
    bcc: string;
    subject: string;
    body: string;
  }) => void | Promise<void>;
  onSaveDraft?: (data: {
    to: string;
    cc: string;
    bcc: string;
    subject: string;
    body: string;
  }) => void | Promise<void>;
  className?: string;
}

export default function EmailEnvironment({
  environmentId,
  initialTo = "",
  initialSubject = "",
  initialBody = "",
  onSend,
  onSaveDraft,
  className = "",
}: EmailEnvironmentProps) {
  const [to, setTo] = useState(initialTo);
  const [cc, setCc] = useState("");
  const [bcc, setBcc] = useState("");
  const [subject, setSubject] = useState(initialSubject);
  const [body, setBody] = useState(initialBody);
  const [showCcBcc, setShowCcBcc] = useState(false);
  const [sending, setSending] = useState(false);
  const [saved, setSaved] = useState(false);

  const payload = {
    to,
    cc,
    bcc,
    subject,
    body,
  };

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();

    if (!to.trim() || !subject.trim() || !body.trim()) {
      return;
    }

    setSending(true);
    setSaved(false);

    try {
      await onSend?.(payload);
    } finally {
      setSending(false);
    }
  };

  const handleSaveDraft = async () => {
    setSending(true);

    try {
      await onSaveDraft?.(payload);
      setSaved(true);
    } finally {
      setSending(false);
    }
  };

  return (
    <EnvironmentShell
      title="Email"
      subtitle={
        environmentId
          ? `Environment ${environmentId}`
          : "Compose and manage email"
      }
      icon="✉"
      status="active"
      className={className}
      actions={
        <>
          <button
            type="button"
            onClick={handleSaveDraft}
            disabled={sending}
            className="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900"
          >
            Save draft
          </button>

          <button
            type="submit"
            form="aios-email-form"
            disabled={sending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </>
      }
    >
      <form
        id="aios-email-form"
        onSubmit={handleSend}
        className="mx-auto max-w-4xl p-6"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b border-gray-200 pb-3 dark:border-gray-800">
            <label className="w-16 text-sm text-gray-500">
              To
            </label>

            <input
              value={to}
              onChange={(event) => setTo(event.target.value)}
              placeholder="recipient@example.com"
              type="email"
              className="min-w-0 flex-1 bg-transparent text-sm text-gray-900 outline-none dark:text-white"
            />

            <button
              type="button"
              onClick={() => setShowCcBcc((value) => !value)}
              className="text-xs text-blue-600 hover:underline"
            >
              Cc/Bcc
            </button>
          </div>

          {showCcBcc && (
            <>
              <div className="flex items-center gap-2 border-b border-gray-200 pb-3 dark:border-gray-800">
                <label className="w-16 text-sm text-gray-500">
                  Cc
                </label>

                <input
                  value={cc}
                  onChange={(event) => setCc(event.target.value)}
                  placeholder="cc@example.com"
                  type="email"
                  className="flex-1 bg-transparent text-sm text-gray-900 outline-none dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 border-b border-gray-200 pb-3 dark:border-gray-800">
                <label className="w-16 text-sm text-gray-500">
                  Bcc
                </label>

                <input
                  value={bcc}
                  onChange={(event) => setBcc(event.target.value)}
                  placeholder="bcc@example.com"
                  type="email"
                  className="flex-1 bg-transparent text-sm text-gray-900 outline-none dark:text-white"
                />
              </div>
            </>
          )}

          <div className="flex items-center gap-2 border-b border-gray-200 pb-3 dark:border-gray-800">
            <label className="w-16 text-sm text-gray-500">
              Subject
            </label>

            <input
              value={subject}
              onChange={(event) =>
                setSubject(event.target.value)
              }
              placeholder="Subject"
              className="flex-1 bg-transparent text-sm font-medium text-gray-900 outline-none dark:text-white"
            />
          </div>

          <textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Write your email..."
            className="min-h-[420px] w-full resize-none bg-transparent text-sm leading-7 text-gray-800 outline-none placeholder:text-gray-400 dark:text-gray-200"
          />

          {saved && (
            <div className="rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
              Draft saved successfully.
            </div>
          )}
        </div>
      </form>
    </EnvironmentShell>
  );
}
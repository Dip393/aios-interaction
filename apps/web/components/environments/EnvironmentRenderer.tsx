"use client";

import React from "react";

import CalendarEnvironment from "./CalendarEnvironment";
import CodingEnvironment from "./CodingEnvironment";
import EmailEnvironment from "./EmailEnvironment";
import GenericEnvironment from "./GenericEnvironment";
import WritingEnvironment from "./WritingEnvironment";

export type EnvironmentType =
  | "email"
  | "writing"
  | "coding"
  | "calendar"
  | "generic"
  | "document"
  | "project"
  | "search"
  | "research"
  | "reminder"
  | "code"
  | "unknown";

export type EnvironmentStatus =
  | "active"
  | "paused"
  | "completed"
  | "error"
  | "idle"
  | "destroyed";

export interface EnvironmentData {
  id?: string;
  environmentId?: string;
  type: EnvironmentType | string;
  name?: string;
  title?: string;
  subtitle?: string;
  status?: string;
  data?: Record<string, unknown>;
}

export interface EnvironmentRendererProps {
  environment: EnvironmentData;
  className?: string;

  onEmailSend?: (data: {
    to: string;
    cc: string;
    bcc: string;
    subject: string;
    body: string;
  }) => void | Promise<void>;

  onEmailSaveDraft?: (data: {
    to: string;
    cc: string;
    bcc: string;
    subject: string;
    body: string;
  }) => void | Promise<void>;

  onWritingChange?: (data: {
    title: string;
    content: string;
  }) => void;

  onWritingSave?: (data: {
    title: string;
    content: string;
  }) => void | Promise<void>;

  onCodeRun?: (
    code: string
  ) => void | Promise<void>;

  onCodeSave?: (data: {
    fileName: string;
    code: string;
    language: string;
  }) => void | Promise<void>;

  onCalendarCreateEvent?: (
    event: {
      title: string;
      date: string;
      startTime?: string;
      endTime?: string;
      description?: string;
      location?: string;
    }
  ) => void | Promise<void>;

  onCalendarSelectEvent?: (
    event: {
      id: string;
      title: string;
      date: string;
      startTime?: string;
      endTime?: string;
      description?: string;
      location?: string;
    }
  ) => void;
}

function getEnvironmentData(
  environment: EnvironmentData
): Record<string, unknown> {
  if (
    environment.data &&
    typeof environment.data === "object"
  ) {
    return environment.data;
  }

  return {};
}

function normalizeType(
  type: string
): EnvironmentType {
  const normalized = type
    .toLowerCase()
    .trim()
    .replace(/[\s-]+/g, "_");

  switch (normalized) {
    case "email":
    case "mail":
    case "email_environment":
      return "email";

    case "writing":
    case "writer":
    case "writing_environment":
      return "writing";

    case "coding":
    case "code":
    case "developer":
    case "development":
    case "coding_environment":
      return "coding";

    case "calendar":
    case "schedule":
    case "calendar_environment":
      return "calendar";

    case "document":
      return "document";

    case "project":
      return "project";

    case "search":
      return "search";

    case "research":
      return "research";

    case "reminder":
      return "reminder";

    default:
      return "generic";
  }
}

function normalizeStatus(
  status?: string
): EnvironmentStatus {
  switch (status?.toLowerCase()) {
    case "active":
      return "active";

    case "paused":
      return "paused";

    case "completed":
      return "completed";

    case "error":
      return "error";

    case "idle":
      return "idle";

    case "destroyed":
      return "destroyed";

    default:
      return "active";
  }
}

export default function EnvironmentRenderer({
  environment,
  className = "",
  onEmailSend,
  onEmailSaveDraft,
  onWritingChange,
  onWritingSave,
  onCodeRun,
  onCodeSave,
  onCalendarCreateEvent,
  onCalendarSelectEvent,
}: EnvironmentRendererProps) {
  const type = normalizeType(
    environment.type
  );

  const data =
    getEnvironmentData(environment);

  const environmentId =
    environment.environmentId ??
    environment.id;

  if (type === "email") {
    return (
      <EmailEnvironment
        environmentId={environmentId}
        initialTo={
          typeof data.to === "string"
            ? data.to
            : ""
        }
        initialSubject={
          typeof data.subject === "string"
            ? data.subject
            : ""
        }
        initialBody={
          typeof data.body === "string"
            ? data.body
            : ""
        }
        onSend={onEmailSend}
        onSaveDraft={onEmailSaveDraft}
        className={className}
      />
    );
  }

  if (type === "writing") {
    return (
      <WritingEnvironment
        environmentId={environmentId}
        initialTitle={
          typeof data.title === "string"
            ? data.title
            : environment.title ?? ""
        }
        initialContent={
          typeof data.content === "string"
            ? data.content
            : ""
        }
        onChange={onWritingChange}
        onSave={onWritingSave}
        className={className}
      />
    );
  }

  if (type === "coding") {
    return (
      <CodingEnvironment
        environmentId={environmentId}
        initialFileName={
          typeof data.fileName === "string"
            ? data.fileName
            : "main.py"
        }
        initialCode={
          typeof data.code === "string"
            ? data.code
            : ""
        }
        language={
          typeof data.language === "string"
            ? data.language
            : "python"
        }
        onRun={onCodeRun}
        onSave={onCodeSave}
        className={className}
      />
    );
  }

  if (type === "calendar") {
    const rawEvents = Array.isArray(
      data.events
    )
      ? data.events
      : [];

    const events = rawEvents.filter(
      (
        event
      ): event is {
        id: string;
        title: string;
        date: string;
        startTime?: string;
        endTime?: string;
        description?: string;
        location?: string;
      } => {
        if (
          !event ||
          typeof event !== "object"
        ) {
          return false;
        }

        const value =
          event as Record<
            string,
            unknown
          >;

        return (
          typeof value.id === "string" &&
          typeof value.title === "string" &&
          typeof value.date === "string"
        );
      }
    );

    return (
      <CalendarEnvironment
        environmentId={environmentId}
        events={events}
        onCreateEvent={
          onCalendarCreateEvent
        }
        onSelectEvent={
          onCalendarSelectEvent
        }
        className={className}
      />
    );
  }

  return (
    <GenericEnvironment
      environmentId={environmentId}
      title={
        environment.title ??
        environment.name ??
        "AIOS Environment"
      }
      subtitle={environment.subtitle}
      type={environment.type}
      status={normalizeStatus(
        environment.status
      )}
      data={data}
      className={className}
    />
  );
}
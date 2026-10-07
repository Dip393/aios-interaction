"use client";

import React, {
  ChangeEvent,
  FormEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import VoiceButton from "./VoiceButton";
import ThinkingStatus from "./ThinkingStatus";
import ActionApproval from "./ActionApproval";
import ActivityStream, {
  ActivityItem,
} from "./ActivityStream";

import CameraView from "@/components/vision/CameraView";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp?: string;
  status?: "sending" | "sent" | "error";
}

export interface PendingAction {
  id: string;
  title: string;
  description?: string;
  action?: string;
  risk?: "low" | "medium" | "high" | "critical";
  details?: Record<string, unknown>;
}

export interface AIChatProps {
  apiUrl?: string;
  sessionId?: string;
  initialMessages?: ChatMessage[];
  placeholder?: string;
  title?: string;
  subtitle?: string;
  className?: string;
  showVoice?: boolean;
  showActivity?: boolean;
  showImage?: boolean;
  showCamera?: boolean;
  onMessage?: (message: ChatMessage) => void;
  onActionApproval?: (
    action: PendingAction,
    approved: boolean
  ) => void;
}

const createId = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 9)}`;

const createTimestamp = () => new Date().toISOString();

const defaultMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "Hello! I’m AIOS. Tell me what you want to do, and I’ll understand the task, plan the required actions, and help you execute it.",
    status: "sent",
  },
];

export default function AIChat({
  apiUrl = "/api/kernel/process",
  sessionId,
  initialMessages,
  placeholder = "Tell AIOS what you want to do...",
  title = "AIOS Assistant",
  subtitle = "AI-powered operating environment",
  className = "",
  showVoice = true,
  showActivity = true,
  showImage = true,
  showCamera = true,
  onMessage,
  onActionApproval,
}: AIChatProps) {
  const initialChatMessages = useMemo(
    () => initialMessages ?? defaultMessages,
    [initialMessages]
  );

  const [messages, setMessages] =
    useState<ChatMessage[]>(initialChatMessages);

  const [input, setInput] = useState("");

  const [isThinking, setIsThinking] =
    useState(false);

  const [pendingAction, setPendingAction] =
    useState<PendingAction | null>(null);

  const [activities, setActivities] =
    useState<ActivityItem[]>([]);

  const [error, setError] =
    useState<string | null>(null);

  const [isHydrated, setIsHydrated] =
    useState(false);

  const [selectedImage, setSelectedImage] =
    useState<string | null>(null);

  const [selectedImageName, setSelectedImageName] =
    useState<string | null>(null);

  const [isCameraOpen, setIsCameraOpen] =
    useState(false);

  const imageInputRef =
    useRef<HTMLInputElement>(null);

  const textareaRef =
    useRef<HTMLTextAreaElement>(null);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isThinking]);

  const formatMessageTime = (
    timestamp?: string
  ) => {
    if (!timestamp || !isHydrated) {
      return "";
    }

    return new Date(timestamp).toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  };

  const addActivity = (
    type: ActivityItem["type"],
    title: string,
    description?: string
  ) => {
    const item: ActivityItem = {
      id: createId("activity"),
      type,
      title,
      description,
      timestamp: createTimestamp(),
    };

    setActivities((previous) => [
      ...previous,
      item,
    ]);
  };

  const addMessage = (
    message: ChatMessage
  ) => {
    setMessages((previous) => [
      ...previous,
      message,
    ]);

    onMessage?.(message);
  };

  const extractAssistantText = (
    data: unknown
  ): string => {
    if (
      !data ||
      typeof data !== "object"
    ) {
      return "I received a response, but there was no readable result.";
    }

    const payload =
      data as Record<string, unknown>;

    const candidates = [
      payload.response,
      payload.message,
      payload.output,
      payload.result,
      payload.content,
      payload.text,
    ];

    for (const candidate of candidates) {
      if (
        typeof candidate === "string" &&
        candidate.trim()
      ) {
        return candidate;
      }
    }

    if (
      payload.result &&
      typeof payload.result === "object" &&
      payload.result !== null
    ) {
      const result =
        payload.result as Record<
          string,
          unknown
        >;

      for (const key of [
        "response",
        "message",
        "output",
        "content",
        "text",
      ]) {
        if (
          typeof result[key] === "string" &&
          result[key].trim()
        ) {
          return result[key] as string;
        }
      }
    }

    return "Task processed successfully.";
  };

  const extractPendingAction = (
    data: unknown
  ): PendingAction | null => {
    if (
      !data ||
      typeof data !== "object"
    ) {
      return null;
    }

    const payload =
      data as Record<string, unknown>;

    const action =
      payload.pending_action ??
      payload.pendingAction ??
      payload.approval ??
      payload.action_approval;

    if (
      !action ||
      typeof action !== "object"
    ) {
      return null;
    }

    const value =
      action as Record<string, unknown>;

    if (value.required === false) {
      return null;
    }

    return {
      id:
        typeof value.id === "string"
          ? value.id
          : createId("action"),

      title:
        typeof value.title === "string"
          ? value.title
          : "Action requires approval",

      description:
        typeof value.description === "string"
          ? value.description
          : undefined,

      action:
        typeof value.action === "string"
          ? value.action
          : undefined,

      risk:
        value.risk === "low" ||
        value.risk === "medium" ||
        value.risk === "high" ||
        value.risk === "critical"
          ? value.risk
          : "medium",

      details:
        value.details &&
        typeof value.details === "object"
          ? (value.details as Record<
              string,
              unknown
            >)
          : undefined,
    };
  };

  const sendMessage = async (
    text: string
  ) => {
    const trimmed = text.trim();

    if (
      !trimmed ||
      isThinking
    ) {
      return;
    }

    setInput("");
    setError(null);

    const userMessage: ChatMessage = {
      id: createId("user"),
      role: "user",
      content: trimmed,
      timestamp: createTimestamp(),
      status: "sent",
    };

    addMessage(userMessage);

    addActivity(
      "user",
      "Request received",
      trimmed
    );

    if (selectedImageName) {
      addActivity(
        "user",
        "Image attached",
        selectedImageName
      );
    }

    setIsThinking(true);

    addActivity(
      "thinking",
      "AIOS is thinking",
      "Understanding your request and preparing a plan."
    );

    try {
      const response = await fetch(
        apiUrl,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            input: trimmed,
            session_id: sessionId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `AIOS request failed with status ${response.status}`
        );
      }

      const data =
        await response.json();

      const assistantText =
        extractAssistantText(data);

      const action =
        extractPendingAction(data);

      addActivity(
        "assistant",
        "Response generated",
        assistantText
      );

      if (action) {
        setPendingAction(action);

        addActivity(
          "approval",
          "Approval required",
          action.title
        );
      }

      const assistantMessage: ChatMessage =
        {
          id: createId("assistant"),
          role: "assistant",
          content: assistantText,
          timestamp: createTimestamp(),
          status: "sent",
        };

      addMessage(
        assistantMessage
      );

      /*
       * Clear the selected attachment after
       * the request has been processed.
       */
      setSelectedImage(null);
      setSelectedImageName(null);
    } catch (
      requestError
    ) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong while processing your request.";

      setError(message);

      addActivity(
        "error",
        "Request failed",
        message
      );

      addMessage({
        id: createId("error"),
        role: "assistant",
        content:
          "I couldn't complete that request. Please check the AIOS backend connection and try again.",
        timestamp:
          createTimestamp(),
        status: "error",
      });
    } finally {
      setIsThinking(false);
    }
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    await sendMessage(input);
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      void sendMessage(input);
    }
  };

  const handleVoiceTranscript = (
    text: string
  ) => {
    if (!text.trim()) {
      return;
    }

    setInput(text);

    void sendMessage(text);
  };

  const handleImageClick = () => {
    if (isThinking) {
      return;
    }

    imageInputRef.current?.click();
  };

  const handleImageSelected = (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      setError(
        "Please select a valid image file."
      );

      return;
    }

    const maxSize =
      10 * 1024 * 1024;

    if (file.size > maxSize) {
      setError(
        "Image size must be smaller than 10 MB."
      );

      return;
    }

    setError(null);

    const reader =
      new FileReader();

    reader.onload = () => {
      if (
        typeof reader.result ===
        "string"
      ) {
        setSelectedImage(
          reader.result
        );

        setSelectedImageName(
          file.name
        );

        addActivity(
          "user",
          "Image selected",
          file.name
        );
      }
    };

    reader.onerror = () => {
      setError(
        "Could not read the selected image."
      );
    };

    reader.readAsDataURL(file);

    /*
     * Allow selecting the same image again.
     */
    event.target.value = "";
  };

  const removeSelectedImage = () => {
    setSelectedImage(null);
    setSelectedImageName(null);
  };

  const handleCameraOpen = () => {
    if (isThinking) {
      return;
    }

    setError(null);
    setIsCameraOpen(true);

    addActivity(
      "user",
      "Camera opened",
      "AIOS Vision mode is ready."
    );
  };

  const handleCameraClose = () => {
    setIsCameraOpen(false);

    addActivity(
      "user",
      "Camera closed"
    );
  };

  const handleApproval = async (
    approved: boolean
  ) => {
    if (!pendingAction) {
      return;
    }

    const action =
      pendingAction;

    setPendingAction(null);

    onActionApproval?.(
      action,
      approved
    );

    addActivity(
      approved
        ? "success"
        : "warning",
      approved
        ? "Action approved"
        : "Action rejected",
      action.title
    );

    addMessage({
      id: createId("system"),
      role: "system",
      content: approved
        ? `Approved: ${action.title}`
        : `Rejected: ${action.title}`,
      timestamp: createTimestamp(),
      status: "sent",
    });

    if (!approved) {
      return;
    }

    try {
      const response =
        await fetch(
          "/api/kernel/confirm",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              action_id:
                action.id,
              approved: true,
              session_id:
                sessionId,
            }),
          }
        );

      if (!response.ok) {
        throw new Error(
          `Confirmation failed with status ${response.status}`
        );
      }

      addActivity(
        "success",
        "Action confirmed",
        "AIOS accepted the approval."
      );
    } catch (
      confirmationError
    ) {
      const message =
        confirmationError instanceof
        Error
          ? confirmationError.message
          : "Action confirmation failed.";

      setError(message);

      addActivity(
        "error",
        "Confirmation failed",
        message
      );
    }
  };

  return (
    <>
      <section
        className={`flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-xl ${className}`}
      >
        {/* Header */}
        <header className="flex shrink-0 items-center justify-between border-b border-slate-800 bg-slate-950 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 font-bold text-white shadow-lg shadow-blue-600/20">
              AI
            </div>

            <div>
              <h2 className="font-semibold text-white">
                {title}
              </h2>

              <p className="text-xs text-slate-400">
                {subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isThinking
                  ? "animate-pulse bg-amber-400"
                  : "bg-emerald-400"
              }`}
            />

            <span className="text-xs text-slate-400">
              {isThinking
                ? "Thinking"
                : "Ready"}
            </span>
          </div>
        </header>

        {/* Main */}
        <div className="flex min-h-0 flex-1">
          {/* Conversation */}
          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            {/* Messages */}
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5">
              {messages.map(
                (message) => {
                  const isUser =
                    message.role ===
                    "user";

                  const isSystem =
                    message.role ===
                    "system";

                  return (
                    <div
                      key={
                        message.id
                      }
                      className={`flex ${
                        isUser
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                          isUser
                            ? "rounded-br-md bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                            : isSystem
                            ? "border border-slate-700 bg-slate-900 text-slate-400"
                            : "rounded-bl-md border border-slate-800 bg-slate-900 text-slate-200"
                        }`}
                      >
                        <p className="whitespace-pre-wrap break-words leading-6">
                          {
                            message.content
                          }
                        </p>

                        {message.timestamp &&
                          isHydrated && (
                            <div
                              className={`mt-1 text-[10px] ${
                                isUser
                                  ? "text-blue-100"
                                  : "text-slate-500"
                              }`}
                            >
                              {formatMessageTime(
                                message.timestamp
                              )}
                            </div>
                          )}
                      </div>
                    </div>
                  );
                }
              )}

              {isThinking && (
                <ThinkingStatus />
              )}

              <div
                ref={
                  messagesEndRef
                }
              />
            </div>

            {/* Approval */}
            {pendingAction && (
              <div className="shrink-0 border-t border-slate-800 bg-slate-950 p-4">
                <ActionApproval
                  action={
                    pendingAction
                  }
                  onApprove={() =>
                    void handleApproval(
                      true
                    )
                  }
                  onReject={() =>
                    void handleApproval(
                      false
                    )
                  }
                />
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="shrink-0 border-t border-red-900/40 bg-red-950/20 px-4 py-2 text-xs text-red-400">
                {error}
              </div>
            )}

            {/* Selected image */}
            {selectedImage && (
              <div className="shrink-0 border-t border-slate-800 bg-slate-950 px-4 pt-3">
                <div className="relative w-fit overflow-hidden rounded-xl border border-slate-700 bg-slate-900">
                  <img
                    src={selectedImage}
                    alt="Selected attachment"
                    className="max-h-32 max-w-[220px] object-cover"
                  />

                  <button
                    type="button"
                    onClick={
                      removeSelectedImage
                    }
                    className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-sm text-white transition hover:bg-red-600"
                    aria-label="Remove image"
                  >
                    ×
                  </button>

                  <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 text-[10px] text-slate-200">
                    {selectedImageName}
                  </div>
                </div>
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={
                handleSubmit
              }
              className="shrink-0 border-t border-slate-800 bg-slate-950 p-4"
            >
              <input
                ref={
                  imageInputRef
                }
                type="file"
                accept="image/*"
                onChange={
                  handleImageSelected
                }
                className="hidden"
              />

              <div className="flex items-end gap-2 rounded-2xl border border-slate-700 bg-slate-900 p-2 transition focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500/30">
                {/* Image */}
                {showImage && (
                  <button
                    type="button"
                    onClick={
                      handleImageClick
                    }
                    disabled={
                      isThinking
                    }
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-700 bg-slate-800 text-lg text-slate-300 transition hover:border-blue-500 hover:bg-blue-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                    aria-label="Upload image"
                    title="Upload image"
                  >
                    🖼
                  </button>
                )}

                {/* Camera */}
                {showCamera && (
                  <button
                    type="button"
                    onClick={
                      handleCameraOpen
                    }
                    disabled={
                      isThinking
                    }
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-700 bg-slate-800 text-lg text-slate-300 transition hover:border-blue-500 hover:bg-blue-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                    aria-label="Open camera"
                    title="Open camera"
                  >
                    📷
                  </button>
                )}

                {/* Text */}
                <textarea
                  ref={
                    textareaRef
                  }
                  value={input}
                  onChange={(event) =>
                    setInput(
                      event.target
                        .value
                    )
                  }
                  onKeyDown={
                    handleKeyDown
                  }
                  placeholder={
                    placeholder
                  }
                  rows={1}
                  disabled={
                    isThinking
                  }
                  className="max-h-32 min-h-[42px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-slate-500 disabled:opacity-50"
                />

                {/* Voice */}
                {showVoice && (
                  <VoiceButton
                    disabled={
                      isThinking
                    }
                    onTranscript={
                      handleVoiceTranscript
                    }
                  />
                )}

                {/* Send */}
                <button
                  type="submit"
                  disabled={
                    (!input.trim() &&
                      !selectedImage) ||
                    isThinking
                  }
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-lg font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Send message"
                >
                  ↑
                </button>
              </div>

              <p className="mt-2 px-1 text-[10px] text-slate-500">
                Enter to send · Shift +
                Enter for a new line ·
                🖼 Image · 📷 Camera · 🎙
                Voice
              </p>
            </form>
          </div>

          {/* Activity */}
          {showActivity && (
            <aside className="hidden w-72 shrink-0 overflow-hidden border-l border-slate-800 bg-slate-950 lg:flex lg:flex-col">
              <ActivityStream
                activities={
                  activities
                }
              />
            </aside>
          )}
        </div>
      </section>

      {/* Camera modal */}
      {isCameraOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
              <div>
                <h3 className="font-semibold text-white">
                  AIOS Vision
                </h3>

                <p className="mt-1 text-xs text-slate-400">
                  Camera and vision interface
                </p>
              </div>

              <button
                type="button"
                onClick={
                  handleCameraClose
                }
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-lg text-slate-300 transition hover:border-red-500 hover:bg-red-600 hover:text-white"
                aria-label="Close camera"
              >
                ×
              </button>
            </div>

            <div className="p-5">
              <CameraView
                autoStart
                facingMode="user"
                muted
                mirrored
                showControls
                showStatus
                onError={(cameraError) => {
                  const message =
                    cameraError instanceof Error
                      ? cameraError.message
                      : "Unable to access the camera.";

                  setError(message);

                  addActivity(
                    "error",
                    "Camera error",
                    message
                  );
                }}
              />
            </div>

            <div className="flex justify-end border-t border-slate-800 px-5 py-4">
              <button
                type="button"
                onClick={
                  handleCameraClose
                }
                className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500"
              >
                Close Camera
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
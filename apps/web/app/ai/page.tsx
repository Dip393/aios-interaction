"use client";

import AIChat from "@/components/ai/AIChat";
import VisionPanel from "@/components/vision/VisionPanel";

export default function AIPage() {
  return (
    <main className="min-h-screen bg-[#070a12] text-[#edf3ff]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col px-4 py-4 sm:px-6 lg:px-8">

        {/* Header */}
        <header className="mb-4 flex items-center justify-between border-b border-[#263249] pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5b8cff]">
              AIOS
            </p>

            <h1 className="mt-1 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              AI Assistant
            </h1>

            <p className="mt-1 text-sm text-[#91a0b8]">
              Communicate with AIOS using natural language, voice,
              vision, and intelligent actions.
            </p>
          </div>

          <div className="hidden items-center gap-2 text-xs text-[#91a0b8] sm:flex">
            <span className="h-2 w-2 rounded-full bg-[#43d19e] shadow-[0_0_12px_#43d19e]" />
            AIOS Ready
          </div>
        </header>

        {/* AI Chat */}
        <section className="mb-6 min-h-0">
          <AIChat
            sessionId="aios-web-session"
            showVoice
            showActivity
            className="min-h-[500px]"
          />
        </section>

        {/* Vision / Hands-Free Control */}
        <section className="min-h-0">
          <VisionPanel
            autoStart={true}
            className="min-h-[600px]"
          />
        </section>

      </div>
    </main>
  );
}
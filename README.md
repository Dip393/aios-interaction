# AIOS Runtime — Free-First Intent-Driven AIOS MVP

AIOS Runtime is a **local-first, intent-driven computing environment**. It is not an MS Word clone or a traditional app launcher. A user describes a task, the AIOS planner turns it into a structured plan, a dynamic workspace is rendered, task state is persisted, memory/events can be recorded, reminders can be scheduled, and high-impact external actions require confirmation.

This repository is an intentionally safe, runnable MVP. It includes:

- Next.js 16 web UI with dynamic workspace rendering
- FastAPI Python runtime
- SQLite persistent state
- Optional local LLM through Ollama
- Deterministic planner fallback when Ollama is unavailable
- Task manager with active/paused/completed states
- Task snapshots and rollback
- Durable memory and activity/event records
- Local reminder scheduler
- SMTP email connector with explicit confirmation
- Writing/code/email/general workspace types
- Tauri 2 desktop shell configuration
- Clear separation between planning and execution

## 1. What this MVP does

Try these commands in the UI:

- `Email Rahul that we have a meeting tomorrow`
- `Create a Python project for CSV analysis`
- `I want to write a mythological story`
- `Remind me to study tomorrow`

For the email flow, AIOS creates a task and email workspace. After the user confirms the send action, the SMTP connector sends only when SMTP credentials are configured. After a successful send, the event extractor creates a meeting record and a reminder if the email plan contained a meeting. If no exact meeting time is available, the demo uses the default 09:00 local reminder window for tomorrow; change this policy before production use.

## 2. Architecture

```text
Voice / Text / Vision
        |
        v
   Input Layer
        |
        v
    AI Kernel
   /    |     \
Intent Memory Planner
        |
        v
 Agent / Tool Router
        |
        v
 Dynamic Environment Engine
        |
        v
 Execution + Verification
        |
   +----+----+
   |         |
 Memory   Rollback
   |
 Scheduler / Notifications
```

### Why this architecture

1. The LLM plans; deterministic tools execute.
2. UI is generated from safe component schemas instead of arbitrary LLM HTML.
3. Task state is durable so a task can be paused and resumed.
4. External side effects are explicitly confirmed.
5. Rollback is state-based. External actions such as sent email are **not** falsely treated as reversible.

## 3. Prerequisites

### Required

- Windows 10/11, macOS or Linux
- Node.js 22+ (Node 24 LTS is recommended for a new machine)
- npm 10+
- Python 3.11–3.13
- Git

### Optional but recommended for local AI

- Ollama
- A local model such as `gemma3:4b` or another model supported by your machine

### Optional for desktop packaging

- Rust stable
- Tauri prerequisites for your operating system

## 4. Install

### Clone / unzip

```bash
git clone <your-repository-url>
cd aios-project
```

### Python environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Node packages

```bash
npm install
cd apps/web
npm install
cd ../..
```

### Environment

Copy `.env.example` to `.env` and adjust values.

## 5. Optional Ollama setup

Install Ollama from the official site, start it, then pull a model:

```bash
ollama pull gemma3:4b
```

Make sure Ollama is serving locally. The API normally listens on:

```text
http://127.0.0.1:11434
```

If the model is too large for your machine, select a smaller compatible model in `.env`.

If Ollama is unavailable, AIOS automatically falls back to deterministic intent parsing for the included demo commands.

## 6. Run the web runtime

From the project root:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

The API runs at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## 7. Email connector

The email connector is deliberately **not configured by default**. This keeps the first run safe and free.

To connect SMTP, set:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-user
SMTP_PASSWORD=your-password
SMTP_FROM=your-address@example.com
SMTP_USE_TLS=true
```

The UI will still require an explicit send confirmation. AIOS does not pretend that an email was sent when SMTP is not configured.

For Gmail, use Google's supported SMTP/authentication approach for your account rather than storing your normal account password. A dedicated app password may be required depending on the account's security configuration.

## 8. Current free/local modules

- UI: local
- API: local
- SQLite: local
- Planner fallback: local
- Ollama: local
- Speech: not bundled into the first install because model size/device requirements vary
- Vision: connector-ready, not forced into the base install
- TTS: connector-ready
- Email: optional SMTP
- Calendar: local event/reminder store in this MVP

## 9. Voice module roadmap

The intended production pipeline is:

```text
Microphone
   -> faster-whisper
   -> AIOS command endpoint
   -> planner
   -> tool router
```

Keep speech recognition as a separate process/service so the desktop UI does not become dependent on a heavy ML runtime.

## 10. Vision / gesture roadmap

The intended pipeline is:

```text
Camera
  -> MediaPipe hand landmarks
  -> deterministic gesture classifier
  -> UI event
  -> AIOS intent/tool router
```

Do not send every camera frame to an LLM. Detect hand landmarks locally and emit compact semantic events such as `pointer_move`, `pinch`, `double_tap`, `swipe_up`.

## 11. Production safety rules

Before allowing autonomous tools, add a permission policy layer.

Suggested levels:

- Read-only: automatic
- Draft/create temporary workspace: automatic
- Modify local files: configurable
- Delete/overwrite: confirmation
- Send email/message: confirmation
- Financial or irreversible external actions: explicit confirmation every time

Rollback only guarantees state restoration for operations that are actually reversible. A sent email, external API mutation or physical-world action cannot be magically undone.

## 12. Test checklist

1. Start API.
2. Start web UI.
3. Enter `Create a Python project for CSV analysis`.
4. Confirm a code workspace appears.
5. Enter `I want to write a mythological story`.
6. Confirm a writing workspace appears.
7. Enter `Email Rahul that we have a meeting tomorrow`.
8. Confirm email workspace appears.
9. Click Review & Send.
10. Verify confirmation dialog appears.
11. Without SMTP, confirm that nothing is actually sent.
12. With SMTP configured, send a test email to your own address.
13. Check the Reminders panel after successful send.
14. Click Rollback on a task and verify its state changes back one snapshot.

## 13. Build

Web build:

```bash
npm run build
```

Type check:

```bash
npm run check
```

Desktop development requires Rust + Tauri prerequisites:

```bash
npm run desktop:dev
```

Desktop package:

```bash
npm run desktop:build
```

## 14. Important limitation of this repository

This is a **complete runnable MVP foundation**, not a claim that a free local application can safely replace every desktop application or every cloud API on day one. Production-grade autonomous coding, arbitrary OS control, WhatsApp automation, Gmail OAuth, sandboxed code execution, browser control, encrypted secrets, multimodal streaming and robust Windows accessibility integration should be added as separate audited connectors.

That separation is intentional: it keeps the core runtime stable and prevents an LLM from receiving unrestricted access to the user's machine.

## 15. Recommended next modules

1. Gmail OAuth connector
2. Google Calendar OAuth connector
3. Browser automation connector
4. Sandboxed Python/Node execution using containers or OS-level sandboxing
5. faster-whisper service
6. Piper TTS service
7. MediaPipe gesture service
8. Windows native notification service
9. encrypted credential vault
10. semantic vector memory
11. full event extraction with exact date/time parsing
12. agent graph with retry/verification nodes
13. application-independent accessibility layer

## License

Use this repository as the starting point for your AIOS project. Add your own license before public distribution.


## Official downloads

- Node.js: https://nodejs.org/en/download/
- Python: https://www.python.org/downloads/windows/
- Ollama: https://ollama.com/download
- Tauri prerequisites: https://tauri.app/start/prerequisites/
- Rust: https://www.rust-lang.org/tools/install

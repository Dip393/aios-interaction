# AIOS Runtime — Implementation Status

## Implemented in this MVP

- [x] Next.js UI
- [x] FastAPI runtime
- [x] SQLite persistence
- [x] Intent planner with Ollama + deterministic fallback
- [x] Dynamic workspace types: general, writing, email, code, reminder
- [x] Persistent tasks
- [x] Paused/resumable task state model
- [x] Task snapshots
- [x] Rollback of local task state
- [x] Durable memories
- [x] Event records
- [x] Reminder scheduler
- [x] External-action confirmation UI
- [x] SMTP connector
- [x] Activity/action ledger
- [x] Tauri 2 desktop shell configuration
- [x] Windows setup guide
- [x] README and architecture documentation

## Intentionally separate next modules

- [ ] Full Gmail OAuth connector
- [ ] Official calendar OAuth connector
- [ ] Official messaging connector
- [ ] Browser automation connector
- [ ] OS accessibility/native-control connector
- [ ] faster-whisper streaming service
- [ ] Piper TTS service
- [ ] MediaPipe gesture service
- [ ] Sandboxed code execution service
- [ ] Encrypted OS credential vault
- [ ] Production vector database
- [ ] Multi-agent graph with retries and verification nodes

These are not hidden behind fake implementations. The base runtime is designed so they can be plugged in without changing the core task/memory/rollback model.

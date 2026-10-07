'use client';

import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import Workspace from '../components/Workspace';

type Task = {
  id: string;
  title: string;
  kind?: string;
  status?: string;
  state_json?: Record<string, any>;
  state?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
};

type Memory = {
  id: number | string;
  category?: string;
  content?: string;
  importance?: number;
  created_at?: string;
};

type Reminder = {
  id: number | string;
  title: string;
  due_at?: string;
  status?: string;
};

type EmailDraft = {
  to?: string;
  subject?: string;
  body?: string;
  [key: string]: any;
};

export default function Home() {
  const [cmd, setCmd] = useState('');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [active, setActive] = useState<Task | null>(null);

  const [busy, setBusy] = useState(false);
  const [modal, setModal] = useState<EmailDraft | null>(null);
  const [notice, setNotice] = useState('');

  // -------------------------------------------------------------------------
  // Refresh dashboard data
  // -------------------------------------------------------------------------

  const refresh = async () => {
    try {
      const [taskResponse, memoryResponse, reminderResponse] =
        await Promise.all([
          api<any>('/api/tasks'),
          api<any>('/api/memory/recent?limit=50'),
          api<any>('/api/reminders'),
        ]);

      setTasks(
        Array.isArray(taskResponse)
          ? taskResponse
          : taskResponse?.tasks ?? [],
      );

      setMemories(
        Array.isArray(memoryResponse)
          ? memoryResponse
          : memoryResponse?.memories ??
              memoryResponse?.items ??
              [],
      );

      setReminders(
        Array.isArray(reminderResponse)
          ? reminderResponse
          : reminderResponse?.reminders ?? [],
      );
    } catch (error: any) {
      setNotice(
        error?.message ||
          'API unavailable. Start the backend on port 8000.',
      );
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  // -------------------------------------------------------------------------
  // Execute AIOS command
  // -------------------------------------------------------------------------

  async function run() {
    const input = cmd.trim();

    if (!input || busy) {
      return;
    }

    setBusy(true);
    setNotice('');

    try {
      const response = await api<any>(
        '/api/command',
        {
          method: 'POST',
          body: JSON.stringify({
            text: input,
          }),
        },
      );

      const task =
        response?.task ??
        response?.data?.task ??
        null;

      if (task) {
        setActive(task);
      }

      setCmd('');

      if (response?.message) {
        setNotice(response.message);
      } else if (response?.result?.message) {
        setNotice(response.result.message);
      }

      await refresh();
    } catch (error: any) {
      setNotice(
        error?.message ||
          'Unable to process the command.',
      );
    } finally {
      setBusy(false);
    }
  }

  // -------------------------------------------------------------------------
  // Rollback
  // -------------------------------------------------------------------------

  async function rollbackTask() {
    if (!active) {
      return;
    }

    setBusy(true);
    setNotice('');

    try {
      /*
       * Task rollback is now handled by the dedicated rollback layer.
       *
       * We first create/use a rollback snapshot for the current task and
       * then restore it through the rollback API.
       */

      const snapshotResponse = await api<any>(
        '/api/rollback/snapshot',
        {
          method: 'POST',
          body: JSON.stringify({
            task_id: active.id,
            name: `Task rollback: ${active.title}`,
            state:
              active.state_json ??
              active.state ??
              {},
          }),
        },
      );

      const snapshotId =
        snapshotResponse?.snapshot?.id ??
        snapshotResponse?.id;

      if (!snapshotId) {
        setNotice(
          'Rollback snapshot could not be created.',
        );
        return;
      }

      const restored = await api<any>(
        `/api/rollback/snapshots/${snapshotId}/restore`,
        {
          method: 'POST',
          body: JSON.stringify({
            task_id: active.id,
          }),
        },
      );

      if (
        restored?.success === false
      ) {
        setNotice(
          restored?.message ||
            'Rollback failed.',
        );
        return;
      }

      setNotice(
        'Task rollback completed.',
      );

      await refresh();

      const updatedTask = await api<any>(
        `/api/tasks/${encodeURIComponent(active.id)}`,
      );

      setActive(
        updatedTask?.task ??
          updatedTask ??
          active,
      );
    } catch (error: any) {
      /*
       * The dedicated rollback layer may evolve independently from the
       * legacy task API. Keep the UI graceful if rollback is unavailable.
       */
      setNotice(
        error?.message ||
          'Rollback is currently unavailable.',
      );
    } finally {
      setBusy(false);
    }
  }

  // -------------------------------------------------------------------------
  // Email draft
  // -------------------------------------------------------------------------

  function sendEmail(data: EmailDraft) {
    setModal(data);
  }

  function closeEmailModal() {
    setModal(null);
  }

  async function confirmEmail() {
    if (!modal) {
      return;
    }

    const recipient =
      modal.to?.trim() ||
      window.prompt(
        'Enter recipient email:',
      )?.trim() ||
      '';

    if (!recipient) {
      return;
    }

    setBusy(true);
    setNotice('');

    try {
      /*
       * External email sending should go through the AIOS agent/policy
       * pipeline rather than bypassing confirmation with a direct legacy
       * /api/email endpoint.
       */

      const response = await api<any>(
        '/api/agents/email/execute',
        {
          method: 'POST',
          body: JSON.stringify({
            action: 'send_email',
            parameters: {
              to: recipient,
              subject:
                modal.subject || '',
              body:
                modal.body || '',
            },
            confirm: true,
            task_id: active?.id ?? null,
          }),
        },
      );

      const success =
        response?.success ??
        response?.sent ??
        false;

      setNotice(
        response?.message ||
          (success
            ? 'Email sent successfully.'
            : 'Email request processed.'),
      );

      setModal(null);

      await refresh();
    } catch (error: any) {
      setNotice(
        error?.message ||
          'Unable to send email.',
      );
    } finally {
      setBusy(false);
    }
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function getTaskState(task: Task) {
    return (
      task.state_json ??
      task.state ??
      {}
    );
  }

  function getEnvironment(task: Task) {
    const state = getTaskState(task);

    return (
      state?.plan?.environment ||
      state?.environment ||
      task.kind ||
      'general'
    );
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          AI<span>OS</span> RUNTIME
        </div>

        <div className="status">
          <span className="dot" />
          Local-first ·{' '}
          {busy ? 'thinking…' : 'ready'}
        </div>
      </header>

      <aside className="side">
        <button className="navbtn active">
          ⌂ Home
        </button>

        <button className="navbtn">
          ◫ Workspaces
        </button>

        <button className="navbtn">
          ◷ Tasks &amp; Reminders
        </button>

        <button className="navbtn">
          ◌ Memory
        </button>

        <button className="navbtn">
          ↶ Rollback
        </button>

        <div
          style={{ marginTop: 30 }}
          className="muted"
        >
          AIOS runtime
          <br />
          Voice, vision and external connectors
          are modular capabilities.
        </div>
      </aside>

      <main className="main">
        <div>
          {/* --------------------------------------------------------------- */}
          {/* Hero / Command area */}
          {/* --------------------------------------------------------------- */}

          <section className="hero">
            <div className="eyebrow">
              Intent-driven computing
            </div>

            <h1>
              Tell AIOS what you want.
            </h1>

            <p>
              AIOS turns a natural-language request
              into a plan, a focused environment,
              persistent task state and verifiable
              actions. It does not require you to
              think in terms of traditional
              applications.
            </p>

            <div className="command">
              <input
                value={cmd}
                onChange={(event) =>
                  setCmd(event.target.value)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === 'Enter'
                  ) {
                    void run();
                  }
                }}
                placeholder="Try: Email Rahul that we have a meeting tomorrow"
                disabled={busy}
              />

              <button
                className="primary"
                onClick={() => void run()}
                disabled={
                  busy ||
                  !cmd.trim()
                }
              >
                {busy
                  ? 'Thinking…'
                  : 'Run'}
              </button>
            </div>

            {notice && (
              <div className="suggestion">
                {notice}
              </div>
            )}
          </section>

          {/* --------------------------------------------------------------- */}
          {/* Dynamic environment */}
          {/* --------------------------------------------------------------- */}

          {active && (
            <Workspace
              environment={getEnvironment(
                active,
              )}
              task={active}
              onEmail={sendEmail}
            />
          )}

          {/* --------------------------------------------------------------- */}
          {/* Dashboard cards */}
          {/* --------------------------------------------------------------- */}

          <div className="grid">
            <div className="card">
              <h3>Active tasks</h3>

              <div className="list">
                {tasks
                  .slice(0, 5)
                  .map((task) => (
                    <button
                      key={task.id}
                      className="item"
                      onClick={() =>
                        setActive(task)
                      }
                      style={{
                        textAlign: 'left',
                        color: 'inherit',
                      }}
                    >
                      <strong>
                        {task.title}
                      </strong>

                      <small>
                        {task.status ||
                          'unknown'}
                        {' · '}
                        {task.kind ||
                          'general'}
                      </small>
                    </button>
                  ))}

                {!tasks.length && (
                  <div className="muted">
                    No tasks yet.
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <h3>
                Upcoming reminders
              </h3>

              <div className="list">
                {reminders
                  .slice(0, 5)
                  .map((reminder) => (
                    <div
                      className="item"
                      key={reminder.id}
                    >
                      <strong>
                        {reminder.title}
                      </strong>

                      <small>
                        {reminder.due_at ||
                          'No due time'}
                        {' · '}
                        {reminder.status ||
                          'pending'}
                      </small>
                    </div>
                  ))}

                {!reminders.length && (
                  <div className="muted">
                    No reminders yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* Right side panel */}
        {/* ----------------------------------------------------------------- */}

        <aside className="sidepanel">
          <div className="card">
            <h3>
              Current task
            </h3>

            {active ? (
              <>
                <div className="muted">
                  {active.title}
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: 8,
                    marginTop: 12,
                  }}
                >
                  <button
                    className="ghost"
                    onClick={() =>
                      void rollbackTask()
                    }
                    disabled={busy}
                  >
                    ↶ Rollback
                  </button>

                  <button
                    className="ghost"
                    onClick={() => {
                      setActive(null);
                      void refresh();
                    }}
                  >
                    Close
                  </button>
                </div>
              </>
            ) : (
              <div className="muted">
                Run a command to create a task.
                Tasks can be paused, resumed,
                completed and rolled back.
              </div>
            )}
          </div>

          <div className="card">
            <h3>
              Memory
            </h3>

            <div className="list">
              {memories
                .slice(0, 6)
                .map((memory) => (
                  <div
                    className="item"
                    key={memory.id}
                  >
                    <strong>
                      {memory.category ||
                        'memory'}
                    </strong>

                    <small>
                      {memory.content ||
                        'No content'}
                    </small>
                  </div>
                ))}

              {!memories.length && (
                <div className="muted">
                  No durable memories yet.
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h3>
              Architecture
            </h3>

            <div className="muted">
              Input → AI Kernel → Intent →
              Planner → Policy → Agents /
              Connectors → Dynamic Environment
              → Execution → Verify →
              Memory / Rollback
            </div>
          </div>
        </aside>
      </main>

      {/* ------------------------------------------------------------------- */}
      {/* External action confirmation */}
      {/* ------------------------------------------------------------------- */}

      {modal && (
        <div className="modal">
          <div className="modalbox">
            <h3>
              Confirm external action
            </h3>

            <p className="muted">
              AIOS is ready to send this
              email. Sending is an external
              side effect and cannot be
              automatically rolled back.
            </p>

            <div className="item">
              <strong>
                {modal.subject ||
                  'No subject'}
              </strong>

              <small>
                To:{' '}
                {modal.to ||
                  'recipient required'}
              </small>

              <div
                style={{
                  marginTop: 10,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {modal.body ||
                  'No message body.'}
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent:
                  'flex-end',
                gap: 8,
                marginTop: 16,
              }}
            >
              <button
                className="ghost"
                onClick={
                  closeEmailModal
                }
                disabled={busy}
              >
                Cancel
              </button>

              <button
                className="primary"
                onClick={() =>
                  void confirmEmail()
                }
                disabled={busy}
              >
                {busy
                  ? 'Sending…'
                  : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
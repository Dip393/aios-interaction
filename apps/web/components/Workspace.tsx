'use client';

import { useEffect, useMemo, useState } from 'react';

type WorkspaceTask = {
  id?: string;
  title?: string;
  state_json?: {
    input?: string;
    plan?: {
      entities?: Record<string, any>;
      [key: string]: any;
    };
    [key: string]: any;
  };
  [key: string]: any;
};

type EmailData = {
  to: string;
  subject: string;
  body: string;
};

type Props = {
  environment: string;
  task: WorkspaceTask | null | undefined;
  onEmail: (data: EmailData) => void;
};

const EMAIL_SUGGESTION =
  'Hi, just a reminder that we have our meeting tomorrow.';

export default function Workspace({
  environment,
  task,
  onEmail,
}: Props) {
  const [text, setText] = useState('');
  const [subject, setSubject] = useState('');

  const plan = task?.state_json?.plan;
  const entities = plan?.entities ?? {};

  const taskInput = task?.state_json?.input ?? '';

  useEffect(() => {
    setText(
      entities.body ??
        task?.state_json?.body ??
        taskInput ??
        '',
    );

    setSubject(
      entities.subject ??
        'Meeting',
    );
  }, [
    task?.id,
    taskInput,
    entities.body,
    entities.subject,
    task?.state_json?.body,
  ]);

  const environmentType = useMemo(
    () => environment?.toLowerCase().trim(),
    [environment],
  );

  /* ---------------------------------------------------------------------- */
  /* Email Workspace                                                        */
  /* ---------------------------------------------------------------------- */

  if (
    environmentType === 'email' ||
    environmentType === 'mail'
  ) {
    const recipient =
      entities.recipient_email ??
      entities.email ??
      '';

    const recipientName =
      entities.recipient_name ??
      '';

    const recipientDisplay =
      recipientName || recipient;

    const handleInsertSuggestion = () => {
      setText((current) => {
        if (!current.trim()) {
          return EMAIL_SUGGESTION;
        }

        return `${current.trim()}\n\n${EMAIL_SUGGESTION}`;
      });
    };

    const handleReviewAndSend = () => {
      onEmail({
        to: recipient,
        subject: subject.trim() || 'Meeting Tomorrow',
        body: text.trim(),
      });
    };

    return (
      <section className="workspace card">
        <div className="workspaceHeader">
          <div>
            <h3>✉ Email Workspace</h3>

            {recipientDisplay && (
              <div className="muted">
                {recipientDisplay}
              </div>
            )}
          </div>

          <span className="pill">
            AI assisted
          </span>
        </div>

        <input
          value={recipientDisplay}
          readOnly
          placeholder="Recipient"
          aria-label="Recipient"
          style={{
            width: '100%',
            padding: 12,
            background: '#080c15',
            border: '1px solid #263249',
            borderRadius: 9,
            color: '#fff',
            marginBottom: 9,
          }}
        />

        <input
          value={subject}
          onChange={(event) =>
            setSubject(event.target.value)
          }
          placeholder="Subject"
          aria-label="Email subject"
          style={{
            width: '100%',
            padding: 12,
            background: '#080c15',
            border: '1px solid #263249',
            borderRadius: 9,
            color: '#fff',
            marginBottom: 9,
          }}
        />

        <textarea
          value={text}
          onChange={(event) =>
            setText(event.target.value)
          }
          className="editor"
          aria-label="Email body"
          placeholder="Write your email..."
          style={{
            width: '100%',
            minHeight: 230,
          }}
        />

        <div className="suggestion">
          <strong>AI suggestion</strong>
          <div style={{ marginTop: 5 }}>
            “{EMAIL_SUGGESTION}”
          </div>
        </div>

        <div
          style={{
            marginTop: 12,
            display: 'flex',
            gap: 8,
            flexWrap: 'wrap',
          }}
        >
          <button
            type="button"
            className="ghost"
            onClick={handleInsertSuggestion}
          >
            Insert suggestion
          </button>

          <button
            type="button"
            className="primary"
            onClick={handleReviewAndSend}
            disabled={!recipient || !text.trim()}
          >
            Review & Send
          </button>
        </div>
      </section>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Coding Workspace                                                       */
  /* ---------------------------------------------------------------------- */

  if (
    environmentType === 'code' ||
    environmentType === 'coding'
  ) {
    const request =
      entities.request ??
      taskInput ??
      'No coding request provided.';

    const generatedCode = [
      '# AIOS generated coding workspace',
      `# Request: ${request}`,
      '',
      'def main():',
      '    print("Workspace ready")',
      '',
      '',
      'if __name__ == "__main__":',
      '    main()',
    ].join('\n');

    return (
      <section className="workspace card">
        <div className="workspaceHeader">
          <div>
            <h3>⌘ Coding Workspace</h3>

            <div className="muted">
              {request}
            </div>
          </div>

          <span className="pill">
            Sandbox-ready
          </span>
        </div>

        <pre
          className="editor"
          style={{
            margin: 0,
            overflowX: 'auto',
          }}
        >
          {generatedCode}
        </pre>

        <div className="suggestion">
          <strong>Execution safety</strong>
          <div style={{ marginTop: 5 }}>
            Execution is intentionally sandboxed.
            Add a container/runtime connector before
            allowing arbitrary code execution.
          </div>
        </div>
      </section>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Writing Workspace                                                      */
  /* ---------------------------------------------------------------------- */

  if (
    environmentType === 'writing' ||
    environmentType === 'document'
  ) {
    return (
      <section className="workspace card">
        <div className="workspaceHeader">
          <div>
            <h3>
              ✎ {task?.title || 'Writing Workspace'}
            </h3>

            <div className="muted">
              AI-assisted writing environment
            </div>
          </div>

          <span className="pill">
            {environmentType}
          </span>
        </div>

        <textarea
          className="editor"
          value={text}
          onChange={(event) =>
            setText(event.target.value)
          }
          placeholder="Start writing..."
          style={{
            width: '100%',
            minHeight: 300,
          }}
        />

        <div className="suggestion">
          AIOS keeps this document state so you can
          pause the task and return to it later.
        </div>
      </section>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Calendar Workspace                                                     */
  /* ---------------------------------------------------------------------- */

  if (environmentType === 'calendar') {
    return (
      <section className="workspace card">
        <div className="workspaceHeader">
          <div>
            <h3>◷ Calendar Workspace</h3>

            <div className="muted">
              Calendar planning environment
            </div>
          </div>

          <span className="pill">
            calendar
          </span>
        </div>

        <div className="editor">
          {text ||
            'No calendar event details have been generated yet.'}
        </div>

        <div className="suggestion">
          AIOS can prepare the event details before
          an external calendar action is performed.
        </div>
      </section>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Generic Workspace                                                      */
  /* ---------------------------------------------------------------------- */

  return (
    <section className="workspace card">
      <div className="workspaceHeader">
        <div>
          <h3>
            ✦ {task?.title || 'AIOS Workspace'}
          </h3>

          <div className="muted">
            Dynamic AIOS environment
          </div>
        </div>

        <span className="pill">
          {environment || 'general'}
        </span>
      </div>

      <div className="editor">
        {text ||
          'This environment is ready. AIOS will populate the workspace as the task progresses.'}
      </div>

      <div className="suggestion">
        AIOS keeps this task state so you can pause
        it and return later.
      </div>
    </section>
  );
}
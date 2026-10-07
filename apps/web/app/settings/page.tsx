"use client";

import { useEffect, useState } from "react";

type SettingsState = {
  voiceEnabled: boolean;
  visionEnabled: boolean;
  notificationsEnabled: boolean;
  autoApproveLowRisk: boolean;
  rememberConversations: boolean;
  compactMode: boolean;
};

const DEFAULT_SETTINGS: SettingsState = {
  voiceEnabled: true,
  visionEnabled: true,
  notificationsEnabled: true,
  autoApproveLowRisk: false,
  rememberConversations: true,
  compactMode: false,
};

const STORAGE_KEY = "aios-settings";

function SettingToggle({
  checked,
  onChange,
  title,
  description,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-center justify-between gap-6 py-4">
      <div className="min-w-0">
        <h3 className="text-sm font-medium text-slate-900">
          {title}
        </h3>
        <p className="mt-1 text-sm text-slate-500">
          {description}
        </p>
      </div>

      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          checked ? "bg-blue-600" : "bg-slate-300"
        }`}
      >
        <span
          className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow-sm transition ${
            checked ? "left-6" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] =
    useState<SettingsState>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);

      if (stored) {
        const parsed = JSON.parse(stored) as Partial<SettingsState>;

        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
        });
      }
    } catch {
      // Ignore invalid local settings.
    }
  }, []);

  const updateSetting = <K extends keyof SettingsState>(
    key: K,
    value: SettingsState[K]
  ) => {
    setSettings((current) => ({
      ...current,
      [key]: value,
    }));

    setSaved(false);
  };

  const saveSettings = () => {
    try {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(settings)
      );

      setSaved(true);

      window.setTimeout(() => {
        setSaved(false);
      }, 2500);
    } catch {
      setSaved(false);
    }
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
    window.localStorage.removeItem(STORAGE_KEY);
    setSaved(false);
  };

  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "/api";

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-8">
          <p className="text-sm font-medium text-blue-600">AIOS</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Settings
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Configure AIOS behaviour, interaction modes, and
            preferences.
          </p>
        </header>

        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
              <h2 className="font-semibold text-slate-900">
                AIOS Interaction
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Control how AIOS interacts with voice, vision, and
                conversations.
              </p>
            </div>

            <div className="divide-y divide-slate-100 px-5 sm:px-6">
              <SettingToggle
                title="Voice interaction"
                description="Enable voice input and voice-based interaction."
                checked={settings.voiceEnabled}
                onChange={(value) =>
                  updateSetting("voiceEnabled", value)
                }
              />

              <SettingToggle
                title="Vision interaction"
                description="Enable camera, hand tracking, and gesture interaction."
                checked={settings.visionEnabled}
                onChange={(value) =>
                  updateSetting("visionEnabled", value)
                }
              />

              <SettingToggle
                title="Conversation memory"
                description="Allow AIOS to retain supported conversation context."
                checked={settings.rememberConversations}
                onChange={(value) =>
                  updateSetting(
                    "rememberConversations",
                    value
                  )
                }
              />
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
              <h2 className="font-semibold text-slate-900">
                Safety & Actions
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Configure notifications and action approval behaviour.
              </p>
            </div>

            <div className="divide-y divide-slate-100 px-5 sm:px-6">
              <SettingToggle
                title="Notifications"
                description="Allow AIOS to show task, reminder, and action notifications."
                checked={settings.notificationsEnabled}
                onChange={(value) =>
                  updateSetting(
                    "notificationsEnabled",
                    value
                  )
                }
              />

              <SettingToggle
                title="Auto-approve low-risk actions"
                description="Allow low-risk actions to proceed without an additional approval prompt."
                checked={settings.autoApproveLowRisk}
                onChange={(value) =>
                  updateSetting("autoApproveLowRisk", value)
                }
              />
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
              <h2 className="font-semibold text-slate-900">
                Interface
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Adjust the AIOS web interface.
              </p>
            </div>

            <div className="divide-y divide-slate-100 px-5 sm:px-6">
              <SettingToggle
                title="Compact mode"
                description="Use tighter spacing in supported AIOS interfaces."
                checked={settings.compactMode}
                onChange={(value) =>
                  updateSetting("compactMode", value)
                }
              />
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="px-5 py-5 sm:px-6">
              <h2 className="font-semibold text-slate-900">
                API Configuration
              </h2>

              <div className="mt-4 rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  API Base URL
                </p>
                <p className="mt-2 break-all font-mono text-sm text-slate-700">
                  {apiBaseUrl}
                </p>
              </div>

              <p className="mt-3 text-xs text-slate-500">
                The API URL is controlled through the
                NEXT_PUBLIC_API_URL or NEXT_PUBLIC_API_BASE_URL
                environment variable.
              </p>
            </div>
          </section>

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={resetSettings}
              className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Reset to defaults
            </button>

            <div className="flex items-center gap-3">
              {saved && (
                <span className="text-sm font-medium text-emerald-600">
                  Settings saved
                </span>
              )}

              <button
                type="button"
                onClick={saveSettings}
                className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                Save settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
"use client";

import { useCallback, useEffect, useState } from "react";
import EnvironmentRenderer from "@/components/environments/EnvironmentRenderer";
import {
  environmentApi,
  Environment,
} from "@/lib/environment";

export default function EnvironmentsPage() {
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [selectedId, setSelectedId] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadEnvironments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await environmentApi.list();

      const data = Array.isArray(response)
        ? response
        : Array.isArray(
              (response as { environments?: Environment[] })
                .environments
            )
          ? (
              response as {
                environments: Environment[];
              }
            ).environments
          : [];

      setEnvironments(data);

      if (!selectedId && data.length > 0) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load environments."
      );
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    void loadEnvironments();
  }, [loadEnvironments]);

  const selectedEnvironment = environments.find(
    (environment) => environment.id === selectedId
  );

  const activateEnvironment = async (id: string) => {
    try {
      setError(null);
      await environmentApi.activate(id);
      await loadEnvironments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to activate environment."
      );
    }
  };

  const pauseEnvironment = async (id: string) => {
    try {
      setError(null);
      await environmentApi.pause(id);
      await loadEnvironments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to pause environment."
      );
    }
  };

  const completeEnvironment = async (id: string) => {
    try {
      setError(null);
      await environmentApi.complete(id);
      await loadEnvironments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to complete environment."
      );
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-600">AIOS</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Environments
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Dynamic workspaces created and managed by AIOS.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadEnvironments()}
            disabled={loading}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="mb-3 px-2">
              <h2 className="text-sm font-semibold text-slate-900">
                Workspaces
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                {environments.length} environment
                {environments.length === 1 ? "" : "s"}
              </p>
            </div>

            <div className="space-y-1">
              {environments.map((environment) => {
                const active = environment.id === selectedId;

                return (
                  <button
                    key={environment.id}
                    type="button"
                    onClick={() => setSelectedId(environment.id)}
                    className={`w-full rounded-xl px-3 py-3 text-left transition ${
                      active
                        ? "bg-blue-50 text-blue-700"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="truncate text-sm font-medium">
                        {environment.name}
                      </span>

                      <span
                        className={`h-2 w-2 shrink-0 rounded-full ${
                          environment.status === "active"
                            ? "bg-emerald-500"
                            : environment.status === "error"
                              ? "bg-red-500"
                              : "bg-slate-300"
                        }`}
                      />
                    </div>

                    <div className="mt-1 text-xs opacity-70">
                      {environment.type}
                    </div>
                  </button>
                );
              })}

              {!loading && environments.length === 0 && (
                <div className="rounded-xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                  No environments found.
                </div>
              )}
            </div>
          </aside>

          <section className="min-w-0">
            {selectedEnvironment ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-end gap-2">
                  {selectedEnvironment.status !== "active" && (
                    <button
                      type="button"
                      onClick={() =>
                        void activateEnvironment(
                          selectedEnvironment.id
                        )
                      }
                      className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
                    >
                      Activate
                    </button>
                  )}

                  {selectedEnvironment.status === "active" && (
                    <button
                      type="button"
                      onClick={() =>
                        void pauseEnvironment(
                          selectedEnvironment.id
                        )
                      }
                      className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Pause
                    </button>
                  )}

                  {selectedEnvironment.status !== "completed" && (
                    <button
                      type="button"
                      onClick={() =>
                        void completeEnvironment(
                          selectedEnvironment.id
                        )
                      }
                      className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Complete
                    </button>
                  )}
                </div>

                <EnvironmentRenderer
                  environment={selectedEnvironment}
                />
              </div>
            ) : (
              <div className="flex min-h-[500px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white">
                <div className="text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                    ◎
                  </div>
                  <h2 className="mt-4 font-semibold text-slate-900">
                    No environment selected
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Select an environment from the workspace list.
                  </p>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
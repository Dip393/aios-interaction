"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import MemoryPanel from "@/components/memory/MemoryPanel";
import {
  memoryApi,
  MemoryItem,
  MemoryStats,
} from "@/lib/memory";

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [stats, setStats] = useState<MemoryStats>({
    shortTerm: 0,
    working: 0,
    longTerm: 0,
    semantic: 0,
    total: 0,
  });
  const [selectedMemoryId, setSelectedMemoryId] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMemory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsResponse, recentResponse] = await Promise.all([
        memoryApi.stats(),
        memoryApi.recent(100),
      ]);

      setStats({
        shortTerm:
          Number(statsResponse.shortTerm ?? statsResponse.short_term ?? 0),
        working: Number(statsResponse.working ?? 0),
        longTerm: Number(
          statsResponse.longTerm ?? statsResponse.long_term ?? 0
        ),
        semantic: Number(statsResponse.semantic ?? 0),
        total: Number(statsResponse.total ?? 0),
      });

      const recent = Array.isArray(recentResponse)
        ? recentResponse
        : Array.isArray(
              (recentResponse as { items?: MemoryItem[] }).items
            )
          ? (recentResponse as { items: MemoryItem[] }).items
          : [];

      setMemories(recent);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load memory."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMemory();
  }, [loadMemory]);

  const handleSearch = useCallback(async (query: string) => {
    try {
      const response = await memoryApi.semanticSearch(query, 20);

      const results = Array.isArray(response)
        ? response
        : Array.isArray(
              (response as { results?: MemoryItem[] }).results
            )
          ? (response as { results: MemoryItem[] }).results
          : [];

      return results;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Memory search failed."
      );

      return [];
    }
  }, []);

  const handleForget = useCallback(async (memory: MemoryItem) => {
    if (!memory.id) {
      return;
    }

    try {
      await memoryApi.forget(memory.id);
      await loadMemory();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to forget memory."
      );
    }
  }, [loadMemory]);

  const visibleMemories = useMemo(() => memories, [memories]);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-600">AIOS</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Memory
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Explore recent, working, long-term, and semantic memories.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadMemory()}
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

        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <MemoryPanel
            memories={visibleMemories}
            stats={stats}
            selectedMemoryId={selectedMemoryId}
            onMemorySelect={(memory) => setSelectedMemoryId(memory.id)}
            onForget={(memory) => void handleForget(memory)}
            onSearch={handleSearch}
            onRefresh={() => void loadMemory()}
          />
        </section>
      </div>
    </main>
  );
}
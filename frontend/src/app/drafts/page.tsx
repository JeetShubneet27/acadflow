"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { apiFetch } from "@/lib/api";

type Draft = {
  id: number;
  version: number;
  original_filename: string;
  created_at: string;
};

type DraftLock = {
  id: number;
  draft_id: number;
  locked_by_id: number;
  status: string;
  locked_at: string;
  expires_at: string;
};

export default function DraftsPage() {
  const [projectId, setProjectId] = useState("");
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [draftLocks, setDraftLocks] = useState<Record<number, DraftLock | null>>(
    {},
  );
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleLoad = async () => {
    if (!projectId) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await apiFetch<Draft[]>(`/projects/${projectId}/drafts`);
      setDrafts(response);
      const lockResults = await Promise.allSettled(
        response.map((draft) => apiFetch<DraftLock>(`/drafts/${draft.id}/lock`)),
      );
      const lockMap: Record<number, DraftLock | null> = {};
      response.forEach((draft, index) => {
        const result = lockResults[index];
        lockMap[draft.id] = result.status === "fulfilled" ? result.value : null;
      });
      setDraftLocks(lockMap);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load drafts");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLock = async (draftId: number) => {
    try {
      const lock = await apiFetch<DraftLock>(`/drafts/${draftId}/lock`, {
        method: "POST",
      });
      setDraftLocks((prev) => ({ ...prev, [draftId]: lock }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to lock draft");
    }
  };

  const handleUnlock = async (draftId: number) => {
    try {
      const lock = await apiFetch<DraftLock>(`/drafts/${draftId}/lock`, {
        method: "DELETE",
      });
      setDraftLocks((prev) => ({ ...prev, [draftId]: lock }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to unlock draft");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Drafts</h1>
        <p className="text-sm text-slate-600">
          Review uploaded versions across your projects.
        </p>
      </div>

      <SectionCard title="Fetch project drafts">
        <div className="flex flex-wrap gap-3">
          <input
            type="number"
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
            placeholder="Project ID"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={handleLoad}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Load drafts
          </button>
        </div>
      </SectionCard>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <SectionCard title="Draft versions">
        {isLoading ? (
          <div className="text-sm text-slate-500">Loading drafts...</div>
        ) : drafts.length === 0 ? (
          <div className="text-sm text-slate-500">
            No drafts available for this project.
          </div>
        ) : (
          <ul className="space-y-2 text-sm text-slate-600">
            {drafts.map((draft) => {
              const lock = draftLocks[draft.id];
              const isLocked = lock?.status === "active";
              return (
                <li
                  key={draft.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-2"
                >
                  <div>
                    v{draft.version} • {draft.original_filename}
                    <div className="text-xs text-slate-400">
                      {isLocked
                        ? `Locked by user #${lock?.locked_by_id}`
                        : "No active lock"}
                    </div>
                  </div>
                  {isLocked ? (
                    <button
                      type="button"
                      onClick={() => handleUnlock(draft.id)}
                      className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700"
                    >
                      Release lock
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleLock(draft.id)}
                      className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white"
                    >
                      Lock draft
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}

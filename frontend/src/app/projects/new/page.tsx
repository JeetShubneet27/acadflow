"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiFetch<{ id: number }>("/projects", {
        method: "POST",
        body: JSON.stringify({
          title,
          abstract,
          visibility,
        }),
      });
      router.push(`/projects/${response.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">New project</h1>
        <p className="text-sm text-[var(--color-muted)]">
          Create a research workspace and invite collaborators.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">Title</label>
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="input"
            required
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">Abstract</label>
          <textarea
            value={abstract}
            onChange={(event) => setAbstract(event.target.value)}
            className="textarea min-h-[120px]"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">
            Visibility
          </label>
          <select
            value={visibility}
            onChange={(event) => setVisibility(event.target.value)}
            className="select"
          >
            <option value="private">Private</option>
            <option value="public">Public</option>
          </select>
        </div>
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary disabled:opacity-60"
        >
          {isSubmitting ? "Creating..." : "Create project"}
        </button>
      </form>
    </div>
  );
}

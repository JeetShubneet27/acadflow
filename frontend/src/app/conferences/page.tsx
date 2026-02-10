"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type ConferenceItem = {
  title: string;
  url: string;
  conference_date: string;
  submission_deadline: string;
  location?: string;
  source?: string;
};

export default function ConferencesPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<ConferenceItem[]>([]);
  const [keyword, setKeyword] = useState("research");
  const [query, setQuery] = useState("research");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (activeKeyword: string) => {
    if (!user) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const response = await apiFetch<{ items: ConferenceItem[] }>(
        `/conferences?keyword=${encodeURIComponent(activeKeyword)}`,
      );
      setItems(response.items || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load conferences");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load(query);
  }, [query, user]);

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!keyword.trim()) {
      return;
    }
    setQuery(keyword.trim());
  };

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Log in to browse upcoming conferences.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          Upcoming research conferences
        </h1>
        <p className="text-sm text-[var(--color-muted)]">
          Search open calls, submission deadlines, and conference dates.
        </p>
      </div>

      <SectionCard title="Search conferences">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            className="input flex-1 min-w-[240px]"
            placeholder="AI, biology, HCI, security..."
          />
          <button type="submit" className="btn btn-primary">
            Search
          </button>
        </form>
      </SectionCard>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <SectionCard title={`Results for “${query}”`}>
        {isLoading ? (
          <div className="text-sm text-[var(--color-muted)]">Loading conferences...</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-[var(--color-muted)]">
            No results. Try a different keyword.
          </div>
        ) : (
          <div className="space-y-4 text-sm text-[var(--color-muted)]">
            {items.map((item) => (
              <a
                key={`${item.url}-${item.title}`}
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-[var(--color-text)]"
              >
                <div className="font-semibold">{item.title}</div>
                <div className="mt-1 text-xs text-[var(--color-muted)]">
                  {item.source || "Source"}
                  {item.location ? ` • ${item.location}` : ""}
                </div>
                <div className="mt-3 grid gap-2 text-xs text-[var(--color-muted)] md:grid-cols-2">
                  <div>
                    <span className="font-semibold">Conference date:</span>{" "}
                    {item.conference_date}
                  </div>
                  <div>
                    <span className="font-semibold">Submission deadline:</span>{" "}
                    {item.submission_deadline}
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

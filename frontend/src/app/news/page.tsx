"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { apiFetch } from "@/lib/api";

type NewsItem = {
  title: string;
  url: string;
  published_at?: string;
  source?: string;
};

export default function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await apiFetch<{ items: NewsItem[] }>("/news/trending");
        setItems(response.items || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load news");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          Trending research news
        </h1>
        <p className="text-sm text-[var(--color-muted)]">
          Latest research updates curated from trusted science sources.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <SectionCard>
        {isLoading ? (
          <div className="text-sm text-[var(--color-muted)]">Loading news...</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-[var(--color-muted)]">
            No news available right now.
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <a
                key={`${item.url}-${item.title}`}
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm text-[var(--color-text)] hover:border-[var(--color-accent)]"
              >
                <div className="font-semibold">{item.title}</div>
                <div className="mt-1 text-xs text-[var(--color-muted)]">
                  {item.source || "Source"}{" "}
                  {item.published_at ? `• ${item.published_at}` : ""}
                </div>
              </a>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

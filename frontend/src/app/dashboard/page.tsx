"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Project = {
  id: number;
  title: string;
  visibility: string;
  created_at: string;
};

type PlagiarismJob = {
  id: number;
  project_id?: number | null;
  status: string;
  eta_hours: number;
  original_filename: string;
};

type Review = {
  id: number;
  project_id: number;
  status: string;
};

type NewsItem = {
  title: string;
  url: string;
  published_at?: string;
  source?: string;
};

type ConferenceItem = {
  title: string;
  url: string;
  conference_date: string;
  submission_deadline: string;
  location?: string;
  source?: string;
};

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<PlagiarismJob[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [conferences, setConferences] = useState<ConferenceItem[]>([]);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [conferenceError, setConferenceError] = useState<string | null>(null);
  const [conferenceWarning, setConferenceWarning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }
    const load = async () => {
      try {
        const [projectData, jobData] = await Promise.all([
          apiFetch<Project[]>("/projects"),
          apiFetch<PlagiarismJob[]>("/plagiarism/jobs"),
        ]);
        setProjects(projectData);
        setJobs(jobData);
        if (user.role === "faculty") {
          const reviewData = await apiFetch<Review[]>("/reviews/assigned");
          setReviews(reviewData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load dashboard");
      }
      const [newsResult, conferenceResult] = await Promise.allSettled([
        apiFetch<{ items: NewsItem[] }>("/news/trending"),
        apiFetch<{ items: ConferenceItem[]; warning?: string }>(
          "/conferences?keyword=research",
        ),
      ]);
      if (newsResult.status === "fulfilled") {
        setNews(newsResult.value.items.slice(0, 4));
        setNewsError(null);
      } else {
        setNewsError(
          newsResult.reason instanceof Error
            ? newsResult.reason.message
            : "Unable to load news",
        );
      }
      if (conferenceResult.status === "fulfilled") {
        setConferences(conferenceResult.value.items.slice(0, 4));
        setConferenceError(null);
        setConferenceWarning(conferenceResult.value.warning || null);
      } else {
        setConferenceError(
          conferenceResult.reason instanceof Error
            ? conferenceResult.reason.message
            : "Unable to load conferences",
        );
        setConferenceWarning(null);
      }
    };
    load();
  }, [user]);

  if (isLoading) {
    return <div className="text-sm text-[var(--color-muted)]">Loading session...</div>;
  }

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Please log in to view your dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-[var(--color-text)]">
          Welcome back, {user.full_name}
        </h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          Role: <span className="font-semibold">{user.role}</span>
        </p>
      </div>
      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      <div className="grid gap-6 md:grid-cols-3">
        <SectionCard
          title="Active projects"
          description="Projects you own or collaborate on."
        >
          <div className="text-3xl font-semibold text-[var(--color-text)]">
            {projects.length}
          </div>
        </SectionCard>
        <SectionCard
          title="Plagiarism jobs"
          description="Jobs awaiting review or completed."
        >
          <div className="text-3xl font-semibold text-[var(--color-text)]">
            {jobs.length}
          </div>
        </SectionCard>
        <SectionCard
          title="Assigned reviews"
          description="Your pending and submitted reviews."
        >
          <div className="text-3xl font-semibold text-[var(--color-text)]">
            {user.role === "faculty" ? reviews.length : "—"}
          </div>
        </SectionCard>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="Trending research news"
          description="Latest updates from leading research outlets."
        >
          {newsError ? (
            <div className="text-sm text-red-600">{newsError}</div>
          ) : news.length === 0 ? (
            <div className="text-sm text-[var(--color-muted)]">
              Loading news...
            </div>
          ) : (
            <div className="space-y-3 text-sm text-[var(--color-muted)]">
              {news.map((item) => (
                <a
                  key={item.url}
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]"
                >
                  <div className="font-medium">{item.title}</div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {item.source || "Source"}{" "}
                    {item.published_at ? `• ${item.published_at}` : ""}
                  </div>
                </a>
              ))}
            </div>
          )}
        </SectionCard>
        <SectionCard
          title="Upcoming conferences"
          description="Open calls and submission deadlines."
        >
          {conferenceError ? (
            <div className="text-sm text-red-600">{conferenceError}</div>
          ) : conferences.length === 0 ? (
            <div className="text-sm text-[var(--color-muted)]">
              {conferenceWarning || "Loading conferences..."}
            </div>
          ) : (
            <div className="space-y-3 text-sm text-[var(--color-muted)]">
              {conferences.map((item) => (
                <a
                  key={item.url}
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]"
                >
                  <div className="font-medium">{item.title}</div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {item.source || "Source"}
                    {item.location ? ` • ${item.location}` : ""}
                  </div>
                  <div className="mt-2 text-xs text-[var(--color-muted)]">
                    Deadline: {item.submission_deadline}
                  </div>
                </a>
              ))}
              {conferenceWarning && (
                <div className="text-xs text-amber-600">{conferenceWarning}</div>
              )}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

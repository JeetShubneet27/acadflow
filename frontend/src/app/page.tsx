"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

const audienceContent = {
  student: [
    "Organize thesis or paper projects with your co-authors.",
    "Write in shared Word or LaTeX workspaces with version history.",
    "Request Turnitin-backed plagiarism reports with payment tracking.",
    "Track review feedback and respond with updated drafts.",
  ],
  faculty: [
    "Oversee academic integrity with Turnitin-assisted reviews.",
    "Assign reviewers and monitor submissions across projects.",
    "Audit-ready activity logs for compliance and governance.",
    "Support students with clear status updates and approvals.",
  ],
};

export default function Home() {
  const [audience, setAudience] = useState<"student" | "faculty">("student");
  const [news, setNews] = useState<
    { title: string; url: string; published_at?: string; source?: string }[]
  >([]);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [conferences, setConferences] = useState<
    {
      title: string;
      url: string;
      conference_date: string;
      submission_deadline: string;
      location?: string;
      source?: string;
    }[]
  >([]);
  const [conferenceError, setConferenceError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await apiFetch<{ items: typeof news }>("/news/trending");
        setNews(response.items.slice(0, 4));
      } catch (err) {
        setNewsError(err instanceof Error ? err.message : "Unable to load news");
      }
      try {
        const response = await apiFetch<{ items: typeof conferences }>(
          "/conferences?keyword=research",
        );
        setConferences(response.items.slice(0, 4));
      } catch (err) {
        setConferenceError(
          err instanceof Error ? err.message : "Unable to load conferences",
        );
      }
    };
    load();
  }, []);

  return (
    <div className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-8">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[var(--color-muted)]">
            Research integrity, simplified
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-[var(--color-text)] md:text-5xl">
            AcadFlow is the collaborative workspace for academic research.
          </h1>
          <p className="text-lg text-[var(--color-muted)]">
            Our mission is to help universities, labs, and journals manage research
            projects with clarity, integrity, and accountability—from first draft to
            final Turnitin report.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href="/register" className="btn btn-primary">
            Start a workspace
          </a>
          <a href="/login" className="btn btn-secondary">
            Log in
          </a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            "Live Word + LaTeX collaboration with version history.",
            "Role-based access with faculty governance controls.",
            "Turnitin-backed plagiarism workflows and reporting.",
            "Secure reviewer assignment and structured feedback.",
          ].map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm text-[var(--color-muted)] shadow-sm"
            >
              {item}
            </div>
          ))}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-[var(--color-text)]">Our focus</h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            AcadFlow provides a single system for research collaboration, peer
            review, and plagiarism verification—without sacrificing academic rigor.
          </p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-[var(--color-text)]">
              Trending research news
            </h2>
            <a href="/news" className="text-xs text-[var(--color-muted)]">
              View all
            </a>
          </div>
          {newsError ? (
            <p className="mt-3 text-sm text-red-600">{newsError}</p>
          ) : news.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--color-muted)]">
              Loading updates...
            </p>
          ) : (
            <div className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
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
        </div>
        <div className="card">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-[var(--color-text)]">
              Upcoming conferences
            </h2>
            <a href="/conferences" className="text-xs text-[var(--color-muted)]">
              Search all
            </a>
          </div>
          {conferenceError ? (
            <p className="mt-3 text-sm text-red-600">{conferenceError}</p>
          ) : conferences.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--color-muted)]">
              Loading upcoming calls...
            </p>
          ) : (
            <div className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
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
            </div>
          )}
        </div>
      </div>
      <div className="space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-[var(--color-text)]">
            Choose your path
          </h2>
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={() => setAudience("student")}
              className={`btn btn-xs ${
                audience === "student" ? "btn-primary" : "btn-secondary"
              }`}
            >
              Students
            </button>
            <button
              type="button"
              onClick={() => setAudience("faculty")}
              className={`btn btn-xs ${
                audience === "faculty" ? "btn-primary" : "btn-secondary"
              }`}
            >
              Faculty
            </button>
          </div>
          <ul className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
            {audienceContent[audience].map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-[var(--color-text)]">
            Turnitin report delivery
          </h3>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            We run every plagiarism check through Turnitin and return verified
            reports directly to your workspace with full audit history.
          </p>
        </div>
        <div className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-accent)] p-6 text-sm text-[var(--color-on-primary)] shadow-sm">
          <h3 className="text-lg font-semibold">Ready to pilot AcadFlow?</h3>
          <p className="mt-2 text-[var(--color-on-primary)] opacity-90">
            Launch a workspace for your department or lab in minutes with secure
            role-based onboarding.
          </p>
        </div>
      </div>
    </div>
  );
}

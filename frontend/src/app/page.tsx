"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

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
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [audience, setAudience] = useState<"student" | "faculty">("student");

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

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

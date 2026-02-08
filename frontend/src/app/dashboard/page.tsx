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

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<PlagiarismJob[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
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
        if (user.role === "reviewer") {
          const reviewData = await apiFetch<Review[]>("/reviews/assigned");
          setReviews(reviewData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load dashboard");
      }
    };
    load();
  }, [user]);

  if (isLoading) {
    return <div className="text-sm text-slate-500">Loading session...</div>;
  }

  if (!user) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Please log in to view your dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">
          Welcome back, {user.full_name}
        </h1>
        <p className="mt-2 text-sm text-slate-600">
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
          <div className="text-3xl font-semibold text-slate-900">
            {projects.length}
          </div>
        </SectionCard>
        <SectionCard
          title="Plagiarism jobs"
          description="Jobs awaiting review or completed."
        >
          <div className="text-3xl font-semibold text-slate-900">
            {jobs.length}
          </div>
        </SectionCard>
        <SectionCard
          title="Assigned reviews"
          description="Your pending and submitted reviews."
        >
          <div className="text-3xl font-semibold text-slate-900">
            {user.role === "reviewer" ? reviews.length : "—"}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

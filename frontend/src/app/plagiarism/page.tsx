"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";

type Job = {
  id: number;
  project_id: number;
  status: string;
  eta_hours: number;
  original_filename: string;
  report_filename?: string;
};

export default function PlagiarismPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [projectId, setProjectId] = useState("");
  const [reportJobId, setReportJobId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch<Job[]>("/plagiarism/jobs");
      setJobs(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load jobs");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      load();
    } else {
      setIsLoading(false);
    }
  }, [user]);

  const handleRequest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("plagiarism") as HTMLInputElement;
    if (!fileInput.files || fileInput.files.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    try {
      await apiFetch(`/projects/${projectId}/plagiarism/jobs`, {
        method: "POST",
        body: formData,
      });
      form.reset();
      setProjectId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create job");
    }
  };

  const handleReportUpload = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("report") as HTMLInputElement;
    if (!fileInput.files || fileInput.files.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    try {
      await apiFetch(`/plagiarism/jobs/${reportJobId}/report`, {
        method: "POST",
        body: formData,
      });
      form.reset();
      setReportJobId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to upload report");
    }
  };

  const downloadReport = async (jobId: number, filename?: string) => {
    const baseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const token = getToken();
    if (!token) {
      setError("You must be logged in to download reports.");
      return;
    }
    try {
      const response = await fetch(
        `${baseUrl}/plagiarism/jobs/${jobId}/report`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!response.ok) {
        throw new Error("Unable to download report");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename || `plagiarism-report-${jobId}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to download report");
    }
  };

  if (!user) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Log in to manage plagiarism checks.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Plagiarism checks
        </h1>
        <p className="text-sm text-slate-600">
          Submit manuscripts for human-reviewed similarity checks.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <SectionCard
        title="Request a new plagiarism check"
        description="Upload a manuscript to queue a human review."
      >
        <form onSubmit={handleRequest} className="flex flex-wrap gap-3">
          <input
            type="number"
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
            placeholder="Project ID"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
            required
          />
          <input type="file" name="plagiarism" className="text-sm" required />
          <button
            type="submit"
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Submit
          </button>
        </form>
      </SectionCard>

      {user.role === "faculty" && (
        <SectionCard
          title="Upload plagiarism report"
          description="Faculty can attach the final Turnitin report."
        >
          <form onSubmit={handleReportUpload} className="flex flex-wrap gap-3">
            <input
              type="number"
              value={reportJobId}
              onChange={(event) => setReportJobId(event.target.value)}
              placeholder="Job ID"
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <input type="file" name="report" className="text-sm" required />
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Upload report
            </button>
          </form>
        </SectionCard>
      )}

      <SectionCard title="Recent plagiarism jobs">
        {isLoading ? (
          <div className="text-sm text-slate-500">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="text-sm text-slate-500">No jobs submitted yet.</div>
        ) : (
          <div className="space-y-3 text-sm text-slate-600">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 px-4 py-3"
              >
                <div>
                  Job #{job.id} • Project #{job.project_id} • {job.status}
                </div>
                {job.report_filename ? (
                  <button
                    type="button"
                    onClick={() => downloadReport(job.id, job.report_filename)}
                    className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700"
                  >
                    Download report
                  </button>
                ) : (
                  <span className="text-xs text-slate-400">
                    Report pending
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

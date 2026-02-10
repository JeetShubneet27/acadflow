"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatCurrency } from "@/lib/format";
import { loadRazorpay, openRazorpay } from "@/lib/razorpay";

type Job = {
  id: number;
  project_id?: number | null;
  status: string;
  eta_hours: number;
  original_filename: string;
  report_filename?: string;
  payment_status: string;
  amount_cents: number;
  currency: string;
};

type RazorpayOrder = {
  key_id: string;
  order_id: string;
  amount: number;
  currency: string;
  job_id: number;
};

export default function PlagiarismPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [projectId, setProjectId] = useState("");
  const [reportJobId, setReportJobId] = useState("");
  const [payingJobId, setPayingJobId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    if (!user) {
      return;
    }
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

  const handleProjectPayment = async (jobId: number) => {
    setPayingJobId(jobId);
    try {
      const loaded = await loadRazorpay();
      if (!loaded) {
        throw new Error("Unable to load payment gateway");
      }
      const order = await apiFetch<RazorpayOrder>(
        `/plagiarism/jobs/${jobId}/razorpay/order`,
        {
          method: "POST",
        },
      );
      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "AcadFlow",
        description: "Plagiarism check",
        order_id: order.order_id,
        prefill: {
          email: user?.email,
          name: user?.full_name,
        },
        handler: async (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) => {
          await apiFetch(`/plagiarism/jobs/${jobId}/razorpay/verify`, {
            method: "POST",
            body: JSON.stringify(response),
          });
          await load();
        },
        theme: { color: "#0f172a" },
      };
      openRazorpay(options);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setPayingJobId(null);
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          Plagiarism checks
        </h1>
        <p className="text-sm text-[var(--color-muted)]">
          Submit manuscripts for human-reviewed similarity checks.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!user && (
        <SectionCard
          title="Login required"
          description="Plagiarism checks are available after you sign in."
        >
          <p className="text-sm text-[var(--color-muted)]">
            Log in as a student or faculty member to submit manuscripts and track
            results.
          </p>
          <a href="/login" className="btn btn-primary mt-4">
            Go to login
          </a>
        </SectionCard>
      )}

      {user && (
        <SectionCard
          title="Project-based plagiarism check"
          description="Upload a manuscript tied to a project workspace."
        >
          <form onSubmit={handleRequest} className="flex flex-wrap gap-3">
            <input
              type="number"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
              placeholder="Project ID"
              className="input w-auto"
              required
            />
            <input type="file" name="plagiarism" className="text-sm" required />
            <button
              type="submit"
              className="btn btn-primary"
            >
              Submit
            </button>
          </form>
        </SectionCard>
      )}

      {user?.role === "faculty" && (
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
              className="input w-auto"
              required
            />
            <input type="file" name="report" className="text-sm" required />
            <button
              type="submit"
              className="btn btn-primary"
            >
              Upload report
            </button>
          </form>
        </SectionCard>
      )}

      {user && (
        <SectionCard title="Recent plagiarism jobs">
          {isLoading ? (
            <div className="text-sm text-[var(--color-muted)]">Loading jobs...</div>
          ) : jobs.length === 0 ? (
            <div className="text-sm text-[var(--color-muted)]">
              No jobs submitted yet.
            </div>
          ) : (
            <div className="space-y-3 text-sm text-[var(--color-muted)]">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] px-4 py-3"
                >
                  <div>
                    Job #{job.id} •{" "}
                    {job.project_id ? `Project #${job.project_id}` : "Direct"} •{" "}
                    {job.status}
                    <div className="text-xs text-[var(--color-muted)]">
                      Payment: {job.payment_status} •{" "}
                      {formatCurrency(job.amount_cents, job.currency)}
                    </div>
                  </div>
                  {job.report_filename ? (
                    <button
                      type="button"
                      onClick={() => downloadReport(job.id, job.report_filename)}
                      className="btn btn-secondary btn-xs"
                    >
                      Download report
                    </button>
                  ) : job.payment_status === "pending" ? (
                    <button
                      type="button"
                      onClick={() => handleProjectPayment(job.id)}
                      disabled={payingJobId === job.id}
                      className="btn btn-primary btn-xs disabled:opacity-60"
                    >
                      {payingJobId === job.id ? "Opening..." : "Pay now"}
                    </button>
                  ) : (
                    <span className="text-xs text-[var(--color-muted)]">
                      Report pending
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}

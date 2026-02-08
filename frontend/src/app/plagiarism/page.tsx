"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatCurrency } from "@/lib/format";

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

type PublicJobResponse = {
  id: number;
  access_token: string;
  status: string;
  eta_hours: number;
  amount_cents: number;
  currency: string;
};

type PublicJobStatus = {
  id: number;
  status: string;
  eta_hours: number;
  amount_cents: number;
  currency: string;
  payment_status: string;
  report_filename?: string;
  payment_submitted_at?: string;
  created_at: string;
  completed_at?: string;
};

type RazorpayOrder = {
  key_id: string;
  order_id: string;
  amount: number;
  currency: string;
  job_id: number;
};

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

export default function PlagiarismPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [projectId, setProjectId] = useState("");
  const [reportJobId, setReportJobId] = useState("");
  const [publicEmail, setPublicEmail] = useState("");
  const [publicName, setPublicName] = useState("");
  const [publicResponse, setPublicResponse] = useState<PublicJobResponse | null>(
    null,
  );
  const [publicLookupId, setPublicLookupId] = useState("");
  const [publicLookupToken, setPublicLookupToken] = useState("");
  const [publicStatus, setPublicStatus] = useState<PublicJobStatus | null>(null);
  const [publicContactEmail, setPublicContactEmail] = useState("");
  const [isPaying, setIsPaying] = useState(false);
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

  const loadRazorpay = () =>
    new Promise<boolean>((resolve) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });

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

  const handlePublicSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem(
      "public-plagiarism",
    ) as HTMLInputElement;
    if (!fileInput.files || fileInput.files.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("requester_email", publicEmail);
    if (publicName) {
      formData.append("requester_name", publicName);
    }
    try {
      const response = await apiFetch<PublicJobResponse>(
        "/plagiarism/public-jobs",
        {
          method: "POST",
          body: formData,
        },
      );
      setPublicResponse(response);
      setPublicLookupId(String(response.id));
      setPublicLookupToken(response.access_token);
      setPublicStatus(null);
      setPublicContactEmail(publicEmail);
      form.reset();
      setPublicEmail("");
      setPublicName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create job");
    }
  };

  const handlePublicLookup = async () => {
    if (!publicLookupId || !publicLookupToken) {
      return;
    }
    try {
      const response = await apiFetch<PublicJobStatus>(
        `/plagiarism/public-jobs/${publicLookupId}?access_token=${encodeURIComponent(
          publicLookupToken,
        )}`,
      );
      setPublicStatus(response);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to fetch job status",
      );
    }
  };

  const handlePublicPayment = async () => {
    if (!publicLookupId || !publicLookupToken) {
      return;
    }
    setIsPaying(true);
    try {
      const loaded = await loadRazorpay();
      if (!loaded) {
        throw new Error("Unable to load payment gateway");
      }
      const order = await apiFetch<RazorpayOrder>(
        `/plagiarism/public-jobs/${publicLookupId}/razorpay/order?access_token=${encodeURIComponent(
          publicLookupToken,
        )}`,
        {
          method: "POST",
        },
      );
      const RazorpayConstructor = window.Razorpay;
      if (!RazorpayConstructor) {
        throw new Error("Payment gateway unavailable");
      }
      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "AcadFlow",
        description: "Plagiarism check",
        order_id: order.order_id,
        prefill: {
          email: publicContactEmail || publicEmail,
        },
        handler: async (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) => {
          await apiFetch(
            `/plagiarism/public-jobs/${order.job_id}/razorpay/verify?access_token=${encodeURIComponent(
              publicLookupToken,
            )}`,
            {
              method: "POST",
              body: JSON.stringify(response),
            },
          );
          await handlePublicLookup();
        },
        theme: { color: "#0f172a" },
      };
      const razorpay = new RazorpayConstructor(options);
      razorpay.open();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setIsPaying(false);
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

  const downloadPublicReport = async (jobId: number, filename?: string) => {
    const baseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    try {
      const response = await fetch(
        `${baseUrl}/plagiarism/public-jobs/${jobId}/report?access_token=${encodeURIComponent(
          publicLookupToken,
        )}`,
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
        title="Public plagiarism check"
        description="Anyone can submit a manuscript without creating an account."
      >
        <form onSubmit={handlePublicSubmit} className="grid gap-3 md:grid-cols-2">
          <input
            type="text"
            value={publicName}
            onChange={(event) => setPublicName(event.target.value)}
            placeholder="Full name (optional)"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="email"
            value={publicEmail}
            onChange={(event) => setPublicEmail(event.target.value)}
            placeholder="Email address"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
            required
          />
          <input
            type="file"
            name="public-plagiarism"
            className="text-sm md:col-span-2"
            required
          />
          <button
            type="submit"
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white md:col-span-2"
          >
            Submit for review
          </button>
        </form>
        {publicResponse && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900">
              Submission received • Job #{publicResponse.id}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Save your access token to track status and download the report.
            </p>
            <div className="mt-3 grid gap-2 text-xs">
              <div>
                Access token:{" "}
                <span className="font-mono">{publicResponse.access_token}</span>
              </div>
              <div>
                Estimated fee:{" "}
                {formatCurrency(
                  publicResponse.amount_cents,
                  publicResponse.currency,
                )}
              </div>
              <div>ETA: {publicResponse.eta_hours} hours</div>
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handlePublicPayment}
                disabled={isPaying}
                className="rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                {isPaying ? "Opening gateway..." : "Pay with Razorpay"}
              </button>
              <p className="text-[11px] text-slate-400">
                Pay via UPI, card, or netbanking. You will be redirected after
                payment.
              </p>
            </div>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Track a public plagiarism job"
        description="Use your job ID and access token to view status."
      >
        <div className="flex flex-wrap gap-3">
          <input
            type="number"
            value={publicLookupId}
            onChange={(event) => setPublicLookupId(event.target.value)}
            placeholder="Job ID"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="text"
            value={publicLookupToken}
            onChange={(event) => setPublicLookupToken(event.target.value)}
            placeholder="Access token"
            className="min-w-[220px] flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={handlePublicLookup}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Check status
          </button>
        </div>
        {publicStatus && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-600">
            <div>
              Job #{publicStatus.id} • {publicStatus.status} • Payment{" "}
              {publicStatus.payment_status}
              <div className="text-xs text-slate-400">
                {formatCurrency(publicStatus.amount_cents, publicStatus.currency)}
              </div>
            </div>
            {publicStatus.report_filename ? (
              <button
                type="button"
                onClick={() =>
                  downloadPublicReport(
                    publicStatus.id,
                    publicStatus.report_filename,
                  )
                }
                className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700"
              >
                Download report
              </button>
            ) : (
              <span className="text-xs text-slate-400">Report pending</span>
            )}
          </div>
        )}
        {publicStatus &&
          publicStatus.payment_status === "pending" &&
          !publicStatus.report_filename && (
            <div className="mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
              <button
                type="button"
                onClick={handlePublicPayment}
                disabled={isPaying}
                className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                {isPaying ? "Opening gateway..." : "Pay with Razorpay"}
              </button>
              <span className="text-[11px] text-slate-400">
                Complete payment to access the report once it is ready.
              </span>
            </div>
          )}
      </SectionCard>

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

      {user && (
        <SectionCard title="Recent plagiarism jobs">
          {isLoading ? (
            <div className="text-sm text-slate-500">Loading jobs...</div>
          ) : jobs.length === 0 ? (
            <div className="text-sm text-slate-500">
              No jobs submitted yet.
            </div>
          ) : (
            <div className="space-y-3 text-sm text-slate-600">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 px-4 py-3"
                >
                  <div>
                    Job #{job.id} •{" "}
                    {job.project_id ? `Project #${job.project_id}` : "Public"} •{" "}
                    {job.status}
                    <div className="text-xs text-slate-400">
                      Payment: {job.payment_status} •{" "}
                      {formatCurrency(job.amount_cents, job.currency)}
                    </div>
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
      )}
    </div>
  );
}

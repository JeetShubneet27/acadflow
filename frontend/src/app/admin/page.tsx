"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

type Project = {
  id: number;
  title: string;
  visibility: string;
};

type Job = {
  id: number;
  project_id?: number | null;
  status: string;
  original_filename: string;
  is_public: boolean;
  requester_email?: string | null;
  payment_status: string;
  amount_cents: number;
  currency: string;
  payment_reference?: string | null;
  payment_submitted_at?: string | null;
};

export default function AdminPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [roleUserId, setRoleUserId] = useState("");
  const [role, setRole] = useState("student");
  const [assignProjectId, setAssignProjectId] = useState("");
  const [assignReviewerId, setAssignReviewerId] = useState("");
  const [paymentJobId, setPaymentJobId] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("pending");
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [projectData, jobData] = await Promise.all([
        apiFetch<Project[]>("/projects"),
        apiFetch<Job[]>("/plagiarism/jobs"),
      ]);
      setProjects(projectData);
      setJobs(jobData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load admin data");
    }
  };

  useEffect(() => {
    if (user?.role === "faculty") {
      load();
    }
  }, [user]);

  const handleRoleUpdate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiFetch(`/users/${roleUserId}/role`, {
        method: "PUT",
        body: JSON.stringify({ role }),
      });
      setRoleUserId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update role");
    }
  };

  const handleAssign = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiFetch(`/projects/${assignProjectId}/reviews/assign`, {
        method: "POST",
        body: JSON.stringify({ reviewer_id: Number(assignReviewerId) }),
      });
      setAssignProjectId("");
      setAssignReviewerId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to assign reviewer");
    }
  };

  const handlePaymentUpdate = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    try {
      await apiFetch(`/plagiarism/jobs/${paymentJobId}/payment`, {
        method: "PUT",
        body: JSON.stringify({ status: paymentStatus }),
      });
      setPaymentJobId("");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to update payment status",
      );
    }
  };

  if (!user) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Log in to access faculty tools.
      </div>
    );
  }

  if (user.role !== "faculty") {
    return (
      <SectionCard
        title="Faculty dashboard"
        description="Only faculty administrators can access these tools."
      >
        <div className="text-sm text-slate-600">
          You do not have faculty permissions.
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Faculty oversight
        </h1>
        <p className="text-sm text-slate-600">
          Manage roles, reviewer assignments, and plagiarism workflows.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Update user role">
          <form onSubmit={handleRoleUpdate} className="space-y-3">
            <input
              type="number"
              value={roleUserId}
              onChange={(event) => setRoleUserId(event.target.value)}
              placeholder="User ID"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <select
              value={role}
              onChange={(event) => setRole(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
            </select>
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Update role
            </button>
          </form>
        </SectionCard>
        <SectionCard title="Assign reviewer">
          <form onSubmit={handleAssign} className="space-y-3">
            <input
              type="number"
              value={assignProjectId}
              onChange={(event) => setAssignProjectId(event.target.value)}
              placeholder="Project ID"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <input
              type="number"
              value={assignReviewerId}
              onChange={(event) => setAssignReviewerId(event.target.value)}
              placeholder="Reviewer user ID"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Assign reviewer
            </button>
          </form>
        </SectionCard>
        <SectionCard title="Update payment status">
          <form onSubmit={handlePaymentUpdate} className="space-y-3">
            <input
              type="number"
              value={paymentJobId}
              onChange={(event) => setPaymentJobId(event.target.value)}
              placeholder="Job ID"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <select
              value={paymentStatus}
              onChange={(event) => setPaymentStatus(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="waived">Waived</option>
            </select>
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Update payment
            </button>
          </form>
        </SectionCard>
      </div>

      <SectionCard title="All projects">
        <div className="space-y-2 text-sm text-slate-600">
          {projects.map((project) => (
            <div key={project.id} className="rounded-xl border border-slate-200 px-3 py-2">
              #{project.id} • {project.title} • {project.visibility}
            </div>
          ))}
          {projects.length === 0 && (
            <div className="text-slate-400">No projects found.</div>
          )}
        </div>
      </SectionCard>

      <SectionCard title="Plagiarism jobs">
        <div className="space-y-2 text-sm text-slate-600">
          {jobs.map((job) => (
            <div key={job.id} className="rounded-xl border border-slate-200 px-3 py-2">
              <div className="font-medium text-slate-900">
                Job #{job.id} • {job.is_public ? "Public" : `Project #${job.project_id}`} •{" "}
                {job.status}
              </div>
              <div className="text-xs text-slate-500">
                Payment: {job.payment_status} •{" "}
                {formatCurrency(job.amount_cents, job.currency)}
                {job.requester_email ? ` • ${job.requester_email}` : ""}
                {job.payment_reference ? ` • UTR ${job.payment_reference}` : ""}
              </div>
            </div>
          ))}
          {jobs.length === 0 && (
            <div className="text-slate-400">No jobs queued.</div>
          )}
        </div>
      </SectionCard>
    </div>
  );
}

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
  payment_provider?: string | null;
  payment_order_id?: string | null;
  payment_payment_id?: string | null;
};

type Conference = {
  id: number;
  title: string;
  website?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  submission_deadline?: string | null;
  description?: string | null;
};

export default function AdminPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [conferences, setConferences] = useState<Conference[]>([]);
  const [roleUserId, setRoleUserId] = useState("");
  const [role, setRole] = useState("student");
  const [assignProjectId, setAssignProjectId] = useState("");
  const [assignReviewerId, setAssignReviewerId] = useState("");
  const [paymentJobId, setPaymentJobId] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("pending");
  const [conferenceForm, setConferenceForm] = useState({
    title: "",
    website: "",
    location: "",
    start_date: "",
    end_date: "",
    submission_deadline: "",
    description: "",
  });
  const [cleanupResult, setCleanupResult] = useState<{
    expired_invites: number;
    expired_locks: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [projectData, jobData, conferenceData] = await Promise.all([
        apiFetch<Project[]>("/projects"),
        apiFetch<Job[]>("/plagiarism/jobs"),
        apiFetch<Conference[]>("/conferences?limit=100"),
      ]);
      setProjects(projectData);
      setJobs(jobData);
      setConferences(conferenceData);
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

  const handleCleanup = async () => {
    try {
      const response = await apiFetch<{
        expired_invites: number;
        expired_locks: number;
      }>("/maintenance/cleanup", { method: "POST" });
      setCleanupResult(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run cleanup");
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

  const handleConferenceChange = (field: keyof typeof conferenceForm, value: string) => {
    setConferenceForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleConferenceCreate = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    try {
      await apiFetch("/conferences", {
        method: "POST",
        body: JSON.stringify({
          title: conferenceForm.title,
          website: conferenceForm.website || null,
          location: conferenceForm.location || null,
          start_date: conferenceForm.start_date || null,
          end_date: conferenceForm.end_date || null,
          submission_deadline: conferenceForm.submission_deadline || null,
          description: conferenceForm.description || null,
        }),
      });
      setConferenceForm({
        title: "",
        website: "",
        location: "",
        start_date: "",
        end_date: "",
        submission_deadline: "",
        description: "",
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create conference");
    }
  };

  const handleConferenceDelete = async (conferenceId: number) => {
    try {
      await apiFetch(`/conferences/${conferenceId}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete conference");
    }
  };

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
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
        <div className="text-sm text-[var(--color-muted)]">
          You do not have faculty permissions.
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          Admin dashboard
        </h1>
        <p className="text-sm text-[var(--color-muted)]">
          Manage roles, reviewer assignments, payments, and plagiarism workflows.
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
              className="input"
              required
            />
            <select
              value={role}
              onChange={(event) => setRole(event.target.value)}
              className="select"
            >
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
            </select>
            <button
              type="submit"
              className="btn btn-primary"
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
              className="input"
              required
            />
            <input
              type="number"
              value={assignReviewerId}
              onChange={(event) => setAssignReviewerId(event.target.value)}
              placeholder="Reviewer user ID"
              className="input"
              required
            />
            <button
              type="submit"
              className="btn btn-primary"
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
              className="input"
              required
            />
            <select
              value={paymentStatus}
              onChange={(event) => setPaymentStatus(event.target.value)}
              className="select"
            >
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="waived">Waived</option>
            </select>
            <button
              type="submit"
              className="btn btn-primary"
            >
              Update payment
            </button>
          </form>
        </SectionCard>
        <SectionCard title="Add conference">
          <form onSubmit={handleConferenceCreate} className="space-y-3">
            <input
              value={conferenceForm.title}
              onChange={(event) => handleConferenceChange("title", event.target.value)}
              placeholder="Conference title"
              className="input"
              required
            />
            <input
              value={conferenceForm.website}
              onChange={(event) => handleConferenceChange("website", event.target.value)}
              placeholder="Website (optional)"
              className="input"
            />
            <input
              value={conferenceForm.location}
              onChange={(event) => handleConferenceChange("location", event.target.value)}
              placeholder="Location (optional)"
              className="input"
            />
            <div className="grid gap-3 md:grid-cols-2">
              <input
                type="date"
                value={conferenceForm.start_date}
                onChange={(event) => handleConferenceChange("start_date", event.target.value)}
                className="input"
              />
              <input
                type="date"
                value={conferenceForm.end_date}
                onChange={(event) => handleConferenceChange("end_date", event.target.value)}
                className="input"
              />
            </div>
            <input
              type="date"
              value={conferenceForm.submission_deadline}
              onChange={(event) =>
                handleConferenceChange("submission_deadline", event.target.value)
              }
              className="input"
            />
            <textarea
              value={conferenceForm.description}
              onChange={(event) => handleConferenceChange("description", event.target.value)}
              placeholder="Short description (optional)"
              className="textarea"
              rows={3}
            />
            <button type="submit" className="btn btn-primary">
              Add conference
            </button>
          </form>
        </SectionCard>
        <SectionCard title="Manage conferences">
          <div className="space-y-2 text-sm text-[var(--color-muted)]">
            {conferences.map((conference) => (
              <div
                key={conference.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] px-3 py-2"
              >
                <div>
                  <div className="font-medium text-[var(--color-text)]">
                    {conference.title}
                  </div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {conference.submission_deadline
                      ? `Deadline: ${conference.submission_deadline}`
                      : "Deadline: TBA"}
                    {conference.location ? ` • ${conference.location}` : ""}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleConferenceDelete(conference.id)}
                  className="btn btn-secondary btn-xs"
                >
                  Delete
                </button>
              </div>
            ))}
            {conferences.length === 0 && (
              <div className="text-[var(--color-muted)]">No conferences added.</div>
            )}
          </div>
        </SectionCard>
        <SectionCard title="Maintenance cleanup">
          <p className="text-xs text-[var(--color-muted)]">
            Expire stale invites and draft locks.
          </p>
          <button
            type="button"
            onClick={handleCleanup}
            className="btn btn-primary mt-3"
          >
            Run cleanup
          </button>
          {cleanupResult && (
            <div className="mt-3 text-xs text-[var(--color-muted)]">
              Expired invites: {cleanupResult.expired_invites} • Expired locks:{" "}
              {cleanupResult.expired_locks}
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title="All projects">
        <div className="space-y-2 text-sm text-[var(--color-muted)]">
          {projects.map((project) => (
            <div key={project.id} className="rounded-xl border border-[var(--color-border)] px-3 py-2">
              #{project.id} • {project.title} • {project.visibility}
            </div>
          ))}
          {projects.length === 0 && (
            <div className="text-[var(--color-muted)]">No projects found.</div>
          )}
        </div>
      </SectionCard>

      <SectionCard title="Plagiarism jobs">
        <div className="space-y-2 text-sm text-[var(--color-muted)]">
          {jobs.map((job) => (
            <div key={job.id} className="rounded-xl border border-[var(--color-border)] px-3 py-2">
              <div className="font-medium text-[var(--color-text)]">
                Job #{job.id} • {job.is_public ? "Public" : `Project #${job.project_id}`} •{" "}
                {job.status}
              </div>
              <div className="text-xs text-[var(--color-muted)]">
                Payment: {job.payment_status} •{" "}
                {formatCurrency(job.amount_cents, job.currency)}
                {job.requester_email ? ` • ${job.requester_email}` : ""}
                {job.payment_reference ? ` • UTR ${job.payment_reference}` : ""}
                {job.payment_provider ? ` • ${job.payment_provider}` : ""}
                {job.payment_order_id ? ` • Order ${job.payment_order_id}` : ""}
                {job.payment_payment_id ? ` • Payment ${job.payment_payment_id}` : ""}
              </div>
            </div>
          ))}
          {jobs.length === 0 && (
            <div className="text-[var(--color-muted)]">No jobs queued.</div>
          )}
        </div>
      </SectionCard>
    </div>
  );
}

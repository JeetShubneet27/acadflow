"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Project = {
  id: number;
  title: string;
  abstract?: string;
  visibility: string;
  owner_id: number;
};

type Member = {
  user_id: number;
  role: string;
};

type Draft = {
  id: number;
  version: number;
  original_filename: string;
  created_at: string;
};

type Review = {
  id: number;
  reviewer_id: number;
  status: string;
  score?: number;
  comments?: string;
};

type Job = {
  id: number;
  project_id: number;
  status: string;
  eta_hours: number;
  original_filename: string;
  report_filename?: string;
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("coauthor");
  const [reviewerId, setReviewerId] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    try {
      setIsLoading(true);
      const [projectData, memberData, draftData, reviewData, jobData] =
        await Promise.all([
          apiFetch<Project>(`/projects/${projectId}`),
          apiFetch<Member[]>(`/projects/${projectId}/members`),
          apiFetch<Draft[]>(`/projects/${projectId}/drafts`),
          apiFetch<Review[]>(`/projects/${projectId}/reviews`),
          apiFetch<Job[]>(`/plagiarism/jobs`),
        ]);
      setProject(projectData);
      setMembers(memberData);
      setDrafts(draftData);
      setReviews(reviewData);
      setJobs(jobData.filter((job) => job.project_id === projectId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load project");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (Number.isFinite(projectId)) {
      load();
    }
  }, [projectId]);

  const handleInvite = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiFetch(`/projects/${projectId}/invite`, {
        method: "POST",
        body: JSON.stringify({
          invitee_email: inviteEmail,
          membership_role: inviteRole,
        }),
      });
      setInviteEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send invite");
    }
  };

  const handleDraftUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("draft") as HTMLInputElement;
    if (!fileInput.files || fileInput.files.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    try {
      await apiFetch(`/projects/${projectId}/drafts`, {
        method: "POST",
        body: formData,
      });
      form.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to upload draft");
    }
  };

  const handlePlagiarism = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem(
      "plagiarism",
    ) as HTMLInputElement;
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
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to request plagiarism",
      );
    }
  };

  const handleAssignReviewer = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    if (!reviewerId) {
      return;
    }
    try {
      await apiFetch(`/projects/${projectId}/reviews/assign`, {
        method: "POST",
        body: JSON.stringify({ reviewer_id: Number(reviewerId) }),
      });
      setReviewerId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to assign reviewer");
    }
  };

  if (!user) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Log in to view project details.
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-sm text-slate-500">Loading project...</div>;
  }

  if (!project) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Project not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          {project.title}
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          {project.abstract || "No abstract provided yet."}
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Team members" description="Current collaborators.">
          <ul className="space-y-2 text-sm text-slate-600">
            {members.map((member) => (
              <li key={member.user_id}>
                User #{member.user_id} • {member.role}
              </li>
            ))}
          </ul>
        </SectionCard>
        {(user.role === "faculty" || user.id === project.owner_id) && (
          <SectionCard title="Invite collaborator">
            <form onSubmit={handleInvite} className="space-y-3">
              <input
                type="email"
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                placeholder="Invitee email"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                required
              />
              <select
                value={inviteRole}
                onChange={(event) => setInviteRole(event.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="coauthor">Co-author</option>
                <option value="owner">Owner</option>
              </select>
              <button
                type="submit"
                className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
              >
                Send invite
              </button>
            </form>
          </SectionCard>
        )}
      </div>

      <SectionCard title="Drafts">
        <form onSubmit={handleDraftUpload} className="flex flex-wrap gap-3">
          <input type="file" name="draft" className="text-sm" required />
          <button
            type="submit"
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Upload draft
          </button>
        </form>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {drafts.map((draft) => (
            <li key={draft.id}>
              v{draft.version} • {draft.original_filename}
            </li>
          ))}
          {drafts.length === 0 && (
            <li className="text-slate-400">No drafts uploaded yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard title="Plagiarism checks">
        <form onSubmit={handlePlagiarism} className="flex flex-wrap gap-3">
          <input type="file" name="plagiarism" className="text-sm" required />
          <button
            type="submit"
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Request check
          </button>
        </form>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {jobs.map((job) => (
            <li key={job.id}>
              Job #{job.id} • {job.status} • {job.original_filename}
            </li>
          ))}
          {jobs.length === 0 && (
            <li className="text-slate-400">No jobs requested yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard title="Reviews">
        {user.role === "faculty" && (
          <form onSubmit={handleAssignReviewer} className="flex flex-wrap gap-3">
            <input
              type="number"
              value={reviewerId}
              onChange={(event) => setReviewerId(event.target.value)}
              placeholder="Reviewer user id"
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Assign reviewer
            </button>
          </form>
        )}
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {reviews.map((review) => (
            <li key={review.id}>
              Reviewer #{review.reviewer_id} • {review.status}{" "}
              {review.score ? `• Score ${review.score}` : ""}
            </li>
          ))}
          {reviews.length === 0 && (
            <li className="text-slate-400">No reviews yet.</li>
          )}
        </ul>
      </SectionCard>
    </div>
  );
}

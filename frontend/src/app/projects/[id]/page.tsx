"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatCurrency } from "@/lib/format";
import { loadRazorpay, openRazorpay } from "@/lib/razorpay";

type Project = {
  id: number;
  title: string;
  abstract?: string;
  visibility: string;
  owner_id: number;
};

type Member = {
  id: number;
  user_id: number;
  role: string;
  status: string;
};

type Draft = {
  id: number;
  version: number;
  original_filename: string;
  created_at: string;
};

type DraftLock = {
  id: number;
  draft_id: number;
  locked_by_id: number;
  status: string;
  locked_at: string;
  expires_at: string;
  released_at?: string | null;
};

type Invite = {
  id: number;
  project_id: number;
  invitee_id: number;
  status: string;
  membership_role: string;
  expires_at?: string | null;
  revoked_at?: string | null;
  accepted_at?: string | null;
  rejected_at?: string | null;
};

type Permissions = {
  can_view: boolean;
  can_invite: boolean;
  can_manage_members: boolean;
  can_change_visibility: boolean;
  can_upload_drafts: boolean;
  can_comment: boolean;
  can_assign_reviewers: boolean;
};

type Annotation = {
  id: number;
  draft_id: number;
  author_id: number;
  parent_id?: number | null;
  anchor_type: string;
  anchor_data?: Record<string, unknown> | null;
  body: string;
  status: string;
  created_at: string;
  resolved_at?: string | null;
  resolved_by_id?: number | null;
};

type ActivityEvent = {
  id: number;
  actor_id?: number | null;
  event_type: string;
  summary: string;
  created_at: string;
};

type AuditEvent = {
  id: number;
  actor_id?: number | null;
  event_type: string;
  entity_type?: string | null;
  entity_id?: number | null;
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

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [permissions, setPermissions] = useState<Permissions | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [draftLocks, setDraftLocks] = useState<Record<number, DraftLock | null>>(
    {},
  );
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedDraftId, setSelectedDraftId] = useState<number | null>(null);
  const [annotationBody, setAnnotationBody] = useState("");
  const [annotationAnchorType, setAnnotationAnchorType] = useState("page");
  const [annotationAnchorValue, setAnnotationAnchorValue] = useState("");
  const [replyInputs, setReplyInputs] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("coauthor");
  const [reviewerId, setReviewerId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [payingJobId, setPayingJobId] = useState<number | null>(null);

  const load = async () => {
    try {
      setIsLoading(true);
      const [
        projectData,
        memberData,
        draftData,
        reviewData,
        jobData,
        permissionsData,
        activityData,
      ] = await Promise.all([
        apiFetch<Project>(`/projects/${projectId}`),
        apiFetch<Member[]>(`/projects/${projectId}/members`),
        apiFetch<Draft[]>(`/projects/${projectId}/drafts`),
        apiFetch<Review[]>(`/projects/${projectId}/reviews`),
        apiFetch<Job[]>(`/plagiarism/jobs`),
        apiFetch<Permissions>(`/projects/${projectId}/permissions`),
        apiFetch<ActivityEvent[]>(`/projects/${projectId}/activity`),
      ]);
      setProject(projectData);
      setMembers(memberData);
      setDrafts(draftData);
      setReviews(reviewData);
      setJobs(jobData.filter((job) => job.project_id === projectId));
      setPermissions(permissionsData);
      setActivity(activityData);
      if (!selectedDraftId && draftData.length > 0) {
        setSelectedDraftId(draftData[0].id);
      }
      const inviteResult = await Promise.allSettled([
        apiFetch<Invite[]>(`/projects/${projectId}/invites`),
        apiFetch<AuditEvent[]>(`/projects/${projectId}/audit`),
      ]);
      if (inviteResult[0].status === "fulfilled") {
        setInvites(inviteResult[0].value);
      } else {
        setInvites([]);
      }
      if (inviteResult[1].status === "fulfilled") {
        setAuditEvents(inviteResult[1].value);
      } else {
        setAuditEvents([]);
      }
      const lockResults = await Promise.allSettled(
        draftData.map((draft) => apiFetch<DraftLock>(`/drafts/${draft.id}/lock`)),
      );
      const lockMap: Record<number, DraftLock | null> = {};
      draftData.forEach((draft, index) => {
        const result = lockResults[index];
        lockMap[draft.id] = result.status === "fulfilled" ? result.value : null;
      });
      setDraftLocks(lockMap);
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

  useEffect(() => {
    const fetchAnnotations = async () => {
      if (!selectedDraftId) {
        return;
      }
      try {
        const data = await apiFetch<Annotation[]>(
          `/drafts/${selectedDraftId}/annotations`,
        );
        setAnnotations(data);
      } catch (err) {
        setAnnotations([]);
      }
    };
    fetchAnnotations();
  }, [selectedDraftId]);

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

  const handleInviteRevoke = async (inviteId: number) => {
    try {
      await apiFetch(`/projects/invites/${inviteId}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to revoke invite");
    }
  };

  const handleInviteResend = async (inviteId: number) => {
    try {
      await apiFetch(`/projects/invites/${inviteId}/resend`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to resend invite");
    }
  };

  const handleMemberRoleChange = async (memberId: number, role: string) => {
    try {
      await apiFetch(`/projects/${projectId}/members/${memberId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update role");
    }
  };

  const handleMemberStatusChange = async (memberId: number, status: string) => {
    try {
      await apiFetch(`/projects/${projectId}/members/${memberId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update status");
    }
  };

  const handleMemberRemove = async (memberId: number) => {
    try {
      await apiFetch(`/projects/${projectId}/members/${memberId}`, {
        method: "DELETE",
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to remove member");
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

  const handleLockDraft = async (draftId: number) => {
    try {
      const lock = await apiFetch<DraftLock>(`/drafts/${draftId}/lock`, {
        method: "POST",
      });
      setDraftLocks((prev) => ({ ...prev, [draftId]: lock }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to lock draft");
    }
  };

  const handleUnlockDraft = async (draftId: number) => {
    try {
      const lock = await apiFetch<DraftLock>(`/drafts/${draftId}/lock`, {
        method: "DELETE",
      });
      setDraftLocks((prev) => ({ ...prev, [draftId]: lock }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to unlock draft");
    }
  };

  const handleAnnotationSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    if (!selectedDraftId || !annotationBody) {
      return;
    }
    const anchor_data =
      annotationAnchorType === "page"
        ? { page: Number(annotationAnchorValue || 1) }
        : { text: annotationAnchorValue };
    try {
      await apiFetch(`/drafts/${selectedDraftId}/annotations`, {
        method: "POST",
        body: JSON.stringify({
          anchor_type: annotationAnchorType,
          anchor_data,
          body: annotationBody,
        }),
      });
      setAnnotationBody("");
      setAnnotationAnchorValue("");
      const data = await apiFetch<Annotation[]>(
        `/drafts/${selectedDraftId}/annotations`,
      );
      setAnnotations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to add annotation");
    }
  };

  const handleAnnotationResolve = async (annotationId: number) => {
    try {
      await apiFetch(`/annotations/${annotationId}/resolve`, { method: "POST" });
      if (selectedDraftId) {
        const data = await apiFetch<Annotation[]>(
          `/drafts/${selectedDraftId}/annotations`,
        );
        setAnnotations(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to resolve annotation");
    }
  };

  const handleAnnotationReopen = async (annotationId: number) => {
    try {
      await apiFetch(`/annotations/${annotationId}/reopen`, { method: "POST" });
      if (selectedDraftId) {
        const data = await apiFetch<Annotation[]>(
          `/drafts/${selectedDraftId}/annotations`,
        );
        setAnnotations(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reopen annotation");
    }
  };

  const handleAnnotationReply = async (annotationId: number, body: string) => {
    if (!body) {
      return;
    }
    try {
      await apiFetch(`/annotations/${annotationId}/replies`, {
        method: "POST",
        body: JSON.stringify({ body }),
      });
      if (selectedDraftId) {
        const data = await apiFetch<Annotation[]>(
          `/drafts/${selectedDraftId}/annotations`,
        );
        setAnnotations(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reply");
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

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Log in to view project details.
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-sm text-[var(--color-muted)]">Loading project...</div>;
  }

  if (!project) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Project not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          {project.title}
        </h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
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
          <div className="space-y-3 text-sm text-[var(--color-muted)]">
            {members.map((member) => (
              <div
                key={member.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] px-3 py-2"
              >
                <div>
                  User #{member.user_id} • {member.role} • {member.status}
                </div>
                {permissions?.can_manage_members && (
                  <div className="flex flex-wrap gap-2">
                    <select
                      defaultValue={member.role}
                      onChange={(event) =>
                        handleMemberRoleChange(member.id, event.target.value)
                      }
                      disabled={member.user_id === project.owner_id}
                      className="select w-auto px-2 py-1 text-xs"
                    >
                      <option value="owner">Owner</option>
                      <option value="coauthor">Co-author</option>
                    </select>
                    <select
                      defaultValue={member.status}
                      onChange={(event) =>
                        handleMemberStatusChange(member.id, event.target.value)
                      }
                      disabled={member.user_id === project.owner_id}
                      className="select w-auto px-2 py-1 text-xs"
                    >
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => handleMemberRemove(member.id)}
                      disabled={member.user_id === project.owner_id}
                      className="btn btn-secondary btn-xs disabled:opacity-50"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
        {permissions?.can_invite && (
          <div className="space-y-4">
            <SectionCard title="Invite collaborator">
              <form onSubmit={handleInvite} className="space-y-3">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(event) => setInviteEmail(event.target.value)}
                  placeholder="Invitee email"
                  className="input"
                  required
                />
                <select
                  value={inviteRole}
                  onChange={(event) => setInviteRole(event.target.value)}
                  className="select"
                >
                  <option value="coauthor">Co-author</option>
                  <option value="owner">Owner</option>
                </select>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Send invite
                </button>
              </form>
            </SectionCard>
            {invites.length > 0 && (
              <SectionCard title="Invitations">
                <div className="space-y-3 text-sm text-[var(--color-muted)]">
                  {invites.map((invite) => (
                    <div
                      key={invite.id}
                      className="rounded-xl border border-[var(--color-border)] px-3 py-2"
                    >
                      <div>
                        Invitee #{invite.invitee_id} • {invite.membership_role} •{" "}
                        {invite.status}
                      </div>
                      {invite.expires_at && (
                        <div className="text-xs text-[var(--color-muted)]">
                          Expires {new Date(invite.expires_at).toLocaleString()}
                        </div>
                      )}
                      <div className="mt-2 flex flex-wrap gap-2">
                        {invite.status === "pending" && (
                          <button
                            type="button"
                            onClick={() => handleInviteRevoke(invite.id)}
                            className="btn btn-secondary btn-xs"
                          >
                            Revoke
                          </button>
                        )}
                        {["expired", "revoked", "rejected"].includes(
                          invite.status,
                        ) && (
                          <button
                            type="button"
                            onClick={() => handleInviteResend(invite.id)}
                            className="btn btn-primary btn-xs"
                          >
                            Resend
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}
          </div>
        )}
      </div>

      <SectionCard title="Drafts">
        {permissions?.can_upload_drafts && (
          <form onSubmit={handleDraftUpload} className="flex flex-wrap gap-3">
            <input type="file" name="draft" className="text-sm" required />
            <button
              type="submit"
              className="btn btn-primary"
            >
              Upload draft
            </button>
          </form>
        )}
        <ul className="mt-4 space-y-2 text-sm text-[var(--color-muted)]">
          {drafts.map((draft) => {
            const lock = draftLocks[draft.id];
            const isLocked = lock?.status === "active";
            return (
              <li
                key={draft.id}
                className="rounded-xl border border-[var(--color-border)] px-3 py-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    v{draft.version} • {draft.original_filename}
                    <div className="text-xs text-[var(--color-muted)]">
                      {isLocked
                        ? `Locked by user #${lock?.locked_by_id}`
                        : "No active lock"}
                    </div>
                  </div>
                  {permissions?.can_upload_drafts && (
                    <>
                      {isLocked ? (
                        <button
                          type="button"
                          onClick={() => handleUnlockDraft(draft.id)}
                          className="btn btn-secondary btn-xs"
                        >
                          Release lock
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleLockDraft(draft.id)}
                          className="btn btn-primary btn-xs"
                        >
                          Lock draft
                        </button>
                      )}
                    </>
                  )}
                </div>
              </li>
            );
          })}
          {drafts.length === 0 && (
            <li className="text-[var(--color-muted)]">No drafts uploaded yet.</li>
          )}
        </ul>
      </SectionCard>

      {permissions?.can_comment && (
        <SectionCard title="Annotations">
          {drafts.length === 0 ? (
          <div className="text-sm text-[var(--color-muted)]">
            Upload a draft to start annotations.
          </div>
          ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <select
                value={selectedDraftId ?? ""}
                onChange={(event) =>
                  setSelectedDraftId(Number(event.target.value))
                }
                className="select"
              >
                {drafts.map((draft) => (
                  <option key={draft.id} value={draft.id}>
                    Draft v{draft.version}
                  </option>
                ))}
              </select>
            </div>
            <form onSubmit={handleAnnotationSubmit} className="grid gap-3 md:grid-cols-4">
              <select
                value={annotationAnchorType}
                onChange={(event) => setAnnotationAnchorType(event.target.value)}
                className="select"
              >
                <option value="page">Page</option>
                <option value="text">Text</option>
              </select>
              <input
                type="text"
                value={annotationAnchorValue}
                onChange={(event) => setAnnotationAnchorValue(event.target.value)}
                placeholder={
                  annotationAnchorType === "page" ? "Page number" : "Text snippet"
                }
                className="input md:col-span-1"
              />
              <input
                type="text"
                value={annotationBody}
                onChange={(event) => setAnnotationBody(event.target.value)}
                placeholder="Add an annotation"
                className="input md:col-span-2"
              />
              <button
                type="submit"
                className="btn btn-primary"
              >
                Add
              </button>
            </form>
            <div className="space-y-3 text-sm text-[var(--color-muted)]">
              {annotations
                .filter((annotation) => !annotation.parent_id)
                .map((annotation) => {
                  const replies = annotations.filter(
                    (reply) => reply.parent_id === annotation.id,
                  );
                  return (
                    <div
                      key={annotation.id}
                      className="rounded-xl border border-[var(--color-border)] px-3 py-2"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          {annotation.anchor_type.toUpperCase()} •{" "}
                          {annotation.anchor_data
                            ? JSON.stringify(annotation.anchor_data)
                            : "General"}
                        </div>
                        <div className="text-xs text-[var(--color-muted)]">
                          {annotation.status}
                        </div>
                      </div>
                      <div className="mt-2">{annotation.body}</div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {annotation.status === "open" ? (
                          <button
                            type="button"
                            onClick={() => handleAnnotationResolve(annotation.id)}
                            className="btn btn-secondary btn-xs"
                          >
                            Resolve
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleAnnotationReopen(annotation.id)}
                            className="btn btn-secondary btn-xs"
                          >
                            Reopen
                          </button>
                        )}
                      </div>
                      <div className="mt-3 space-y-2">
                        {replies.map((reply) => (
                          <div
                            key={reply.id}
                            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-2 text-xs"
                          >
                            Reply by user #{reply.author_id}: {reply.body}
                          </div>
                        ))}
                        <div className="flex flex-wrap gap-2">
                          <input
                            type="text"
                            value={replyInputs[annotation.id] || ""}
                            onChange={(event) =>
                              setReplyInputs((prev) => ({
                                ...prev,
                                [annotation.id]: event.target.value,
                              }))
                            }
                            placeholder="Reply"
                            className="input flex-1 px-3 py-1 text-xs"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              handleAnnotationReply(
                                annotation.id,
                                replyInputs[annotation.id],
                              );
                              setReplyInputs((prev) => ({
                                ...prev,
                                [annotation.id]: "",
                              }));
                            }}
                            className="btn btn-primary btn-xs"
                          >
                            Send
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              {annotations.length === 0 && (
                <div className="text-[var(--color-muted)]">No annotations yet.</div>
              )}
            </div>
          </div>
          )}
        </SectionCard>
      )}

      <SectionCard title="Plagiarism checks">
        <form onSubmit={handlePlagiarism} className="flex flex-wrap gap-3">
          <input type="file" name="plagiarism" className="text-sm" required />
          <button
            type="submit"
            className="btn btn-primary"
          >
            Request check
          </button>
        </form>
        <ul className="mt-4 space-y-2 text-sm text-[var(--color-muted)]">
          {jobs.map((job) => (
            <li key={job.id}>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] px-3 py-2">
                <div>
                  Job #{job.id} • {job.status} • {job.original_filename}
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
                  <span className="text-xs text-[var(--color-muted)]">Report pending</span>
                )}
              </div>
            </li>
          ))}
          {jobs.length === 0 && (
            <li className="text-[var(--color-muted)]">No jobs requested yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard title="Reviews">
        {permissions?.can_assign_reviewers && (
          <form onSubmit={handleAssignReviewer} className="flex flex-wrap gap-3">
            <input
              type="number"
              value={reviewerId}
              onChange={(event) => setReviewerId(event.target.value)}
              placeholder="Reviewer user id"
              className="input w-auto"
              required
            />
            <button
              type="submit"
              className="btn btn-primary"
            >
              Assign reviewer
            </button>
          </form>
        )}
        <ul className="mt-4 space-y-2 text-sm text-[var(--color-muted)]">
          {reviews.map((review) => (
            <li key={review.id}>
              Reviewer #{review.reviewer_id} • {review.status}{" "}
              {review.score ? `• Score ${review.score}` : ""}
            </li>
          ))}
          {reviews.length === 0 && (
            <li className="text-[var(--color-muted)]">No reviews yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard title="Activity feed">
        <div className="space-y-2 text-sm text-[var(--color-muted)]">
          {activity.map((event) => (
            <div key={event.id} className="rounded-xl border border-[var(--color-border)] px-3 py-2">
              <div className="font-medium text-[var(--color-text)]">{event.summary}</div>
              <div className="text-xs text-[var(--color-muted)]">
                User #{event.actor_id ?? "System"} •{" "}
                {new Date(event.created_at).toLocaleString()}
              </div>
            </div>
          ))}
          {activity.length === 0 && (
            <div className="text-[var(--color-muted)]">No activity yet.</div>
          )}
        </div>
      </SectionCard>

      {(permissions?.can_manage_members || user.role === "faculty") && (
        <SectionCard title="Audit log">
          <div className="space-y-2 text-sm text-[var(--color-muted)]">
            {auditEvents.map((event) => (
              <div
                key={event.id}
                className="rounded-xl border border-[var(--color-border)] px-3 py-2"
              >
                <div className="font-medium text-[var(--color-text)]">
                  {event.event_type.replace(/_/g, " ")}
                </div>
                <div className="text-xs text-[var(--color-muted)]">
                  User #{event.actor_id ?? "System"} •{" "}
                  {new Date(event.created_at).toLocaleString()}
                </div>
              </div>
            ))}
            {auditEvents.length === 0 && (
              <div className="text-[var(--color-muted)]">No audit events yet.</div>
            )}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

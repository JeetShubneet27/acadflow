"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Project = {
  id: number;
  title: string;
  abstract?: string;
  visibility: string;
  created_at: string;
};

type Invite = {
  id: number;
  project_id: number;
  status: string;
  membership_role: string;
};

export default function ProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    try {
      setIsLoading(true);
      const [projectData, inviteData] = await Promise.all([
        apiFetch<Project[]>("/projects"),
        apiFetch<Invite[]>("/projects/invites"),
      ]);
      setProjects(projectData);
      setInvites(inviteData.filter((invite) => invite.status === "pending"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load projects");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      load();
    }
  }, [user]);

  const respondInvite = async (inviteId: number, status: string) => {
    try {
      await apiFetch(`/projects/invites/${inviteId}`, {
        method: "PUT",
        body: JSON.stringify({ status }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update invite");
    }
  };

  if (!user) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Log in to view your projects.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Projects</h1>
          <p className="text-sm text-slate-600">
            Manage your research projects and collaborations.
          </p>
        </div>
        <Link
          href="/projects/new"
          className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white"
        >
          New project
        </Link>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {invites.length > 0 && (
        <SectionCard
          title="Pending invitations"
          description="Respond to collaboration invites."
        >
          <div className="space-y-3">
            {invites.map((invite) => (
              <div
                key={invite.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 px-4 py-3 text-sm"
              >
                <div>
                  Project #{invite.project_id} • {invite.membership_role}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => respondInvite(invite.id, "accepted")}
                    className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => respondInvite(invite.id, "rejected")}
                    className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700"
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      <SectionCard
        title="Active projects"
        description="Projects you own or contribute to."
      >
        {isLoading ? (
          <div className="text-sm text-slate-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="text-sm text-slate-500">
            No projects yet. Create one to get started.
          </div>
        ) : (
          <div className="space-y-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/projects/${project.id}`}
                className="flex flex-col gap-1 rounded-xl border border-slate-200 px-4 py-3 text-sm hover:border-slate-300"
              >
                <div className="font-semibold text-slate-900">
                  {project.title}
                </div>
                <div className="text-slate-500">
                  {project.abstract || "No abstract yet."}
                </div>
                <div className="text-xs text-slate-400">
                  Visibility: {project.visibility}
                </div>
              </Link>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

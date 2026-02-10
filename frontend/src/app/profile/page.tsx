"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Profile = {
  email: string;
  full_name: string;
  role: string;
  bio?: string | null;
  institution?: string | null;
  department?: string | null;
  research_interests?: string | null;
  website?: string | null;
  orcid?: string | null;
  linkedin?: string | null;
};

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState({
    bio: "",
    institution: "",
    department: "",
    research_interests: "",
    website: "",
    orcid: "",
    linkedin: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!user) {
        return;
      }
      try {
        const response = await apiFetch<Profile>("/profile");
        setProfile(response);
        setForm({
          bio: response.bio || "",
          institution: response.institution || "",
          department: response.department || "",
          research_interests: response.research_interests || "",
          website: response.website || "",
          orcid: response.orcid || "",
          linkedin: response.linkedin || "",
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load profile");
      }
    };
    load();
  }, [user]);

  const handleChange = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await apiFetch<Profile>("/profile", {
        method: "PUT",
        body: JSON.stringify(form),
      });
      setProfile(response);
      setSuccess("Profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Log in to update your profile.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">Profile</h1>
        <p className="text-sm text-[var(--color-muted)]">
          Introduce yourself to collaborators and reviewers.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {success}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <SectionCard title="Profile details">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-text)]">
                Short bio
              </label>
              <textarea
                value={form.bio}
                onChange={(event) => handleChange("bio", event.target.value)}
                className="textarea"
                rows={4}
                placeholder="Tell collaborators what you’re working on."
              />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">
                  Institution
                </label>
                <input
                  value={form.institution}
                  onChange={(event) =>
                    handleChange("institution", event.target.value)
                  }
                  className="input"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">
                  Department
                </label>
                <input
                  value={form.department}
                  onChange={(event) =>
                    handleChange("department", event.target.value)
                  }
                  className="input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-text)]">
                Research interests
              </label>
              <textarea
                value={form.research_interests}
                onChange={(event) =>
                  handleChange("research_interests", event.target.value)
                }
                className="textarea"
                rows={3}
                placeholder="Keywords or focus areas."
              />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">
                  Website
                </label>
                <input
                  value={form.website}
                  onChange={(event) => handleChange("website", event.target.value)}
                  className="input"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">
                  ORCID
                </label>
                <input
                  value={form.orcid}
                  onChange={(event) => handleChange("orcid", event.target.value)}
                  className="input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-text)]">
                LinkedIn
              </label>
              <input
                value={form.linkedin}
                onChange={(event) => handleChange("linkedin", event.target.value)}
                className="input"
              />
            </div>
            <button
              type="submit"
              disabled={isSaving}
              className="btn btn-primary disabled:opacity-60"
            >
              {isSaving ? "Saving..." : "Save profile"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Profile preview">
          <div className="space-y-3 text-sm text-[var(--color-muted)]">
            <div className="text-base font-semibold text-[var(--color-text)]">
              {profile?.full_name}
            </div>
            <div className="text-xs text-[var(--color-muted)]">
              {profile?.email} • {profile?.role}
            </div>
            {form.bio && <p>{form.bio}</p>}
            <div className="space-y-1 text-xs text-[var(--color-muted)]">
              {form.institution && <div>Institution: {form.institution}</div>}
              {form.department && <div>Department: {form.department}</div>}
              {form.research_interests && (
                <div>Interests: {form.research_interests}</div>
              )}
              {form.website && <div>Website: {form.website}</div>}
              {form.orcid && <div>ORCID: {form.orcid}</div>}
              {form.linkedin && <div>LinkedIn: {form.linkedin}</div>}
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

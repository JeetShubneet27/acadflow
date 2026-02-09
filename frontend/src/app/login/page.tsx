"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiFetch<{ access_token: string }>("/login", {
        method: "POST",
        body: JSON.stringify({ email, password, role }),
      });
      await login(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-[var(--color-text)]">Log in</h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        Access your AcadFlow workspace with your university credentials.
      </p>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">Email</label>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="input"
            required
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">Password</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="input"
            required
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-[var(--color-text)]">
            Login as
          </label>
          <select
            value={role}
            onChange={(event) => setRole(event.target.value)}
            className="select"
          >
            <option value="student">Student</option>
            <option value="faculty">Faculty</option>
          </select>
          <p className="text-xs text-[var(--color-muted)]">
            Faculty accounts must use official institutional emails.
          </p>
        </div>
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary w-full disabled:opacity-60"
        >
          {isSubmitting ? "Logging in..." : "Log in"}
        </button>
      </form>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [otp, setOtp] = useState("");
  const [otpStep, setOtpStep] = useState(false);
  const [otpExpiresIn, setOtpExpiresIn] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiFetch<{ otp_required: boolean; expires_in: number }>(
        "/signup",
        {
          method: "POST",
          body: JSON.stringify({
            email,
            full_name: fullName,
            password,
            role,
          }),
        },
      );
      if (response.otp_required) {
        setOtpStep(true);
        setOtpExpiresIn(response.expires_in);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
      if (message.includes("OTP recently sent")) {
        setOtpStep(true);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOtp = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiFetch<{ access_token: string }>("/auth/otp/verify", {
        method: "POST",
        body: JSON.stringify({
          email,
          otp,
        }),
      });
      await login(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOtp = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiFetch<{ expires_in: number }>("/auth/otp/resend", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setOtpExpiresIn(response.expires_in);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to resend OTP");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-[var(--color-text)]">
        Create your account
      </h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        Start a research project or join an existing collaboration.
      </p>
      {!otpStep ? (
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">
              Full name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="input"
              required
            />
          </div>
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
              Register as
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
              Faculty registrations require official institutional email domains.
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
            {isSubmitting ? "Sending OTP..." : "Send OTP"}
          </button>
          <button
            type="button"
            onClick={() => setOtpStep(true)}
            className="btn btn-ghost w-full"
          >
            Already have a code? Verify email
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp} className="mt-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">
              Enter OTP
            </label>
            <input
              type="text"
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              className="input"
              placeholder="6-digit code"
              required
            />
            <p className="text-xs text-[var(--color-muted)]">
              OTP sent to {email}.{" "}
              {otpExpiresIn ? `Expires in ${Math.ceil(otpExpiresIn / 60)} min.` : ""}
            </p>
            <p className="text-xs text-[var(--color-muted)]">
              Check spam/junk folders if you don’t see the email.
            </p>
          </div>
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {error}
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary disabled:opacity-60"
            >
              {isSubmitting ? "Verifying..." : "Verify & continue"}
            </button>
            <button
              type="button"
              onClick={handleResendOtp}
              disabled={isSubmitting}
              className="btn btn-secondary disabled:opacity-60"
            >
              Resend OTP
            </button>
            <button
              type="button"
              onClick={() => setOtpStep(false)}
              disabled={isSubmitting}
              className="btn btn-ghost"
            >
              Back
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Review = {
  id: number;
  project_id: number;
  status: string;
  score?: number;
  comments?: string;
};

export default function ReviewsPage() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [inputs, setInputs] = useState<Record<number, { score: string; comments: string }>>(
    {},
  );

  const load = async () => {
    if (!user) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await apiFetch<Review[]>("/reviews/assigned");
      setReviews(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load reviews");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "faculty") {
      load();
    } else {
      setIsLoading(false);
    }
  }, [user]);

  const handleSubmit = async (reviewId: number) => {
    const entry = inputs[reviewId];
    if (!entry) {
      return;
    }
    try {
      await apiFetch(`/reviews/${reviewId}`, {
        method: "PUT",
        body: JSON.stringify({
          score: Number(entry.score),
          comments: entry.comments,
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit review");
    }
  };

  if (!user) {
    return (
      <div className="card text-sm text-[var(--color-muted)]">
        Log in to view your reviews.
      </div>
    );
  }

  if (user.role !== "faculty") {
    return (
      <SectionCard
        title="Faculty reviewer workspace"
        description="Only faculty can access assigned review submissions."
      >
        <div className="text-sm text-[var(--color-muted)]">
          Faculty members can accept and submit review assignments.
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">Faculty reviews</h1>
        <p className="text-sm text-[var(--color-muted)]">
          Submit scores and feedback for assigned manuscripts.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <SectionCard title="Assigned reviews">
        {isLoading ? (
          <div className="text-sm text-[var(--color-muted)]">Loading reviews...</div>
        ) : reviews.length === 0 ? (
          <div className="text-sm text-[var(--color-muted)]">
            No reviews assigned right now.
          </div>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div
                key={review.id}
                className="rounded-xl border border-[var(--color-border)] p-4 text-sm"
              >
                <div className="font-semibold text-[var(--color-text)]">
                  Project #{review.project_id}
                </div>
                <div className="text-xs text-[var(--color-muted)]">
                  Status: {review.status}
                </div>
                {review.status !== "submitted" ? (
                  <div className="mt-3 space-y-3">
                    <input
                      type="number"
                      min={1}
                      max={5}
                      placeholder="Score (1-5)"
                      value={inputs[review.id]?.score || ""}
                      onChange={(event) =>
                        setInputs((prev) => ({
                          ...prev,
                          [review.id]: {
                            score: event.target.value,
                            comments: prev[review.id]?.comments || "",
                          },
                        }))
                      }
                      className="input"
                    />
                    <textarea
                      placeholder="Feedback"
                      value={inputs[review.id]?.comments || ""}
                      onChange={(event) =>
                        setInputs((prev) => ({
                          ...prev,
                          [review.id]: {
                            score: prev[review.id]?.score || "",
                            comments: event.target.value,
                          },
                        }))
                      }
                      className="textarea min-h-[90px]"
                    />
                    <button
                      type="button"
                      onClick={() => handleSubmit(review.id)}
                      className="btn btn-primary"
                    >
                      Submit review
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-[var(--color-muted)]">
                    Score: {review.score} • {review.comments || "No comments"}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

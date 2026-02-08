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
    if (user?.role === "reviewer") {
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
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Log in to view your reviews.
      </div>
    );
  }

  if (user.role !== "reviewer") {
    return (
      <SectionCard
        title="Reviewer workspace"
        description="Only reviewers can access assigned review submissions."
      >
        <div className="text-sm text-slate-600">
          Switch to a reviewer role to access this page.
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Reviews</h1>
        <p className="text-sm text-slate-600">
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
          <div className="text-sm text-slate-500">Loading reviews...</div>
        ) : reviews.length === 0 ? (
          <div className="text-sm text-slate-500">
            No reviews assigned right now.
          </div>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div
                key={review.id}
                className="rounded-xl border border-slate-200 p-4 text-sm"
              >
                <div className="font-semibold text-slate-900">
                  Project #{review.project_id}
                </div>
                <div className="text-xs text-slate-500">
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
                      className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
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
                      className="min-h-[90px] w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => handleSubmit(review.id)}
                      className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                    >
                      Submit review
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-slate-600">
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

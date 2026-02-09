export default function Home() {
  return (
    <div className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-8">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[var(--color-muted)]">
            Production-grade research workflows
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-[var(--color-text)] md:text-5xl">
            AcadFlow keeps research teams and faculty reviewers aligned.
          </h1>
          <p className="text-lg text-[var(--color-muted)]">
            Manage projects, collaborate on drafts, request human-reviewed plagiarism
            checks, and coordinate reviewer feedback in one secure platform.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            href="/register"
            className="btn btn-primary"
          >
            Start a research workspace
          </a>
          <a
            href="/login"
            className="btn btn-secondary"
          >
            Log in
          </a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            "Versioned drafts with project visibility controls.",
            "Human-in-the-loop plagiarism workflows with audit trails.",
            "Role-based dashboards for authors and faculty reviewers.",
            "Secure review assignment and structured feedback.",
          ].map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm text-[var(--color-muted)] shadow-sm"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-[var(--color-text)]">
            Built for academic governance
          </h2>
          <ul className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
            <li>• Project membership and co-author invitations.</li>
            <li>• Reviewer assignment with visibility controls.</li>
            <li>• Faculty oversight of plagiarism reports.</li>
            <li>• Audit-friendly version histories.</li>
          </ul>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-[var(--color-text)]">Transparent pricing</h3>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Human-reviewed plagiarism checks start at INR 25 per submission.
          </p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Faculty can waive or adjust payment status per job.
          </p>
        </div>
        <div className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-accent)] p-6 text-sm text-[var(--color-on-primary)] shadow-sm">
          <h3 className="text-lg font-semibold">Ready to pilot AcadFlow?</h3>
          <p className="mt-2 text-[var(--color-on-primary)] opacity-90">
            Launch a workspace for your department or lab in minutes with secure
            role-based onboarding.
          </p>
        </div>
      </div>
    </div>
  );
}

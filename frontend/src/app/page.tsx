export default function Home() {
  return (
    <div className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-8">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
            Production-grade research workflows
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-slate-900 md:text-5xl">
            AcadFlow keeps research teams, reviewers, and faculty aligned.
          </h1>
          <p className="text-lg text-slate-600">
            Manage projects, collaborate on drafts, request human-reviewed plagiarism
            checks, and coordinate reviewer feedback in one secure platform.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            href="/register"
            className="rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white"
          >
            Start a research workspace
          </a>
          <a
            href="/login"
            className="rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700"
          >
            Log in
          </a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            "Versioned drafts with project visibility controls.",
            "Human-in-the-loop plagiarism workflows with audit trails.",
            "Role-based dashboards for authors, reviewers, and faculty.",
            "Secure review assignment and structured feedback.",
          ].map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Built for academic governance
          </h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>• Project membership and co-author invitations.</li>
            <li>• Reviewer assignment with visibility controls.</li>
            <li>• Faculty oversight of plagiarism reports.</li>
            <li>• Audit-friendly version histories.</li>
          </ul>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Transparent pricing</h3>
          <p className="mt-2 text-sm text-slate-600">
            Human-reviewed plagiarism checks start at $25 per submission.
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Faculty can waive or adjust payment status per job.
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-900 to-slate-700 p-6 text-sm text-white shadow-sm">
          <h3 className="text-lg font-semibold">Ready to pilot AcadFlow?</h3>
          <p className="mt-2 text-slate-100">
            Launch a workspace for your department or lab in minutes with secure
            role-based onboarding.
          </p>
        </div>
      </div>
    </div>
  );
}

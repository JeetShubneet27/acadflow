import { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

export default function SectionCard({
  title,
  description,
  children,
}: SectionCardProps) {
  return (
    <section className="card animate-fade-up">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{title}</h2>
        {description && <p className="text-sm text-[var(--color-muted)]">{description}</p>}
      </div>
      {children && <div className="mt-4">{children}</div>}
    </section>
  );
}

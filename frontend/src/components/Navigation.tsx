"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/context/AuthContext";

const navLinks = [
  { href: "/news", label: "News" },
  { href: "/conferences", label: "Conferences" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/profile", label: "Profile" },
  { href: "/projects", label: "Projects" },
  { href: "/drafts", label: "Drafts" },
  { href: "/reviews", label: "Reviews" },
  { href: "/plagiarism", label: "Plagiarism" },
];

export default function Navigation() {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();

  return (
    <nav className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-semibold text-[var(--color-text)]">
          AcadFlow
        </Link>
        <div className="flex items-center gap-4">
          {!isLoading && user ? (
            <>
              <div className="hidden items-center gap-4 md:flex">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`text-sm font-medium ${
                      pathname === link.href
                        ? "text-[var(--color-text)]"
                        : "text-[var(--color-muted)] hover:text-[var(--color-text)]"
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
                {user.role === "faculty" && (
                  <Link
                    href="/admin"
                    className={`text-sm font-medium ${
                      pathname === "/admin"
                        ? "text-[var(--color-text)]"
                        : "text-[var(--color-muted)] hover:text-[var(--color-text)]"
                    }`}
                  >
                    Admin
                  </Link>
                )}
              </div>
              <div className="flex items-center gap-3">
                <div className="text-xs text-[var(--color-muted)]">
                  {user.full_name} • {user.role}
                </div>
                <ThemeToggle />
                <button
                  type="button"
                  onClick={logout}
                  className="btn btn-secondary btn-xs"
                >
                  Log out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                href="/news"
                className="text-sm font-medium text-[var(--color-muted)] hover:text-[var(--color-text)]"
              >
                News
              </Link>
              <Link
                href="/conferences"
                className="text-sm font-medium text-[var(--color-muted)] hover:text-[var(--color-text)]"
              >
                Conferences
              </Link>
              <Link
                href="/login"
                className="text-sm font-medium text-[var(--color-muted)] hover:text-[var(--color-text)]"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="btn btn-primary"
              >
                Sign up
              </Link>
              <ThemeToggle />
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

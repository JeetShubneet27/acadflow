"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/drafts", label: "Drafts" },
  { href: "/reviews", label: "Reviews" },
  { href: "/plagiarism", label: "Plagiarism" },
];

export default function Navigation() {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();

  return (
    <nav className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-semibold text-slate-900">
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
                        ? "text-slate-900"
                        : "text-slate-500 hover:text-slate-900"
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
                        ? "text-slate-900"
                        : "text-slate-500 hover:text-slate-900"
                    }`}
                  >
                    Admin
                  </Link>
                )}
              </div>
              <div className="flex items-center gap-3">
                <div className="text-xs text-slate-500">
                  {user.full_name} • {user.role}
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-full border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                >
                  Log out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-slate-600 hover:text-slate-900"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

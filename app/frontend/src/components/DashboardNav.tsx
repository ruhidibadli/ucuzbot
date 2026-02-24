"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

const navLinks = [
  { href: "/dashboard", label: "Icmal / Overview" },
  { href: "/dashboard/search", label: "Axtar / Search" },
  { href: "/dashboard/alerts", label: "Alertler / Alerts" },
  { href: "/dashboard/alerts/create", label: "Yarat / Create" },
];

export default function DashboardNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <nav className="dashboard-nav">
      <div className="dashboard-nav-left">
        <Link href="/" className="navbar-logo">UcuzaTap</Link>
        <div className="dashboard-nav-links">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`dashboard-nav-link ${pathname === link.href ? "active" : ""}`}
            >
              {link.label}
            </Link>
          ))}
          {user?.is_admin && (
            <Link
              href="/dashboard/admin"
              className={`dashboard-nav-link ${pathname.startsWith("/dashboard/admin") ? "active" : ""}`}
            >
              Admin
            </Link>
          )}
        </div>
      </div>
      <div className="dashboard-nav-right">
        <span className="navbar-user-name">
          {user?.first_name || user?.email}
        </span>
        <button onClick={logout} className="btn btn-ghost btn-sm">
          Cixis / Logout
        </button>
      </div>
    </nav>
  );
}

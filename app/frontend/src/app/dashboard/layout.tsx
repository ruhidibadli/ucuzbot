"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import DashboardNav from "@/components/DashboardNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.push("/");
    }
  }, [isLoading, token, router]);

  if (isLoading) {
    return (
      <div className="dashboard-loading">
        <div className="dashboard-spinner" />
        <p>Yukl&#601;nir... / Loading...</p>
      </div>
    );
  }

  if (!token) {
    return null;
  }

  return (
    <>
      <DashboardNav />
      <main className="dashboard-content">{children}</main>
    </>
  );
}

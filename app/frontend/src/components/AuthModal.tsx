"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password, firstName);
      } else {
        await login(email, password);
      }
      setEmail("");
      setPassword("");
      setFirstName("");
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-close" onClick={onClose}>
          &#10005;
        </button>
        <h2 className="auth-title">
          {mode === "login" ? "Daxil ol / Login" : "Qeydiyyat / Register"}
        </h2>
        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <div className="form-group">
              <label className="form-label" htmlFor="auth-name">Ad / Name</label>
              <input
                id="auth-name"
                type="text"
                className="form-input"
                placeholder="Adiniz"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
            </div>
          )}
          <div className="form-group">
            <label className="form-label" htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              className="form-input"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="auth-password">Sifre / Password</label>
            <input
              id="auth-password"
              type="password"
              className="form-input"
              placeholder="Minimum 6 simvol"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading
              ? "Gozleyin..."
              : mode === "login"
                ? "Daxil ol / Login"
                : "Qeydiyyat / Register"}
          </button>
        </form>
        {error && <div className="alert-msg alert-msg-error">{error}</div>}
        <div className="auth-switch">
          {mode === "login" ? (
            <>
              Hesabiniz yoxdur?{" "}
              <button
                type="button"
                className="auth-switch-btn"
                onClick={() => { setMode("register"); setError(null); }}
              >
                Qeydiyyatdan kecin / Register
              </button>
            </>
          ) : (
            <>
              Artiq hesabiniz var?{" "}
              <button
                type="button"
                className="auth-switch-btn"
                onClick={() => { setMode("login"); setError(null); }}
              >
                Daxil olun / Login
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

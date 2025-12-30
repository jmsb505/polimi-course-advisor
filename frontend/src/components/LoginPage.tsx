import React, { useState } from "react";
import { supabase } from "../lib/supabase";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) {
        throw signInError;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sign in");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Sign In</h2>
        <p className="login-subtitle">PoliMi Course Advisor</p>
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="student@example.com"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading} className="login-btn">
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
      <style>{`
        .login-container {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          width: 100vw;
          background: #05060a;
          background-image: 
            radial-gradient(at 0% 0%, rgba(124, 58, 237, 0.15) 0, transparent 50%), 
            radial-gradient(at 100% 100%, rgba(37, 99, 235, 0.15) 0, transparent 50%);
          position: relative;
          overflow: hidden;
        }
        
        /* Decorative background elements */
        .login-container::before {
          content: "";
          position: absolute;
          width: 300px;
          height: 300px;
          background: rgba(124, 58, 237, 0.1);
          filter: blur(80px);
          border-radius: 50%;
          top: 10%;
          left: 10%;
        }
        
        .login-container::after {
          content: "";
          position: absolute;
          width: 250px;
          height: 250px;
          background: rgba(37, 99, 235, 0.1);
          filter: blur(80px);
          border-radius: 50%;
          bottom: 15%;
          right: 15%;
        }

        .login-box {
          width: 100%;
          max-width: 420px;
          padding: 3rem;
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-radius: 24px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
          z-index: 10;
        }

        .login-box h2 {
          margin: 0;
          font-size: 2.2rem;
          font-weight: 800;
          letter-spacing: -0.025em;
          background: linear-gradient(to right, #f1f5f9, #94a3b8);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          text-align: center;
        }

        .login-subtitle {
          text-align: center;
          color: #94a3b8;
          margin-bottom: 2.5rem;
          font-size: 0.95rem;
          font-weight: 500;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .form-group {
          margin-bottom: 1.5rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.85rem;
          font-weight: 600;
          color: #cbd5e1;
          letter-spacing: 0.01em;
        }

        .form-group input {
          width: 100%;
          padding: 0.9rem 1.1rem;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          color: #f8fafc;
          font-size: 1rem;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          box-sizing: border-box;
        }

        .form-group input:focus {
          outline: none;
          background: rgba(0, 0, 0, 0.3);
          border-color: rgba(124, 58, 237, 0.5);
          box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.1);
        }

        .form-group input::placeholder {
          color: #475569;
        }

        .error-message {
          padding: 0.75rem 1rem;
          background: rgba(239, 68, 68, 0.1);
          color: #fca5a5;
          border-radius: 10px;
          font-size: 0.85rem;
          margin-bottom: 1.5rem;
          border: 1px solid rgba(239, 68, 68, 0.2);
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .login-btn {
          width: 100%;
          padding: 1rem;
          background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 1rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
          margin-top: 1rem;
        }

        .login-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
          filter: brightness(1.1);
        }

        .login-btn:active:not(:disabled) {
          transform: translateY(0);
          filter: brightness(0.9);
        }

        .login-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          box-shadow: none;
        }
      `}</style>
    </div>
  );
};

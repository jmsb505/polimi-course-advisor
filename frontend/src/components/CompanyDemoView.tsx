import React, { useEffect, useState } from "react";
import type { DemoCompany, RankedCandidate } from "../types/demo";
import { getRankedCandidates } from "../api/demo";

interface CompanyDemoViewProps {
    company: DemoCompany;
    onBack: () => void;
}

export const CompanyDemoView: React.FC<CompanyDemoViewProps> = ({
    company,
    onBack,
}) => {
    const [candidates, setCandidates] = useState<RankedCandidate[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchCandidates = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const data = await getRankedCandidates(company.id);
                setCandidates(data);
            } catch (err) {
                setError("Failed to load candidates");
            } finally {
                setIsLoading(false);
            }
        };
        fetchCandidates();
    }, [company.id]);

    return (
        <div className="demo-view-container">
            <div className="demo-content">
                <header className="demo-header">
                    <button className="back-link" onClick={onBack}>
                        ← Back to Companies
                    </button>
                    <div className="company-info">
                        <h1>{company.name}</h1>
                        <p className="industry-badge">{company.industry}</p>
                        <p className="tagline">{company.tagline}</p>
                    </div>
                </header>

                <main className="candidates-section">
                    <h2>Top Talent Matches</h2>
                    <p className="section-subtitle">
                        Ranked based on company's tech stack, hiring keywords, and job requirements.
                    </p>

                    {isLoading ? (
                        <div className="loading-state">Finding best matches...</div>
                    ) : error ? (
                        <div className="error-state">{error}</div>
                    ) : (
                        <div className="candidates-grid">
                            {candidates.map((cand, idx) => (
                                <div key={cand.public_handle} className="candidate-card">
                                    <div className="card-rank">#{idx + 1}</div>
                                    <div className="card-header">
                                        <div className="handle">{cand.public_handle}</div>
                                        <div className="score-badge">
                                            {(cand.score * 100).toFixed(0)}% Fit
                                        </div>
                                    </div>

                                    <div className="card-body">
                                        <div className="detail-section">
                                            <label>Matched Strengths</label>
                                            <div className="chips">
                                                {cand.matched_terms.map((term) => (
                                                    <span key={term} className="chip match">
                                                        {term}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="detail-section">
                                            <label>Skills</label>
                                            <div className="chips">
                                                {cand.skills.slice(0, 4).map((s) => (
                                                    <span key={s} className="chip">
                                                        {s}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="detail-section">
                                            <label>Goals</label>
                                            <p className="goals-text">{cand.goals[0]}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </main>
            </div>

            <style>{`
        .demo-view-container {
          min-height: 100vh;
          width: 100vw;
          background: #05060a;
          color: #f8fafc;
          overflow-y: auto;
          padding: 2rem;
          box-sizing: border-box;
        }

        .demo-content {
          max-width: 1000px;
          margin: 0 auto;
        }

        .demo-header {
          margin-bottom: 3rem;
        }

        .back-link {
          background: transparent;
          border: none;
          color: #94a3b8;
          font-weight: 600;
          cursor: pointer;
          padding: 0;
          margin-bottom: 2rem;
          transition: color 0.2s;
        }

        .back-link:hover {
          color: #f1f5f9;
        }

        .company-info h1 {
          font-size: 2.5rem;
          margin: 0 0 0.5rem 0;
          background: linear-gradient(to right, #f1f5f9, #94a3b8);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .industry-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          background: rgba(124, 58, 237, 0.1);
          color: #a78bfa;
          border: 1px solid rgba(124, 58, 237, 0.2);
          border-radius: 99px;
          font-size: 0.8rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 1rem;
        }

        .tagline {
          color: #94a3b8;
          font-size: 1.1rem;
          margin: 0;
        }

        .candidates-section h2 {
          font-size: 1.8rem;
          margin: 0 0 0.5rem 0;
        }

        .section-subtitle {
          color: #475569;
          margin: 0 0 2rem 0;
        }

        .candidates-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .candidate-card {
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 20px;
          padding: 1.5rem;
          position: relative;
          transition: transform 0.2s;
        }

        .candidate-card:hover {
          transform: translateY(-4px);
          border-color: rgba(124, 58, 237, 0.3);
        }

        .card-rank {
          position: absolute;
          top: -10px;
          right: -10px;
          width: 32px;
          height: 32px;
          background: #7c3aed;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 0.8rem;
          box-shadow: 0 4px 10px rgba(124, 58, 237, 0.4);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .handle {
          font-weight: 700;
          font-size: 1.1rem;
          color: #f1f5f9;
        }

        .score-badge {
          font-size: 0.85rem;
          font-weight: 800;
          color: #10b981;
          background: rgba(16, 185, 129, 0.1);
          padding: 0.25rem 0.5rem;
          border-radius: 6px;
        }

        .detail-section {
          margin-bottom: 1.25rem;
        }

        .detail-section label {
          display: block;
          font-size: 0.7rem;
          font-weight: 800;
          text-transform: uppercase;
          color: #475569;
          margin-bottom: 0.5rem;
          letter-spacing: 0.05em;
        }

        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .chip {
          font-size: 0.75rem;
          padding: 0.2rem 0.5rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
          color: #cbd5e1;
        }

        .chip.match {
          background: rgba(124, 58, 237, 0.15);
          color: #c4b5fd;
          border: 1px solid rgba(124, 58, 237, 0.3);
        }

        .goals-text {
          font-size: 0.85rem;
          color: #94a3b8;
          margin: 0;
          line-height: 1.4;
        }

        .loading-state, .error-state {
          padding: 4rem;
          text-align: center;
          color: #475569;
          font-size: 1.1rem;
        }

        .error-state {
          color: #fca5a5;
        }
      `}</style>
        </div>
    );
};

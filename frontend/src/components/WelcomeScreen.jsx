import React from 'react';

export default function WelcomeScreen({ setInput }) {
  const useCases = [
    { title: 'Strategic Decisions', desc: 'Stress-test business plans or career moves with diverse viewpoints.' },
    { title: 'Creative Ideation', desc: 'Generate and refine unique ideas through a peer-review loop.' },
    { title: 'Risk Assessment', desc: 'Identify blind spots and potential failures in your strategy.' },
    { title: 'Domain Expertise', desc: 'Consult specialized personas tailored to your problem.' }
  ];

  const examples = [
    "Should I quit my job to start a specialized SaaS company in 2026?",
    "What are the long-term biological effects of a 72-hour fast?",
    "How would Sun Tzu and Marcus Aurelius resolve a modern business conflict?",
    "Identify the biggest risks in a pivot to AI-driven manufacturing."
  ];

  return (
    <div className="chat-interface">
      <div className="welcome-container">
        <div className="welcome-header">
          <h1>🏛️ LLM Council</h1>
          <p>Trust the collective intelligence of multiple AI models.</p>
        </div>

        <div className="welcome-grid">
          <div className="welcome-section">
            <h3>🌟 Use Cases</h3>
            <div className="use-case-list">
              {useCases.map((uc, i) => (
                <div key={i} className="use-case-item">
                  <strong>{uc.title}</strong>
                  <span>{uc.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="welcome-section">
            <h3>💬 Example Questions</h3>
            <div className="example-list">
              {examples.map((ex, i) => (
                <button key={i} className="example-btn" onClick={() => setInput(ex)}>
                  {ex}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="welcome-footer">
          <p>Click <strong>+ New Conversation</strong> in the sidebar to get started.</p>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) {
    return null;
  }

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Stage 1: Individual Responses</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''} ${resp.error ? 'error' : ''}`}
            onClick={() => setActiveTab(index)}
            title={resp.error || ''}
          >
            {resp.error && '⚠️ '}
            {resp.model.split('/')[1] || resp.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="model-name">
          {responses[activeTab].model}
          {responses[activeTab].is_reasoning_model && (
            <span className="reasoning-badge" title="Reasoning model with extended thinking">
              🧠 Reasoning Model
            </span>
          )}
          {responses[activeTab].error && (
            <span className="error-badge">⚠️ Error</span>
          )}
        </div>

        {responses[activeTab].persona && (
          <div className="persona-badge">
            <strong>🎭 Role:</strong> {responses[activeTab].persona}
          </div>
        )}

        {responses[activeTab].is_rebuttal && (
          <div className="rebuttal-badge">
            <strong>⚔️ Revised:</strong> This answer was updated after peer review.
          </div>
        )}

        {responses[activeTab].error ? (
          <div className="error-message">
            <strong>Request Failed:</strong> {responses[activeTab].error}
            <p>The model failed to respond or timed out.</p>
          </div>
        ) : (
          <>
            {responses[activeTab].thinking && responses[activeTab].thinking.length > 50 && (
              <details className="thinking-section">
                <summary className="thinking-summary">
                  💭 Show Thinking Process ({Math.round(responses[activeTab].thinking.length / 4)} tokens)
                </summary>
                <div className="thinking-content markdown-content">
                  <ReactMarkdown>{responses[activeTab].thinking}</ReactMarkdown>
                </div>
              </details>
            )}

            <div className="response-text markdown-content">
              <ReactMarkdown>{responses[activeTab].response}</ReactMarkdown>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

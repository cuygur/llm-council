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
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
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
        </div>

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
      </div>
    </div>
  );
}

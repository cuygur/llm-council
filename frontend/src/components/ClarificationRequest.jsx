import React from 'react';
import './ClarificationRequest.css';

export default function ClarificationRequest({ questions }) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="clarification-container">
      <div className="clarification-header">
        <span className="icon">🤔</span>
        <h3>I need some clarification before I can help</h3>
      </div>
      <p className="clarification-intro">
        Your request is a bit open-ended. Could you answer these questions so I can provide the best solution?
      </p>
      <ul className="clarification-list">
        {questions.map((q, index) => (
          <li key={index} className="clarification-item">
            {q}
          </li>
        ))}
      </ul>
      <div className="clarification-footer">
        <p>Please reply with your answers below.</p>
      </div>
    </div>
  );
}

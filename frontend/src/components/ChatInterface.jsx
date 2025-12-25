import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import { api } from '../api';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
}) {
  const [input, setInput] = useState('');
  const [estimate, setEstimate] = useState(null);
  const [isEstimating, setIsEstimating] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  // Handle cost estimation with debouncing
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (input.trim() && !isLoading && conversation?.id) {
        setIsEstimating(true);
        try {
          const data = await api.estimateCost(input, conversation.id);
          setEstimate(data);
        } catch (error) {
          console.error('Estimation failed:', error);
          setEstimate(null);
        } finally {
          setIsEstimating(false);
        }
      } else {
        setEstimate(null);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [input, isLoading, conversation?.id]);

  // Calculate session stats
  const stats = conversation?.messages.reduce(
    (acc, msg) => {
      if (msg.role === 'assistant' && msg.metadata) {
        acc.cost += msg.metadata.total_cost || 0;
        if (msg.metadata.total_tokens) {
          acc.tokens += msg.metadata.total_tokens.total || 0;
        }
      }
      return acc;
    },
    { cost: 0, tokens: 0 }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
      setEstimate(null);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      {conversation && conversation.messages.length > 0 && (
        <div className="chat-header">
          <div className="chat-title">{conversation.title || 'Conversation'}</div>
          <div className="chat-stats">
            <span className="stat-item" title="Total Cost">
              💰 ${stats.cost.toFixed(4)}
            </span>
            <span className="stat-item" title="Total Tokens">
              🔢 {stats.tokens.toLocaleString()} tokens
            </span>
          </div>
        </div>
      )}

      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>Start a conversation</h2>
            <p>Ask a question to consult the LLM Council</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {/* Persona Resolution */}
                  {msg.loading?.resolving && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Summoning domain specialists and preparing council...</span>
                    </div>
                  )}

                  {/* Stage 1 */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>
                        {msg.stage1 
                          ? 'Running Stage 2.5: Rebuttal Round (Models are reviewing critiques)...' 
                          : 'Running Stage 1: Collecting individual responses...'}
                      </span>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 2: Peer rankings...</span>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 3: Final synthesis...</span>
                    </div>
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        {isEstimating && !isLoading && (
          <div className="input-estimate">
            <span className="estimate-item">Calculating cost...</span>
          </div>
        )}
        {estimate && !isLoading && !isEstimating && (
          <div className="input-estimate">
            <span className="estimate-item" title="Estimated Prompt Tokens">
              Input: ~{estimate.prompt_tokens} tokens
            </span>
            <span className="estimate-item" title="Estimated Total Cost (3 Stages)">
              Est. Cost: {estimate.formatted_cost}
            </span>
          </div>
        )}
        <textarea
          className="message-input"
          placeholder="Ask your question... (Shift+Enter for new line, Enter to send)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={3}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isLoading}
        >
          Send
        </button>
      </form>
    </div>
  );
}

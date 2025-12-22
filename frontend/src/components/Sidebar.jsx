import { useState, useEffect } from 'react';
import ExportMenu from './ExportMenu';
import Settings from './Settings';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onOpenSettings,
}) {
  const [exportingConversationId, setExportingConversationId] = useState(null);
  const [exportingConversationTitle, setExportingConversationTitle] = useState(null);
  const [isNewConvModalOpen, setIsNewConvModalOpen] = useState(false);

  const handleCreateNewConversation = (councilModels, chairmanModel, modelPersonas) => {
    onNewConversation(councilModels, chairmanModel, modelPersonas);
    setIsNewConvModalOpen(false);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={() => setIsNewConvModalOpen(true)}>
          + New Conversation
        </button>
        <button className="settings-btn" onClick={onOpenSettings} title="Configure Default Council">
          ⚙️
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
            >
              <div
                className="conversation-content"
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="conversation-title">
                  {conv.title || 'New Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                </div>
              </div>
              {conv.message_count > 0 && (
                <button
                  className="export-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setExportingConversationId(conv.id);
                    setExportingConversationTitle(conv.title);
                  }}
                  title="Export conversation"
                >
                  ⬇️
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {isNewConvModalOpen && (
        <Settings
          isOpen={isNewConvModalOpen}
          onClose={() => setIsNewConvModalOpen(false)}
          onSaveOverride={handleCreateNewConversation}
          title="Start New Conversation"
          saveButtonText="Start Conversation"
        />
      )}

      {exportingConversationId && (
        <ExportMenu
          conversationId={exportingConversationId}
          conversationTitle={exportingConversationTitle}
          onClose={() => {
            setExportingConversationId(null);
            setExportingConversationTitle(null);
          }}
        />
      )}
    </div>
  );
}

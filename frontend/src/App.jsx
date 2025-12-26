import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';
import { api } from './api';
import { useConversation } from './hooks/useConversation';
import './App.css';

function App() {
  const {
    conversations,
    currentConversationId,
    currentConversation,
    isLoading,
    selectConversation,
    createConversation,
    deleteConversation,
    sendMessage
  } = useConversation();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Theme management
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('llm-council-theme');
    if (savedTheme) return savedTheme === 'dark';
    return document.body.getAttribute('data-theme') === 'dark';
  });

  // Apply theme on change
  useEffect(() => {
    const theme = isDarkMode ? 'dark' : 'light';
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('llm-council-theme', theme);
  }, [isDarkMode]);

  // Load saved config on mount (side effect)
  useEffect(() => {
    const loadConfigFromStorage = async () => {
      try {
        const savedConfig = localStorage.getItem('llm-council-config');
        if (savedConfig) {
          const { councilModels, chairmanModel } = JSON.parse(savedConfig);
          await api.updateConfig(councilModels, chairmanModel);
        }
      } catch (error) {
        console.error('Failed to load saved configuration:', error);
      }
    };
    loadConfigFromStorage();
  }, []);

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={selectConversation}
        onNewConversation={createConversation}
        onDeleteConversation={deleteConversation}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={sendMessage}
        isLoading={isLoading}
      />
      <Settings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
      />
    </div>
  );
}

export default App;

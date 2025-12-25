import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

export function useConversation() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadConversations = useCallback(async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError(err.message);
    }
  }, []);

  const loadConversation = useCallback(async (id) => {
    if (!id) return;
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setError(err.message);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    } else {
      setCurrentConversation(null);
    }
  }, [currentConversationId, loadConversation]);

  const selectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const createConversation = async (councilModels, chairmanModel, modelPersonas, mode) => {
    try {
      setIsLoading(true);
      const newConv = await api.createConversation(councilModels, chairmanModel, modelPersonas, mode);
      setConversations(prev => [
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...prev,
      ]);
      setCurrentConversationId(newConv.id);
      setIsLoading(false);
      return newConv;
    } catch (err) {
      console.error('Failed to create conversation:', err);
      setError(err.message);
      setIsLoading(false);
      throw err;
    }
  };

  const deleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError(err.message);
    }
  };

  const sendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message
      const userMessage = { role: 'user', content };
      
      // Update state with optimistic user message
      setCurrentConversation(prev => ({
        ...prev,
        messages: [...(prev?.messages || []), userMessage]
      }));

      // Create partial assistant message placeholder
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          resolving: false,
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add placeholder
      setCurrentConversation(prev => ({
        ...prev,
        messages: [...(prev?.messages || []), assistantMessage]
      }));

      // Stream updates
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        setCurrentConversation(prev => {
          if (!prev) return prev;
          
          const messages = [...prev.messages];
          const lastMsg = messages[messages.length - 1]; // This is our assistant message
          
          // Modify lastMsg **clone** based on event
          // Note: In React state, we must create new objects. 
          // Since messages is cloned array, we can mutate the object inside IF it's a new object reference?
          // No, must clone the object too to be safe/correct.
          const updatedLastMsg = { ...lastMsg, loading: { ...lastMsg.loading } };

          switch (eventType) {
            case 'resolving_personas':
              updatedLastMsg.loading.resolving = true;
              break;
            case 'stage1_start':
              updatedLastMsg.loading.resolving = false;
              updatedLastMsg.loading.stage1 = true;
              break;
            case 'stage1_complete':
              updatedLastMsg.stage1 = event.data;
              updatedLastMsg.loading.stage1 = false;
              break;
            case 'stage2_start':
              updatedLastMsg.loading.stage2 = true;
              break;
            case 'stage2_complete':
              updatedLastMsg.stage2 = event.data;
              updatedLastMsg.metadata = event.metadata;
              updatedLastMsg.loading.stage2 = false;
              break;
            case 'stage2_5_start':
               updatedLastMsg.loading.stage1 = true; // Re-enable loading for rebuttal updates
               break;
            case 'stage3_start':
              updatedLastMsg.loading.stage3 = true;
              break;
            case 'stage3_complete':
              updatedLastMsg.stage3 = event.data;
              updatedLastMsg.loading.stage3 = false;
              break;
            case 'title_complete':
              loadConversations(); // Trigger side effect
              break;
            case 'complete':
              loadConversations();
              setIsLoading(false);
              break;
            case 'error':
              console.error('Stream error:', event.message);
              setIsLoading(false);
              break;
          }
          
          messages[messages.length - 1] = updatedLastMsg;
          return { ...prev, messages };
        });
      });
    } catch (err) {
      console.error('Failed to send message:', err);
      // Remove optimistic messages on error - roughly
      setCurrentConversation(prev => {
        if (!prev) return prev;
        const msgCount = prev.messages.length;
        // We added 2 messages: user and assistant placeholder
        return {
          ...prev,
          messages: prev.messages.slice(0, Math.max(0, msgCount - 2))
        };
      });
      setIsLoading(false);
      setError(err.message);
    }
  };

  return {
    conversations,
    currentConversationId,
    currentConversation,
    isLoading,
    error,
    selectConversation,
    createConversation,
    deleteConversation,
    sendMessage
  };
}

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from '../components/Sidebar';

describe('Sidebar', () => {
  const mockConversations = [
    { id: '1', title: 'Test Conv 1', message_count: 5 },
    { id: '2', title: 'Test Conv 2', message_count: 0 }
  ];

  it('renders correctly', () => {
    render(
      <Sidebar 
        conversations={mockConversations} 
        currentConversationId="1"
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
        onDeleteConversation={() => {}}
        onOpenSettings={() => {}}
      />
    );

    expect(screen.getByText('LLM Council')).toBeInTheDocument();
    expect(screen.getByText('Test Conv 1')).toBeInTheDocument();
    expect(screen.getByText('Test Conv 2')).toBeInTheDocument();
  });

  it('calls onSelectConversation when a conversation is clicked', () => {
    const onSelect = vi.fn();
    render(
      <Sidebar 
        conversations={mockConversations} 
        currentConversationId="1"
        onSelectConversation={onSelect}
        onNewConversation={() => {}}
        onDeleteConversation={() => {}}
        onOpenSettings={() => {}}
      />
    );

    fireEvent.click(screen.getByText('Test Conv 2'));
    expect(onSelect).toHaveBeenCalledWith('2');
  });

  it('shows no conversations message when list is empty', () => {
    render(
      <Sidebar 
        conversations={[]} 
        currentConversationId={null}
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
        onDeleteConversation={() => {}}
        onOpenSettings={() => {}}
      />
    );

    expect(screen.getByText('No conversations yet')).toBeInTheDocument();
  });
});

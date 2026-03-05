import React, { useEffect, useRef, useState } from 'react';
import type { Message } from '../modules/types';
import MessageItem from './MessageItem';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  userAvatarUrl?: string;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isStreaming, userAvatarUrl }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  useEffect(() => {
    if (!autoScrollEnabled) return;
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [autoScrollEnabled, messages, isStreaming]);

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto p-4 scroll-smooth min-h-0"
      onScroll={() => {
        const el = containerRef.current;
        if (!el) return;
        const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
        setAutoScrollEnabled(distanceToBottom < 120);
      }}
    >
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-gray-400">
          <p className="text-lg">Start a conversation...</p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageItem key={msg.id || index} message={msg} userAvatarUrl={userAvatarUrl} />
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;

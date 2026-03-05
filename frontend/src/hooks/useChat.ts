import { useCallback, useState } from 'react';

import { v4 as uuidv4 } from 'uuid';

import { streamChat } from '../modules/chatService';
import type { ChatMessageRecord, ChatRequest, Message } from '../modules/types';

export const useChat = () => {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMessages = useCallback((records: ChatMessageRecord[], nextSessionId: number | null) => {
    setSessionId(nextSessionId);
    setMessages(
      records.map((r) => ({
        id: String(r.id),
        role: r.role,
        content: r.content,
        content_blocks: r.content_blocks || undefined,
        references: r.references || undefined,
        timestamp: r.created_at,
      }))
    );
    setError(null);
  }, []);

  const resetChat = useCallback(() => {
    setSessionId(null);
    setMessages([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(
    async (text: string, file?: File, kbId?: number | null, documentIds?: number[]) => {
      setIsStreaming(true);
      setError(null);

      const userMsgId = uuidv4();
      const newUserMessage: Message = {
        id: userMsgId,
        role: 'user',
        content: text,
        content_blocks: [{ type: 'text', content: text }],
      };

      if (file) {
        if (file.type.startsWith('image/')) {
          const base64 = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.readAsDataURL(file);
          });
          newUserMessage.content_blocks?.unshift({ type: 'image', content: base64 });
        } else if (file.type.startsWith('audio/')) {
          const base64 = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.readAsDataURL(file);
          });
          newUserMessage.content_blocks?.unshift({ type: 'audio', content: base64 });
        } else if (file.type === 'application/pdf') {
          newUserMessage.content += `\n[Uploaded PDF: ${file.name}]`;
        }
      }

      const assistantMsgId = uuidv4();
      setMessages((prev) => [
        ...prev,
        newUserMessage,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: '',
        },
      ]);

      const request: ChatRequest = {
        session_id: sessionId ?? undefined,
        content_blocks: [{ type: 'text', content: text }],
        history: [],
        image_file: file?.type.startsWith('image/') ? file : undefined,
        audio_file: file?.type.startsWith('audio/') ? file : undefined,
        pdf_file: file?.type === 'application/pdf' ? file : undefined,
        kb_id: kbId ?? undefined,
        document_ids: documentIds,
      };

      try {
        await streamChat(request, (event) => {
          if (event.type === 'session' && event.session_id != null) {
            setSessionId(event.session_id);
          }

          if (event.type === 'content_delta') {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === assistantMsgId) {
                  return { ...msg, content: msg.content + (event.content || '') };
                }
                return msg;
              })
            );
            return;
          }

          if (event.type === 'message_complete') {
            if (event.references) {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id === assistantMsgId) {
                    return { ...msg, references: event.references };
                  }
                  return msg;
                })
              );
            }
            setIsStreaming(false);
            return;
          }

          if (event.type === 'error') {
            setError(event.error || 'Unknown error');
            setIsStreaming(false);
          }
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setIsStreaming(false);
      }
    },
    [sessionId]
  );

  return {
    sessionId,
    messages,
    isStreaming,
    error,
    setSessionId,
    loadMessages,
    resetChat,
    sendMessage,
  };
};

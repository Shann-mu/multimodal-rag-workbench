import type { ContentBlock, Message, StreamEvent, ChatRequest, Reference } from '../modules/types';

import { getAccessToken } from './authToken';

const API_BASE_URL = '/api';

export async function streamChat(
  request: ChatRequest,
  onChunk: (event: StreamEvent) => void
): Promise<void> {
  const formData = new FormData();

  if (request.session_id != null) {
    formData.append('session_id', String(request.session_id));
  }

  if (request.kb_id != null) {
    formData.append('kb_id', String(request.kb_id));
  }

  if (request.document_ids && request.document_ids.length > 0) {
    formData.append('document_ids', JSON.stringify(request.document_ids));
  }

  if (request.image_file) formData.append('image_file', request.image_file);
  if (request.audio_file) formData.append('audio_file', request.audio_file);
  if (request.pdf_file) formData.append('pdf_file', request.pdf_file);

  formData.append('content_blocks', JSON.stringify(request.content_blocks));

  const historyForBackend = request.history.map(msg => ({
    role: msg.role,
    content: msg.content,
    content_blocks: msg.content_blocks || []
  }));
  formData.append('history', JSON.stringify(historyForBackend));

  const token = getAccessToken();

  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: formData,
    });

    if (!response.ok) {
        // Try to read error message
        const text = await response.text();
        throw new Error(`Server error (${response.status}): ${text}`);
    }

    if (!response.body) throw new Error('Response body is null');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      
      const lines = buffer.split('\n');
      // Keep the last part which might be incomplete
      buffer = lines.pop() || ''; 

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        
        const prefix = trimmed.startsWith('data:') ? 'data:' : '';
        if (prefix) {
          const jsonStr = trimmed.replace(/^data:\s?/, '');
          try {
            const data = JSON.parse(jsonStr) as StreamEvent;
            onChunk(data);
          } catch (e) {
            console.error('JSON parse error:', e, jsonStr);
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
    onChunk({
      type: 'error',
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

export type { ContentBlock, Message, StreamEvent, ChatRequest, Reference };

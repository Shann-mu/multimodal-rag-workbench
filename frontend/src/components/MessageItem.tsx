import React from 'react';
import type { Message } from '../modules/types';
import ReactMarkdown from 'react-markdown';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import { Avatar, Tooltip } from 'antd';
import clsx from 'clsx';

interface MessageItemProps {
  message: Message;
  userAvatarUrl?: string;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, userAvatarUrl }) => {
  const isUser = message.role === 'user';

  return (
    <div className={clsx("flex gap-3 mb-6", isUser ? "flex-row-reverse" : "flex-row")}>
      <Avatar
        src={isUser ? userAvatarUrl : undefined}
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        className={clsx("flex-shrink-0", isUser ? "bg-blue-500" : "bg-green-500")}
      />
      <div className={clsx(
        "max-w-[80%] rounded-lg p-3 shadow-sm",
        isUser ? "bg-blue-50 text-white" : "bg-white border border-gray-200"
      )}>
        <div className={clsx("markdown-body text-sm", isUser ? "text-gray-800" : "text-gray-800")}>
          {/* Handle content blocks if present, otherwise just content */}
           {message.content_blocks && message.content_blocks.length > 0 ? (
             <div>
               {message.content_blocks.map((block, idx) => (
                 <div key={idx} className="mb-2">
                   {block.type === 'image' && (
                     <img src={block.content} alt="User Upload" className="max-w-full h-auto rounded mb-2 max-h-60" />
                   )}
                   {block.type === 'audio' && (
                     <audio controls src={block.content} className="w-full mb-2" />
                   )}
                   {block.type === 'text' && (
                     <p className="whitespace-pre-wrap">{block.content}</p>
                   )}
                 </div>
               ))}
             </div>
           ) : (
             <ReactMarkdown 
                components={{
                  // Add custom styling for markdown elements if needed
                  p: ({ node, ...props }) => {
                    void node;
                    return <p className="mb-2 last:mb-0" {...props} />;
                  },
                  a: ({ node, ...props }) => {
                    void node;
                    return <a className="text-blue-600 hover:underline" {...props} />;
                  },
                  code: ({ node, ...props }) => {
                    void node;
                    return <code className="bg-gray-100 rounded px-1 py-0.5 text-sm font-mono" {...props} />;
                  },
                  pre: ({ node, ...props }) => {
                    void node;
                    return <pre className="bg-gray-100 rounded p-2 overflow-x-auto text-sm font-mono mb-2" {...props} />;
                  },
                }}
             >
               {message.content}
             </ReactMarkdown>
           )}
        </div>
        
        {/* Render references if available */}
        {message.references && message.references.length > 0 && (
          <div className="mt-3 pt-2 border-t border-gray-200 text-xs text-gray-500">
            <div className="font-semibold mb-1">References:</div>
            <div className="flex flex-wrap gap-2">
              {message.references.map((ref) => (
                <Tooltip key={ref.id} title={
                  <div>
                    {ref.document_id && <div className="font-bold border-b border-gray-500 mb-1 pb-1">Doc ID: {ref.document_id}</div>}
                    <div className="text-xs">{ref.text}</div>
                  </div>
                }>
                  <div className="bg-gray-100 px-2 py-1 rounded cursor-help flex items-center gap-1">
                    <span className="font-mono text-gray-400">[{ref.id}]</span>
                    <span>{ref.source_info}</span>
                    {ref.document_id && (
                      <span className="bg-blue-100 text-blue-600 px-1 rounded scale-90">Doc:{ref.document_id}</span>
                    )}
                    <span className="text-gray-400 ml-1">(P{ref.page})</span>
                  </div>
                </Tooltip>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageItem;

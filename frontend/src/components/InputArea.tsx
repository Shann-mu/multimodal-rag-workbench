import React, { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface InputAreaProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const InputArea: React.FC<InputAreaProps> = ({ onSend, disabled, placeholder }) => {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-white border-t border-gray-200">
      <div className="flex gap-2 items-end">
        <TextArea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "Type your message..."}
          autoSize={{ minRows: 1, maxRows: 6 }}
          disabled={disabled}
          className="resize-none"
        />
        <Button 
          type="primary" 
          icon={<SendOutlined />} 
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="flex-shrink-0 mb-0.5"
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default InputArea;

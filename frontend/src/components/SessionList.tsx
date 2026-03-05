import React from 'react';

import { Button, List, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

import type { ChatSession } from '../modules/types';

const { Text } = Typography;

interface SessionListProps {
  sessions: ChatSession[];
  selectedSessionId: number | null;
  loading: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
}

const SessionList: React.FC<SessionListProps> = ({ sessions, selectedSessionId, loading, onSelect, onNew }) => {
  return (
    <div className="h-full bg-white border border-gray-200 rounded-lg overflow-hidden flex flex-col">
      <div className="px-3 py-2 border-b border-gray-200 flex items-center justify-between">
        <Text strong>会话</Text>
        <Button size="small" icon={<PlusOutlined />} onClick={onNew}>
          新建
        </Button>
      </div>

      <div className="flex-1 overflow-auto px-2">
        <List
          loading={loading}
          dataSource={sessions}
          renderItem={(item) => {
            const active = item.id === selectedSessionId;
            return (
              <List.Item
                className={active ? 'bg-blue-50 cursor-pointer' : 'cursor-pointer'}
                style={{ paddingInline: 16 }}
                onClick={() => onSelect(item.id)}
              >
                <div className="w-full">
                  <div className="text-sm font-medium truncate">{item.title}</div>
                  <div className="text-xs text-gray-500 truncate">
                    {item.is_default ? '默认会话' : item.mode} · {new Date(item.updated_at).toLocaleString()}
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      </div>
    </div>
  );
};

export default SessionList;
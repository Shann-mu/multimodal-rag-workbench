import React from 'react';
import { Upload, Button } from 'antd';
import { UploadOutlined, DeleteOutlined, FilePdfOutlined, FileImageOutlined, AudioOutlined } from '@ant-design/icons';

interface FileUploaderProps {
  accept: string;
  onFileSelect: (file: File) => void;
  onClear: () => void;
  selectedFile: File | null;
  type: 'image' | 'audio' | 'pdf';
}

const FileUploader: React.FC<FileUploaderProps> = ({ accept, onFileSelect, onClear, selectedFile, type }) => {
  const handleUpload = (file: File) => {
    // Validate file type based on accept
    // This is handled by 'accept' prop in Upload but good to double check if needed
    onFileSelect(file);
    return false; // Prevent automatic upload
  };

  const getIcon = () => {
    switch (type) {
      case 'image': return <FileImageOutlined />;
      case 'audio': return <AudioOutlined />;
      case 'pdf': return <FilePdfOutlined />;
      default: return <UploadOutlined />;
    }
  };

  const getLabel = () => {
    switch (type) {
      case 'image': return 'Upload Image';
      case 'audio': return 'Upload Audio';
      case 'pdf': return 'Upload PDF';
      default: return 'Upload File';
    }
  };

  return (
    <div className="mb-4">
      {!selectedFile ? (
        <Upload
          accept={accept}
          beforeUpload={handleUpload}
          showUploadList={false}
          maxCount={1}
        >
          <Button icon={getIcon()}>{getLabel()}</Button>
        </Upload>
      ) : (
        <div className="flex items-center gap-2 p-2 border rounded bg-gray-50 inline-flex">
          {getIcon()}
          <span className="text-sm truncate max-w-[200px]">{selectedFile.name}</span>
          <Button 
            type="text" 
            size="small" 
            icon={<DeleteOutlined />} 
            onClick={onClear} 
            danger
          />
        </div>
      )}
    </div>
  );
};

export default FileUploader;

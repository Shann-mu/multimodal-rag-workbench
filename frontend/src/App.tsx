import { Suspense, lazy } from 'react';

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';

import RequireAuth from './components/RequireAuth';

const Home = lazy(() => import('./pages/Home'));
const ChatContainer = lazy(() => import('./pages/ChatContainer'));
const Login = lazy(() => import('./pages/Login'));

const ChatPage = () => <ChatContainer title="Smart QA" type="text" />;
const ImagePage = () => <ChatContainer title="Image Analysis" type="image" fileAccept="image/*" />;
const AudioPage = () => <ChatContainer title="Audio Transcribe" type="audio" fileAccept="audio/*" />;
const PDFPage = () => <ChatContainer title="PDF Parsing" type="pdf" fileAccept=".pdf" />;

const Loading = () => (
  <div className="h-screen w-full flex items-center justify-center">
    <Spin size="large" tip="Loading..." />
  </div>
);

function App() {
  return (
    <Router>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<RequireAuth />}>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/image-analysis" element={<ImagePage />} />
            <Route path="/audio-transcribe" element={<AudioPage />} />
            <Route path="/pdf-qa" element={<PDFPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;

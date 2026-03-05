import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
// Import Ant Design styles if not using a specific theme configuration that auto-injects
// With Vite and modern Antd, usually just importing components is enough or configuration in ConfigProvider
// But for some setups, we might need 'antd/dist/reset.css'
import 'antd/dist/reset.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

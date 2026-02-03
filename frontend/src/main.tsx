// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider, theme } from 'antd'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm, // Enables Dark Mode
        token: {
          colorPrimary: '#646cff', // Match Vite brand color
        },
      }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>,
)
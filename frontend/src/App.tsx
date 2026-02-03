// frontend/src/App.tsx
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Typography, Button } from 'antd';
import { SettingOutlined, HomeOutlined } from '@ant-design/icons';
import { Dashboard } from './pages/Dashboard';
import { SettingsPage } from './pages/SettingsPage';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

// Helper component to conditionally render the correct header button
const HeaderActions = () => {
  const location = useLocation();
  const isSettings = location.pathname === '/settings';

  return (
    <div>
      {isSettings ? (
        <Link to="/">
          <Button type="text" icon={<HomeOutlined />} style={{ color: 'white' }}>
            Dashboard
          </Button>
        </Link>
      ) : (
        <Link to="/settings">
          <Button type="text" icon={<SettingOutlined style={{ fontSize: '20px' }} />} style={{ color: 'white' }} />
        </Link>
      )}
    </div>
  );
};

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
        
        {/* TOP BAR */}
        <Header style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            background: '#1a1a1a', 
            padding: '0 20px' 
        }}>
          <Title level={3} style={{ margin: 0, color: 'white' }}>Skyrocket 🚀</Title>
          <HeaderActions />
        </Header>
        
        {/* MAIN CONTENT AREA */}
        <Content style={{ padding: '30px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Content>

        <Footer style={{ textAlign: 'center', background: 'transparent' }}>
          Skyrocket Trading Bot ©{new Date().getFullYear()}
        </Footer>
      </Layout>
    </Router>
  )
}

export default App;
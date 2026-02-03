// frontend/src/App.tsx
import { useState } from 'react'
import { Layout, Button, Card, Typography } from 'antd'
import './App.css'

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

function App() {
  const [count, setCount] = useState(0)

  return (
    <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
      <Header style={{ display: 'flex', alignItems: 'center', background: '#1a1a1a', padding: '0 20px' }}>
        <Title level={3} style={{ margin: 0, color: 'white' }}>Skyrocket 🚀</Title>
      </Header>
      
      <Content style={{ padding: '50px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Card title="Control Panel" style={{ width: 400 }}>
          <div style={{ textAlign: 'center' }}>
            <Paragraph>
              Current Count: <strong>{count}</strong>
            </Paragraph>
            
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <Button type="primary" onClick={() => setCount((c) => c + 1)}>
                Increase
              </Button>
              <Button danger onClick={() => setCount(0)}>
                Reset tr
              </Button>
            </div>
          </div>
        </Card>
      </Content>

      <Footer style={{ textAlign: 'center', background: 'transparent' }}>
        Skyrocket Trading Bot ©{new Date().getFullYear()}
      </Footer>
    </Layout>
  )
}

export default App
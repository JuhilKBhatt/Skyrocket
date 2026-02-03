import { Card, Row, Col, InputNumber, Typography, Button, Form, Divider } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { CompanySettingsTable } from '../components/CompanySettingsTable.jsx';

const { Text, Title } = Typography;

export const SettingsPage = () => {
  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      
      {/* HEADER ACTIONS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={2} style={{ margin: 0, color: 'white' }}>Settings</Title>
        <Button type="primary" icon={<SaveOutlined />}>
          Save Changes
        </Button>
      </div>

      {/* SECTION 1: GLOBAL RISK MANAGEMENT */}
      <Card title="Global Risk Parameters" style={{ marginBottom: 20 }}>
        <Form layout="vertical">
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item 
                label={<Text strong>Global Stop Loss (%)</Text>} 
                extra="Trade will auto-close if price drops by this %"
              >
                <InputNumber 
                  defaultValue={5} 
                  min={1} 
                  max={50} 
                  formatter={(value) => `${value}%`}
                  style={{ width: '100%' }} 
                />
              </Form.Item>
            </Col>
            
            <Col span={12}>
              <Form.Item 
                label={<Text strong>Max Trade Allocation (%)</Text>} 
                extra="Percentage of total equity to use per single trade"
              >
                <InputNumber 
                  defaultValue={2} 
                  min={0.1} 
                  max={100} 
                  step={0.1}
                  formatter={(value) => `${value}%`}
                  style={{ width: '100%' }} 
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {/* SECTION 2: COMPANY WATCHLIST */}
      <Card title="Watchlist Configuration">
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">
            Manage the list of companies the bot is allowed to trade and their individual concurrency limits.
          </Text>
        </div>
        <CompanySettingsTable />
      </Card>

    </div>
  );
};
import { useState, useEffect } from 'react';
import { Card, Row, Col, InputNumber, Typography, Button, Form, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { CompanySettingsTable } from '../components/CompanySettingsTable';
import { settingsApi } from '../services/settingsApi';

const { Text, Title } = Typography;

const MIN_STOP_LOSS_PCT = 1;
const MAX_STOP_LOSS_PCT = 50;
const MIN_TAKE_PROFIT_PCT = 1;
const MAX_TAKE_PROFIT_PCT = 200;
const MIN_TRADE_ALLOCATION_PCT = 0.1;
const MAX_TRADE_ALLOCATION_PCT = 100;

export const SettingsPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    settingsApi.getGlobalSettings()
      .then(data => {
        form.setFieldsValue({
            global_stop_loss_pct: data.global_stop_loss_pct,
            take_profit_pct: data.take_profit_pct,
            max_trade_allocation_pct: data.max_trade_allocation_pct
        });
      })
      .catch(() => {
        message.error("Failed to load global settings");
      });
  }, [form]);

  const handleSave = async () => {
    try {
        setLoading(true);
        const values = form.getFieldsValue();
        const payload = {
            ...values,
            is_trading_enabled: true 
        };
        await settingsApi.updateGlobalSettings(payload);
        message.success("Global settings saved successfully!");
    } catch (e) {
        console.error("Error saving settings:", e);
        message.error("Error saving settings");
    } finally {
        setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={2} style={{ margin: 0, color: 'white' }}>Settings</Title>
        <Button 
            type="primary" 
            icon={<SaveOutlined />} 
            onClick={handleSave} 
            loading={loading}
        >
          Save Changes
        </Button>
      </div>

      <Card title="Global Risk Parameters" style={{ marginBottom: 20 }}>
        <Form form={form} layout="vertical">
          <Row gutter={24}>
            <Col span={8}>
              <Form.Item 
                name="global_stop_loss_pct"
                label={<Text strong>Global Stop Loss (%)</Text>} 
                extra="Auto-close if price drops by this %"
              >
                <InputNumber<number> 
                  min={MIN_STOP_LOSS_PCT} max={MAX_STOP_LOSS_PCT} 
                  formatter={(value) => `${value}%`}
                  parser={(value) => Number.parseFloat(value?.replace('%', '') || '0')}
                  style={{ width: '100%' }} 
                />
              </Form.Item>
            </Col>
            
            <Col span={8}>
              <Form.Item 
                name="take_profit_pct"
                label={<Text strong>Take Profit (%)</Text>} 
                extra="Auto-close if price rises by this %"
              >
                <InputNumber<number> 
                  min={MIN_TAKE_PROFIT_PCT} max={MAX_TAKE_PROFIT_PCT} 
                  formatter={(value) => `${value}%`}
                  parser={(value) => Number.parseFloat(value?.replace('%', '') || '0')}
                  style={{ width: '100%' }} 
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item 
                name="max_trade_allocation_pct"
                label={<Text strong>Max Trade Allocation (%)</Text>} 
                extra="% of equity per trade"
              >
                <InputNumber<number> 
                  min={MIN_TRADE_ALLOCATION_PCT} max={MAX_TRADE_ALLOCATION_PCT} step={0.1}
                  formatter={(value) => `${value}%`}
                  parser={(value) => Number.parseFloat(value?.replace('%', '') || '0')}
                  style={{ width: '100%' }} 
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card title="Watchlist Configuration">
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">
            Manage the list of companies the bot is allowed to trade.
          </Text>
        </div>
        <CompanySettingsTable />
      </Card>
    </div>
  );
};
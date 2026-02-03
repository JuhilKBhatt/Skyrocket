import { Row, Col, Statistic, Card } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { ActiveTradesList } from '../components/ActiveTradesList';
import { TradeHistoryList } from '../components/TradeHistoryList';

export const Dashboard = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* SECTION 1: Total Investment (Centered) */}
      <Row justify="center" style={{ marginBottom: '20px', textAlign: 'center' }}>
        <Col>
          <Statistic title="Total Investment Value" value={125430} prefix="$" />
        </Col>
      </Row>

      {/* SECTION 2: Percentage Changes */}
      <Row gutter={16} justify="center" style={{ marginBottom: '40px' }}>
        <Col span={8} style={{ textAlign: 'center' }}>
          <Card variant="borderless">
            <Statistic
              title="Change (Yesterday)"
              value={1.2}
              precision={2}
              style={{ color: '#3f8600' }}
              prefix={<ArrowUpOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={8} style={{ textAlign: 'center' }}>
          <Card variant="borderless">
            <Statistic
              title="Change (Today)"
              value={0.5}
              precision={2}
              style={{ color: '#cf1322' }}
              prefix={<ArrowDownOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* SECTION 3: The Split View Boxes */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <ActiveTradesList />
        </Col>
        <Col xs={24} md={12}>
          <TradeHistoryList />
        </Col>
      </Row>
    </div>
  );
};
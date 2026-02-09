// src/pages/Dashboard.tsx
import { useEffect, useState } from 'react';
import { Row, Col, Statistic, Card } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { ActiveTradesList } from '../components/ActiveTradesList';
import { TradeHistoryList } from '../components/TradeHistoryList';
import { tradesApi } from '../services/tradesApi';

export const Dashboard = () => {
  const [stats, setStats] = useState({
    total_investment: 0,
    day_change_pct: 0,
    yesterday_change_pct: 0,
  });

  useEffect(() => {
    const fetchStats = () => tradesApi.getStats().then(setStats);
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Refresh stats every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* SECTION 1: Total Investment */}
      <Row justify="center" style={{ marginBottom: '20px', textAlign: 'center' }}>
        <Col>
          <Statistic 
            title="Total Investment Value" 
            value={stats.total_investment} 
            prefix="$" 
            precision={2} 
          />
        </Col>
      </Row>

      {/* SECTION 2: Percentage Changes */}
      <Row gutter={16} justify="center" style={{ marginBottom: '40px' }}>
        <Col span={8} style={{ textAlign: 'center' }}>
          <Card variant="borderless">
            <Statistic
              title="Change (Yesterday)"
              value={Math.abs(stats.yesterday_change_pct)}
              precision={2}
              styles={{ content: { color: stats.yesterday_change_pct >= 0 ? '#3f8600' : '#cf1322' } }}
              prefix={stats.yesterday_change_pct >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={8} style={{ textAlign: 'center' }}>
          <Card variant="borderless">
            <Statistic
              title="Change (Today)"
              value={Math.abs(stats.day_change_pct)}
              precision={2}
              styles={{ content: { color: stats.day_change_pct >= 0 ? '#3f8600' : '#cf1322' } }}
              prefix={stats.day_change_pct >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* SECTION 3: Split View */}
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
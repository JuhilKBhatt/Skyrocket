// src/pages/BacktestPage.tsx
import { useState } from 'react';
import { Card, Row, Col, Input, Button, Statistic, Typography, message, Divider } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import { backtestApi } from '../services/backtestApi';
import type { BacktestResult } from '../services/backtestApi';
import { BacktestChart } from '../components/BacktestChart';

const { Title, Text } = Typography;
const { Search } = Input;

export const BacktestPage = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);

  const onSearch = async (ticker: string) => {
    if (!ticker) return;
    setLoading(true);
    try {
      const data = await backtestApi.runBacktest(ticker);
      setResults(data);
      message.success(`Backtest completed for ${ticker.toUpperCase()}`);
    } catch (error: any) {
      message.error(error.message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2} style={{ color: 'white' }}>Algorithm Backtester</Title>
      
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={16}>
          <Col flex="auto">
            <Search
              placeholder="Enter Ticker Symbol (e.g. AAPL, TSLA)"
              allowClear
              enterButton="Run Analysis"
              size="large"
              onSearch={onSearch}
              loading={loading}
            />
          </Col>
        </Row>
      </Card>

      {results && (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Return"
                  value={results.summary.total_return_pct}
                  suffix="%"
                  precision={2}
                  styles={{
                    content: {
                      color: results.summary.total_return_pct >= 0 ? '#3f8600' : '#cf1322'
                    }
                  }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Win Rate" value={results.summary.win_rate} suffix="%" precision={2} /></Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Total Trades" value={results.summary.total_trades} /></Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Final Balance" value={results.summary.final_balance} prefix="$" precision={2} /></Card>
            </Col>
          </Row>

          <BacktestChart data={results.chart_data} trades={results.trades} />
        </>
      )}
    </div>
  );
};
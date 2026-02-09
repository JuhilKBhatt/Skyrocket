// src/components/TradeHistoryList.tsx
import { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag } from 'antd';
import { tradesApi } from '../services/tradesApi';
import type { TradeType } from '../services/tradesApi';

const { Text } = Typography;

export const TradeHistoryList = () => {
  const [history, setHistory] = useState<TradeType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tradesApi.getHistory()
      .then(data => {
        setHistory(data);
        setLoading(false);
      })
      .catch(err => console.error("Failed to load history:", err));
  }, []);

  const columns = [
    {
      title: 'Ticker',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string, record: TradeType) => (
        <div>
            <Text strong>{text}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.exit_time ? new Date(record.exit_time).toLocaleDateString() : 'N/A'}
            </Text>
        </div>
      )
    },
    {
      title: 'PnL',
      key: 'pnl',
      align: 'right' as const,
      render: (_: any, record: TradeType) => {
        const pnl = record.pnl || 0;
        const pnlPct = record.pnl_percent || 0;
        return (
          <div>
            <Text type={pnl >= 0 ? 'success' : 'danger'} style={{ display: 'block' }}>
              {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
            </Text>
            <Tag color={pnlPct >= 0 ? 'green' : 'red'} style={{ marginRight: 0 }}>
              {pnlPct.toFixed(2)}%
            </Tag>
          </div>
        );
      },
    },
  ];

  return (
    <Card title="Trade History" style={{ height: '100%' }}>
      <Table 
        dataSource={history} 
        columns={columns} 
        rowKey="id" 
        pagination={{ pageSize: 5 }}
        loading={loading}
        size="small"
      />
    </Card>
  );
};
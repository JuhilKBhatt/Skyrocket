// src/components/ActiveTradesList.tsx
import { useEffect, useState } from 'react';
import { Card, Table, Tag, Typography } from 'antd';
import { tradesApi } from '../services/tradesApi';
import type { TradeType } from '../services/tradesApi';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

export const ActiveTradesList = () => {
  const [data, setData] = useState<TradeType[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchActiveTrades = async () => {
    try {
      const trades = await tradesApi.getActiveTrades();
      setData(trades);
    } catch (error) {
      console.error("Failed to fetch active trades:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveTrades();
    const interval = setInterval(fetchActiveTrades, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const columns: ColumnsType<TradeType> = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Entry Price',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (value) => `$${value.toFixed(2)}`,
    },
    {
      title: 'PnL %',
      dataIndex: 'pnl_percent',
      key: 'pnl_percent',
      render: (value) => {
        const pct = value || 0;
        return (
          <Tag color={pct >= 0 ? 'green' : 'red'}>
            {pct.toFixed(2)}%
          </Tag>
        );
      },
    },
  ];

  return (
    <Card title="Active Trades" style={{ height: '100%' }}>
      <Table 
        dataSource={data} 
        columns={columns} 
        rowKey="id" 
        pagination={false} 
        loading={loading}
        size="small"
        bordered
      />
    </Card>
  );
};
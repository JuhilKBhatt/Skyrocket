// frontend/src/components/ActiveTradesList.tsx
import { Card, List, Tag, Typography } from 'antd';

const { Text } = Typography;

const data = [
  { symbol: 'AAPL', entry: 150.50, current: 155.20, pnl: '+3.1%' },
  { symbol: 'TSLA', entry: 210.00, current: 205.50, pnl: '-2.1%' },
];

export const ActiveTradesList = () => {
  return (
    <Card title="Active Trades" style={{ height: '100%' }}>
      <List
        itemLayout="horizontal"
        dataSource={data}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={<Text strong>{item.symbol}</Text>}
              description={`Entry: $${item.entry}`}
            />
            <Tag color={item.pnl.includes('+') ? 'green' : 'red'}>
              {item.pnl}
            </Tag>
          </List.Item>
        )}
      />
    </Card>
  );
};
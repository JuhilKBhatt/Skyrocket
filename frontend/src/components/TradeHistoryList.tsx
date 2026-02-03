// frontend/src/components/TradeHistoryList.tsx
import { Card, List, Typography } from 'antd';

const { Text } = Typography;

const data = [
  { symbol: 'MSFT', exit: 310.00, profit: '+$450', date: '2023-10-01' },
  { symbol: 'GOOGL', exit: 135.00, profit: '-$120', date: '2023-09-28' },
];

export const TradeHistoryList = () => {
  return (
    <Card title="Trade History" style={{ height: '100%' }}>
      <List
        itemLayout="horizontal"
        dataSource={data}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={<Text>{item.symbol}</Text>}
              description={item.date}
            />
            <Text type={item.profit.includes('+') ? 'success' : 'danger'}>
              {item.profit}
            </Text>
          </List.Item>
        )}
      />
    </Card>
  );
};
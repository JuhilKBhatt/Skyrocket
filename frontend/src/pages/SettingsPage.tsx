import { List, Switch, Card, Typography, Button, Tag } from 'antd';

const { Text } = Typography;

export const SettingsPage = () => {
  const data = [
    { title: 'Enable Auto-Trading', action: <Switch defaultChecked /> },
    { title: 'Dark Mode', action: <Switch defaultChecked disabled /> }, // Controlled by main.tsx
    { title: 'Risk Per Trade', action: <Text>2%</Text> },
    { title: 'API Connection', action: <Tag color="green">Connected</Tag> },
  ];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <Card title="Bot Configuration">
        <List
          itemLayout="horizontal"
          dataSource={data}
          renderItem={(item) => (
            <List.Item actions={[item.action]}>
              <List.Item.Meta
                title={item.title}
                description="Manage your bot parameters here"
              />
            </List.Item>
          )}
        />
        <div style={{ marginTop: 20, textAlign: 'right' }}>
            <Button danger>Reset All Settings</Button>
        </div>
      </Card>
    </div>
  );
};
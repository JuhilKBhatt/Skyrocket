import { useState } from 'react';
import { Table, Tag, InputNumber, Button, Modal, Form, Input, Popconfirm } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface CompanyDataType {
  key: string;
  name: string;
  ticker: string;
  concurrentTrades: number;
}

const initialData: CompanyDataType[] = [
  { key: '1', name: 'Apple Inc.', ticker: 'AAPL', concurrentTrades: 2 },
  { key: '2', name: 'Tesla, Inc.', ticker: 'TSLA', concurrentTrades: 1 },
  { key: '3', name: 'NVIDIA Corp.', ticker: 'NVDA', concurrentTrades: 3 },
  { key: '4', name: 'Microsoft Corp.', ticker: 'MSFT', concurrentTrades: 2 },
];

export const CompanySettingsTable = () => {
  const [dataSource, setDataSource] = useState<CompanyDataType[]>(initialData);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  // Function to delete a row
  const handleDelete = (key: string) => {
    const newData = dataSource.filter((item) => item.key !== key);
    setDataSource(newData);
  };

  // Function to add a new row
  const handleAdd = (values: any) => {
    const newData: CompanyDataType = {
      key: Date.now().toString(), // Simple unique ID
      name: values.name,
      ticker: values.ticker.toUpperCase(),
      concurrentTrades: values.concurrentTrades || 1,
    };
    setDataSource([...dataSource, newData]);
    setIsModalOpen(false);
    form.resetFields();
  };

  const columns: ColumnsType<CompanyDataType> = [
    {
      title: 'Ticker',
      dataIndex: 'ticker',
      key: 'ticker',
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Company Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Max Concurrent Trades',
      dataIndex: 'concurrentTrades',
      key: 'concurrentTrades',
      render: (value, record) => (
        <InputNumber 
          min={1} 
          max={10} 
          defaultValue={value}
          // Optional: Update state on change if you want to save this edit
          onChange={(val) => {
            record.concurrentTrades = val || 1; 
          }}
        />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Popconfirm title="Sure to remove?" onConfirm={() => handleDelete(record.key)}>
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      {/* Add Button aligned to the right */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          Add Company
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={dataSource} 
        pagination={false} 
        bordered
        size="middle"
      />

      {/* Modal for Adding New Company */}
      <Modal 
        title="Add Company to Watchlist" 
        open={isModalOpen} 
        onOk={() => form.submit()} 
        onCancel={() => setIsModalOpen(false)}
      >
        <Form form={form} layout="vertical" onFinish={handleAdd}>
          <Form.Item 
            name="name" 
            label="Company Name" 
            rules={[{ required: true, message: 'Please input company name' }]}
          >
            <Input placeholder="e.g. Amazon" />
          </Form.Item>
          
          <Form.Item 
            name="ticker" 
            label="Ticker Symbol" 
            rules={[{ required: true, message: 'Please input ticker' }]}
          >
            <Input placeholder="e.g. AMZN" style={{ textTransform: 'uppercase' }} />
          </Form.Item>

          <Form.Item 
            name="concurrentTrades" 
            label="Max Concurrent Trades" 
            initialValue={1}
          >
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
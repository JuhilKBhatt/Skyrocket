import { useState, useEffect } from 'react';
import { Table, Tag, InputNumber, Button, Popconfirm, message } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { settingsApi } from '../services/settingsApi';
import type { CompanyDataType } from '../services/settingsApi';
import { AddCompanyModal } from './AddCompanyModal.tsx';

export const CompanySettingsTable = () => {
  const [dataSource, setDataSource] = useState<CompanyDataType[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchWatchlist = async () => {
    try {
      const data = await settingsApi.getWatchlist();
      setDataSource(data);
    } catch (error) {
      message.error("Failed to load watchlist");
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAdd = async (values: any) => {
    try {
      const payload: CompanyDataType = {
        ticker: values.ticker.toUpperCase(),
        company_name: values.name,
        max_concurrent_trades: values.concurrentTrades || 1,
        is_active: true
      };
      await settingsApi.addCompany(payload);
      message.success("Company added!");
      setIsModalOpen(false);
      fetchWatchlist();
    } catch (error) {
      message.error("Could not add company. Ticker might exist.");
    }
  };

  const handleDelete = async (ticker: string) => {
    try {
      await settingsApi.deleteCompany(ticker);
      message.success("Company removed");
      fetchWatchlist();
    } catch (error) {
      message.error("Failed to delete");
    }
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
      dataIndex: 'company_name',
      key: 'company_name',
    },
    {
      title: 'Max Concurrent Trades',
      dataIndex: 'max_concurrent_trades',
      key: 'max_concurrent_trades',
      render: (value) => <InputNumber min={1} max={10} defaultValue={value} disabled />,
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Popconfirm title="Remove from watchlist?" onConfirm={() => handleDelete(record.ticker)}>
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          Add Company
        </Button>
      </div>

      <Table 
        rowKey="ticker" 
        columns={columns} 
        dataSource={dataSource} 
        pagination={false} 
        bordered
        size="middle"
      />

      <AddCompanyModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSubmit={handleAdd} 
      />
    </div>
  );
};
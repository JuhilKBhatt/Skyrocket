import { Modal, Form, Input } from 'antd';

interface AddCompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: any) => Promise<void>;
}

export const AddCompanyModal = ({ isOpen, onClose, onSubmit }: AddCompanyModalProps) => {
  const [form] = Form.useForm();

  const handleOk = () => {
    form
      .validateFields()
      .then((values) => {
        onSubmit(values).then(() => {
          form.resetFields();
        });
      })
      .catch((error_) => {
        console.log('Validate Failed:', error_);
      });
  };

  return (
    <Modal
      title="Add Company to Watchlist"
      open={isOpen}
      onOk={handleOk}
      onCancel={onClose}
    >
      <Form form={form} layout="vertical">
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
      </Form>
    </Modal>
  );
};
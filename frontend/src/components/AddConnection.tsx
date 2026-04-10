/**
 * AddConnection Component
 * Form to add a new MySQL server connection
 */
import { useState } from 'react';
import { Form, Input, Button, message, Typography, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { createConnection } from '../services/api';
import type { Connection, ConnectionCreateRequest } from '../types';

const { Text } = Typography;

interface AddConnectionFormProps {
  onSuccess: (connection: Connection) => void;
  existingNames: string[];
  onDelete?: () => void;
}

export function AddConnectionForm({ onSuccess, existingNames, onDelete }: AddConnectionFormProps) {
  const [form] = Form.useForm<ConnectionCreateRequest>();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: ConnectionCreateRequest) => {
    const { name, url } = values;

    if (!name || name.trim() === '') {
      message.error('请输入连接名称');
      return;
    }

    if (existingNames.includes(name)) {
      message.error('连接名称已存在');
      return;
    }

    if (!url || url.trim() === '') {
      message.error('请输入MySQL连接URL');
      return;
    }

    setLoading(true);
    try {
      const response = await createConnection({ name, url });
      const result = response;

      if (result.code === 200) {
        message.success('连接成功!');
        form.resetFields();
        setOpen(false);
        onSuccess({
          id: result.data?.connectionId || 0,
          name: name,
          host: result.data?.host || '',
          port: result.data?.port || 3306,
          username: '',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        });
      } else {
        message.error(result.message || '连接失败');
      }
    } catch (error) {
      message.error('连接失败: ' + String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button
        type="primary"
        className="md-btn-primary"
        icon={<PlusOutlined />}
        loading={loading}
        onClick={() => !open && setOpen(true)}
        style={{ width: '100%', minHeight: 40 }}
      >
        添加连接
      </Button>

      {open && (
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ name: '', url: '' }}
          style={{ marginTop: 12 }}
        >
          <Form.Item label="连接名称" name="name" rules={[{ required: true, message: '请输入连接名称' }]}>
            <Input placeholder="例如: 生产环境 MySQL" />
          </Form.Item>

          <Form.Item
            label="MySQL 连接 URL"
            name="url"
            rules={[{ required: true, message: '请输入MySQL连接URL' }]}
            extra={
              <Text className="md-text-slate" style={{ fontSize: 11 }}>
                格式: mysql://user:password@host:port
              </Text>
            }
          >
            <Input placeholder="mysql://user:password@localhost:3306" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                className="md-btn-primary"
                loading={loading}
                style={{ flex: 1 }}
              >
                确定
              </Button>
              <Button
                onClick={() => {
                  setOpen(false);
                  form.resetFields();
                }}
                className="md-btn-secondary"
                style={{ flex: 1 }}
              >
                取消
              </Button>
            </div>
          </Form.Item>
        </Form>
      )}

      {onDelete && (
        <Popconfirm
          title="确定删除此连接?"
          description="删除后需重新添加才能使用"
          onConfirm={onDelete}
          okText="删除"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <Button danger icon={<DeleteOutlined />} style={{ marginTop: 8, width: '100%', height: 40 }}>
            删除连接
          </Button>
        </Popconfirm>
      )}
    </div>
  );
}

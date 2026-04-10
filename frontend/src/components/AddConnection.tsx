/**
 * AddConnection Component
 * Form to add a new MySQL server connection
 */
import { useState } from 'react';
import { Form, Input, Button, message, Typography, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { createConnection, deleteConnection } from '../services/api';
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
        icon={<PlusOutlined />}
        loading={loading}
        onClick={() => !open && setOpen(true)}
        style={{
          background: 'linear-gradient(135deg, #6B46C1 0%, #805AD5 100%)',
          border: 'none',
          height: 36,
          borderRadius: 8,
          width: '100%',
        }}
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
          <Form.Item
            label={<span style={{ color: '#9CA3AF', fontSize: 12 }}>连接名称</span>}
            name="name"
            rules={[{ required: true, message: '请输入连接名称' }]}
          >
            <Input
              placeholder="例如: 生产环境MySQL"
              style={{
                background: '#232442',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#F9FAFB',
                borderRadius: 8,
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: '#9CA3AF', fontSize: 12 }}>MySQL 连接 URL</span>}
            name="url"
            rules={[{ required: true, message: '请输入MySQL连接URL' }]}
            extra={
              <div style={{ fontSize: 11, color: '#6B7280', marginTop: 4 }}>
                格式: mysql://user:password@host:port
              </div>
            }
          >
            <Input
              placeholder="mysql://root:password@rm-uf6za8t7p16y4q1qcoo.mysql.rds.aliyuncs.com:3306"
              style={{
                background: '#232442',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#F9FAFB',
                borderRadius: 8,
              }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{
                  background: 'linear-gradient(135deg, #6B46C1 0%, #805AD5 100%)',
                  border: 'none',
                  height: 36,
                  borderRadius: 8,
                  flex: 1,
                }}
              >
                确定
              </Button>
              <Button
                onClick={() => { setOpen(false); form.resetFields(); }}
                style={{
                  height: 36,
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#9CA3AF',
                }}
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
          description="删除后所有相关数据将被清除"
          onConfirm={onDelete}
          okText="删除"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <Button
            danger
            icon={<DeleteOutlined />}
            style={{ marginTop: 8, width: '100%', height: 36 }}
          >
            删除连接
          </Button>
        </Popconfirm>
      )}
    </div>
  );
}

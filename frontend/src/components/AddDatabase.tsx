/**
 * AddDatabase Component
 * MotherDuck-style form with dark theme
 */
import { useState } from 'react';
import { Form, Input, Button, message, Typography } from 'antd';
import { PlusOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';
import type { AddDatabaseRequest } from '../types';

const { Text } = Typography;

interface AddDatabaseFormProps {
  onSuccess: (name: string) => void;
  existingNames: string[];
}

export function AddDatabaseForm({ onSuccess, existingNames }: AddDatabaseFormProps) {
  const [form] = Form.useForm<AddDatabaseRequest & { name: string }>();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: AddDatabaseRequest & { name: string }) => {
    const { name, url } = values;

    if (!name || name.trim() === '') {
      message.error('请输入数据库名称');
      return;
    }

    if (existingNames.includes(name)) {
      message.error('数据库名称已存在');
      return;
    }

    if (!url || url.trim() === '') {
      message.error('请输入数据库连接URL');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/dbs/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const result = await response.json();

      if (result.code === 200) {
        message.success('数据库连接添加成功');
        form.resetFields();
        onSuccess(name);
      } else {
        message.error(result.message || '添加失败');
      }
    } catch (error) {
      message.error('添加失败: ' + String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button
        type="primary"
        htmlType="submit"
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
        添加数据库
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
            label={<span style={{ color: '#9CA3AF', fontSize: 12 }}>数据库名称</span>}
            name="name"
            rules={[{ required: true, message: '请输入数据库名称' }]}
          >
            <Input
              placeholder="例如: test_db"
              style={{
                background: '#232442',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#F9FAFB',
                borderRadius: 8,
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: '#9CA3AF', fontSize: 12 }}>连接 URL</span>}
            name="url"
            rules={[{ required: true, message: '请输入数据库连接URL' }]}
            extra={
              <div style={{ fontSize: 11, color: '#6B7280', marginTop: 4 }}>
                支持: mysql://, postgresql://, sqlite:///
              </div>
            }
          >
            <Input
              placeholder="mysql://root:password@localhost:3306/test"
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
    </div>
  );
}

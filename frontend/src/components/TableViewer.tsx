/**
 * TableViewer Component
 * MotherDuck-style table structure display
 */
import { useState } from 'react';
import { Card, Table, Tag, Typography, Space, Button } from 'antd';
import { TableOutlined, EyeOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';
import type { TableMetadata, Column } from '../types';

const { Text } = Typography;

interface TableViewerProps {
  databaseName: string | null;
  metadata: TableMetadata[];
}

export function TableViewer({ databaseName, metadata }: TableViewerProps) {
  const [open, setOpen] = useState(true);

  if (!databaseName) {
    return null;
  }

  const columns = [
    {
      title: '字段名',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string, record: Column) => (
        <Space>
          <Text strong>{name}</Text>
          {record.isPrimaryKey && (
            <Tag color="gold" style={{ margin: 0, borderRadius: 4, fontSize: 10 }}>
              PK
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'dataType',
      key: 'dataType',
      width: 200,
      render: (dataType: string) => (
        <Text style={{ wordBreak: 'break-all', fontSize: 12, fontFamily: 'var(--font-family-mono)' }}>
          {dataType}
        </Text>
      ),
    },
    {
      title: 'Nullable',
      dataIndex: 'isNullable',
      key: 'isNullable',
      width: 80,
      render: (isNullable: boolean) => (
        <Text type={isNullable ? 'success' : 'secondary'} style={{ fontSize: 12 }}>
          {isNullable ? 'YES' : 'NO'}
        </Text>
      ),
    },
    {
      title: '注释',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (comment: string) => comment || '-',
    },
  ];

  const tables = metadata.filter((m) => m.type === 'table');
  const views = metadata.filter((m) => m.type === 'view');

  return (
    <Card
      className="md-card"
      title={
        <div className="md-card__title">
          <TableOutlined style={{ color: '#6B46C1' }} />
          <span>表结构</span>
          <Tag
            style={{
              background: 'rgba(107, 70, 193, 0.1)',
              color: '#6B46C1',
              border: 'none',
              borderRadius: 9999,
              marginLeft: 8,
            }}
          >
            {metadata.length} 个对象
          </Tag>
        </div>
      }
      extra={
        <Button
          type="text"
          size="small"
          onClick={() => setOpen(!open)}
          style={{ color: '#6B7280' }}
          icon={open ? <DownOutlined /> : <RightOutlined />}
        />
      }
      styles={{ body: { padding: open ? 20 : 0, maxHeight: open ? 'none' : 0, overflow: 'hidden' } }}
    >
      {open && (
        <>
          {metadata.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon">📋</div>
              <Text className="empty-state__text" style={{ color: '#6B7280' }}>
                暂无表结构信息
              </Text>
            </div>
          ) : (
            <>
              {tables.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <TableOutlined style={{ color: '#6B46C1' }} />
                    <Text strong style={{ fontSize: 14 }}>
                      表 ({tables.length})
                    </Text>
                  </div>
                  {tables.map((table) => (
                    <div key={table.name} style={{ marginBottom: 16 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <Text strong>{table.name}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          ({table.columns.length} 列)
                        </Text>
                      </div>
                      <Table
                        dataSource={table.columns}
                        columns={columns}
                        rowKey="name"
                        size="small"
                        pagination={false}
                        style={{ background: '#FAFBFF', borderRadius: 10 }}
                      />
                    </div>
                  ))}
                </div>
              )}

              {views.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <EyeOutlined style={{ color: '#8B5CF6' }} />
                    <Text strong style={{ fontSize: 14 }}>
                      视图 ({views.length})
                    </Text>
                  </div>
                  {views.map((view) => (
                    <div key={view.name} style={{ marginBottom: 16 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <Text strong>{view.name}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          ({view.columns.length} 列)
                        </Text>
                      </div>
                      <Table
                        dataSource={view.columns}
                        columns={columns}
                        rowKey="name"
                        size="small"
                        pagination={false}
                        style={{ background: '#FAFBFF', borderRadius: 10 }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </Card>
  );
}

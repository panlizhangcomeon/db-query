/**
 * DatabaseTree Component
 * MotherDuck-style database tree with dark theme
 */
import { useState, useMemo } from 'react';
import { Tree, Typography, Space, Button, Input } from 'antd';
import { TableOutlined, EyeOutlined, DownOutlined, RightOutlined, SearchOutlined } from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';
import type { Table } from '../types';

const { Text } = Typography;

interface DatabaseTreeProps {
  databaseName: string | null;
  tables: Table[];
  onTableSelect?: (tableName: string) => void;
}

export function DatabaseTree({ databaseName, tables, onTableSelect }: DatabaseTreeProps) {
  const [open, setOpen] = useState(true);
  const [searchText, setSearchText] = useState('');

  const filteredTables = useMemo(() => {
    if (!searchText.trim()) {
      return tables;
    }
    const lowerSearch = searchText.toLowerCase();
    return tables.filter((t) =>
      t.name.toLowerCase().includes(lowerSearch) ||
      t.columns.some((c) => c.name.toLowerCase().includes(lowerSearch))
    );
  }, [tables, searchText]);

  const tableNodes: DataNode[] = filteredTables
    .filter((t) => t.type === 'table')
    .map((table) => ({
      key: table.name,
      title: (
        <Space>
          <TableOutlined style={{ color: '#6B46C1' }} />
          <Text style={{ color: '#F9FAFB' }}>{table.name}</Text>
        </Space>
      ),
      children: table.columns.map((col) => ({
        key: `${table.name}.${col.name}`,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text style={{ minWidth: 100, color: '#D1D5DB' }}>{col.name}</Text>
            <Text style={{ color: '#6B7280', fontSize: 11 }}>{col.type}</Text>
            {col.isPrimaryKey && (
              <Text style={{ color: '#F59E0B', fontSize: 10, fontWeight: 600 }}>PK</Text>
            )}
          </div>
        ),
        isLeaf: true,
      })),
    }));

  const viewNodes: DataNode[] = filteredTables
    .filter((t) => t.type === 'view')
    .map((view) => ({
      key: view.name,
      title: (
        <Space>
          <EyeOutlined style={{ color: '#8B5CF6' }} />
          <Text style={{ color: '#F9FAFB' }}>{view.name}</Text>
        </Space>
      ),
      children: view.columns.map((col) => ({
        key: `${view.name}.${col.name}`,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text style={{ minWidth: 100, color: '#D1D5DB' }}>{col.name}</Text>
            <Text style={{ color: '#6B7280', fontSize: 11 }}>{col.type}</Text>
          </div>
        ),
        isLeaf: true,
      })),
    }));

  const treeData: DataNode[] = [
    {
      key: 'tables',
      title: (
        <Text strong style={{ color: '#9CA3AF', fontSize: 12 }}>
          <TableOutlined /> 表 ({tableNodes.length})
        </Text>
      ),
      children: tableNodes,
    },
    {
      key: 'views',
      title: (
        <Text strong style={{ color: '#9CA3AF', fontSize: 12 }}>
          <EyeOutlined /> 视图 ({viewNodes.length})
        </Text>
      ),
      children: viewNodes,
    },
  ];

  const handleSelect = (selectedKeys: React.Key[]) => {
    const key = selectedKeys[0] as string;
    if (key && !key.includes('.') && key !== 'tables' && key !== 'views') {
      onTableSelect?.(key);
    }
  };

  const defaultExpandedKeys = searchText.trim()
    ? filteredTables.map((t) => t.name)
    : ['tables', 'views'];

  if (!databaseName) {
    return (
      <div
        style={{
          background: 'transparent',
          borderRadius: 10,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            flexShrink: 0,
          }}
        >
          <Space>
            <RightOutlined style={{ color: '#6B7280', fontSize: 10 }} />
            <span style={{ color: '#F9FAFB', fontSize: 13, fontWeight: 500 }}>数据库结构</span>
          </Space>
        </div>
        <div style={{ padding: 12, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color: '#6B7280', fontSize: 12 }}>请先选择数据库</Text>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'transparent',
        borderRadius: 10,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          cursor: 'pointer',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          flexShrink: 0,
        }}
        onClick={() => setOpen(!open)}
      >
        <Space>
          {open ? <DownOutlined style={{ color: '#6B7280', fontSize: 10 }} /> : <RightOutlined style={{ color: '#6B7280', fontSize: 10 }} />}
          <span style={{ color: '#F9FAFB', fontSize: 13, fontWeight: 500 }}>数据库结构</span>
        </Space>
        <Button
          type="text"
          size="small"
          onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
          style={{ color: '#6B7280', fontSize: 10, padding: '0 4px', height: 20 }}
        >
          {open ? '折叠' : '展开'}
        </Button>
      </div>

      {open && (
        <div style={{ padding: 12, overflow: 'auto', flex: 1, minHeight: 0 }}>
          <Input
            placeholder="搜索表名或字段名..."
            prefix={<SearchOutlined style={{ color: '#6B7280' }} />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            style={{
              marginBottom: 12,
              background: '#232442',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#F9FAFB',
              borderRadius: 8,
            }}
            className="search-input"
          />

          {filteredTables.length === 0 ? (
            <Text style={{ color: '#6B7280', fontSize: 12 }}>
              未找到匹配的表或视图
            </Text>
          ) : (
            <Tree
              showIcon
              defaultExpandedKeys={defaultExpandedKeys}
              treeData={treeData}
              onSelect={handleSelect}
              style={{
                background: 'transparent',
                color: '#F9FAFB',
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}

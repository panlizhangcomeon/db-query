/**
 * DatabaseTree Component
 * Expandable schema tree for tables / views
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
    return tables.filter(
      (t) =>
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
          <TableOutlined style={{ color: 'var(--md-sky-strong)' }} />
          <Text className="md-text-ink">{table.name}</Text>
        </Space>
      ),
      children: table.columns.map((col) => ({
        key: `${table.name}.${col.name}`,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text style={{ minWidth: 100 }} className="md-text-ink">
              {col.name}
            </Text>
            <Text className="md-text-slate" style={{ fontSize: 11 }}>
              {col.dataType}
            </Text>
            {col.isPrimaryKey && (
              <Text style={{ fontSize: 10, fontWeight: 700, color: 'var(--md-graphite)' }}>PK</Text>
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
          <EyeOutlined style={{ color: 'var(--md-sky-strong)' }} />
          <Text className="md-text-ink">{view.name}</Text>
        </Space>
      ),
      children: view.columns.map((col) => ({
        key: `${view.name}.${col.name}`,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text style={{ minWidth: 100 }} className="md-text-ink">
              {col.name}
            </Text>
            <Text className="md-text-slate" style={{ fontSize: 11 }}>
              {col.dataType}
            </Text>
          </div>
        ),
        isLeaf: true,
      })),
    }));

  const treeData: DataNode[] = [
    {
      key: 'tables',
      title: (
        <Text strong className="md-text-slate" style={{ fontSize: 12 }}>
          <TableOutlined /> 表 ({tableNodes.length})
        </Text>
      ),
      children: tableNodes,
    },
    {
      key: 'views',
      title: (
        <Text strong className="md-text-slate" style={{ fontSize: 12 }}>
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
      <div className="md-panel">
        <div className="md-panel__head" style={{ cursor: 'default' }}>
          <Space>
            <RightOutlined className="md-text-slate" style={{ fontSize: 10 }} />
            <span className="md-panel__title">数据库结构</span>
          </Space>
        </div>
        <div style={{ padding: 12, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Text className="md-text-slate" style={{ fontSize: 12 }}>
            请先选择数据库
          </Text>
        </div>
      </div>
    );
  }

  return (
    <div className="md-panel">
      <div
        className="md-panel__head"
        style={{ cursor: 'pointer' }}
        onClick={() => setOpen(!open)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setOpen(!open);
          }
        }}
        role="button"
        tabIndex={0}
      >
        <Space>
          {open ? (
            <DownOutlined className="md-text-slate" style={{ fontSize: 10 }} />
          ) : (
            <RightOutlined className="md-text-slate" style={{ fontSize: 10 }} />
          )}
          <span className="md-panel__title">数据库结构</span>
        </Space>
        <Button
          type="text"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            setOpen(!open);
          }}
          className="md-text-slate"
          style={{ fontSize: 11, padding: '0 4px', height: 22 }}
        >
          {open ? '折叠' : '展开'}
        </Button>
      </div>

      {open && (
        <div style={{ overflow: 'auto', flex: 1, minHeight: 0 }}>
          <Input
            placeholder="搜索表名或字段名..."
            prefix={<SearchOutlined className="md-text-slate" />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            style={{ marginBottom: 12 }}
            className="search-input"
          />

          {filteredTables.length === 0 ? (
            <Text className="md-text-slate" style={{ fontSize: 12 }}>
              未找到匹配的表或视图
            </Text>
          ) : (
            <Tree
              showIcon
              defaultExpandedKeys={defaultExpandedKeys}
              treeData={treeData}
              onSelect={handleSelect}
              style={{ background: 'transparent' }}
            />
          )}
        </div>
      )}
    </div>
  );
}

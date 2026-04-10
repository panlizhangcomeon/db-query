/**
 * QueryResults Component
 * Display query results with pagination and metadata
 */
import { Card, Table, Typography, Tag } from 'antd';
import { FileTextOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { QueryResult } from '../types';

const { Text } = Typography;

interface QueryResultsProps {
  result: QueryResult | null;
  loading?: boolean;
}

export function QueryResults({ result, loading }: QueryResultsProps) {
  if (!result && !loading) {
    return (
      <Card
        className="md-card"
        title={
          <div className="md-card__title">
            <FileTextOutlined style={{ color: '#6B46C1' }} />
            <span>查询结果</span>
          </div>
        }
        styles={{ body: { padding: 40 } }}
      >
        <div className="empty-state">
          <div className="empty-state__icon">📊</div>
          <Text className="empty-state__text" style={{ color: '#6B7280' }}>
            执行 SQL 查询后，结果将显示在这里
          </Text>
        </div>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card
        className="md-card"
        title={
          <div className="md-card__title">
            <FileTextOutlined style={{ color: '#6B46C1' }} />
            <span>查询结果</span>
          </div>
        }
        styles={{ body: { padding: 40 } }}
      >
        <div style={{ textAlign: 'center', color: '#6B7280' }}>加载中...</div>
      </Card>
    );
  }

  // Handle both old format (rows as arrays) and new format (rows as objects)
  const columns = result.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    width: 150,
    ellipsis: true,
  }));

  // Convert rows to object format for table display
  const dataSource = result.rows.map((row, index) => {
    if (Array.isArray(row)) {
      // Old format: row is an array
      const obj: Record<string, unknown> = { key: index };
      result.columns.forEach((col, i) => {
        obj[col] = row[i];
      });
      return obj;
    }
    // New format: row is already an object
    return { key: index, ...row };
  });

  const executionTime = result.executionTimeMs;

  return (
    <Card
      className="md-card fade-in"
      title={
        <div className="md-card__title">
          <CheckCircleOutlined style={{ color: '#10B981' }} />
          <span>查询结果</span>
          <Tag
            style={{
              background: 'rgba(16, 185, 129, 0.1)',
              color: '#059669',
              border: 'none',
              borderRadius: 9999,
              marginLeft: 8,
            }}
          >
            {result.rowCount} 行
          </Tag>
          {executionTime !== undefined && executionTime !== null && (
            <Tag
              style={{
                background: 'rgba(59, 130, 246, 0.1)',
                color: '#2563EB',
                border: 'none',
                borderRadius: 9999,
              }}
              icon={<ClockCircleOutlined />}
            >
              {executionTime < 1000
                ? `${executionTime.toFixed(0)}ms`
                : `${(executionTime / 1000).toFixed(2)}s`}
            </Tag>
          )}
        </div>
      }
      styles={{ body: { padding: 0 } }}
    >
      {result.naturalLanguage && (
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #E5E7EB' }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
            自然语言查询:
          </Text>
          <Text>{result.naturalLanguage}</Text>
        </div>
      )}

      {(result.sql || result.generatedSql) && (
        <div style={{ padding: 16 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
            执行的 SQL:
          </Text>
          <div className="sql-display">{result.sql || result.generatedSql}</div>
        </div>
      )}

      <Table
        dataSource={dataSource}
        columns={columns}
        rowKey="key"
        size="small"
        scroll={{ x: 'max-content', y: 400 }}
        pagination={{
          pageSize: 100,
          showSizeChanger: true,
          pageSizeOptions: ['50', '100', '500', '1000'],
          showTotal: (total) => `共 ${total} 行`,
        }}
        style={{ borderRadius: 0 }}
      />
    </Card>
  );
}

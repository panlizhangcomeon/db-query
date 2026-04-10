/**
 * SqlQuery Component
 * SQL query input with connection and database selection
 */
import { Input, Button, Card, Typography, Space, Spin, Alert } from 'antd';
import { PlayCircleOutlined, SendOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { executeQuery } from '../services/api';
import type { QueryResult } from '../types';

const { TextArea } = Input;
const { Text } = Typography;

interface SqlQueryProps {
  connectionId: number | undefined;
  databaseName: string | null;
  onResult: (result: QueryResult) => void;
}

export function SqlQuery({ connectionId, databaseName, onResult }: SqlQueryProps) {
  const [sql, setSql] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async () => {
    if (!connectionId) {
      setError('请先选择连接');
      return;
    }

    if (!sql.trim()) {
      setError('请输入 SQL 语句');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await executeQuery({
        connectionId,
        database: databaseName || undefined,
        sql,
      });

      if (response.code === 200) {
        onResult(response.data!);
        setError(null);
      } else {
        setError(response.message || '查询失败');
      }
    } catch (err) {
      setError('查询失败: ' + String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      className="md-card"
      title={
        <div className="md-card__title">
          <PlayCircleOutlined style={{ color: '#6B46C1' }} />
          <span>SQL 查询</span>
        </div>
      }
      styles={{ body: { padding: 20 } }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {!connectionId && (
          <Alert
            type="warning"
            message="请先在左侧选择一个连接"
            showIcon
            style={{ borderRadius: 10 }}
          />
        )}

        <TextArea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          placeholder="输入 SQL 查询语句，例如: SELECT * FROM database.users LIMIT 100"
          autoSize={{ minRows: 4, maxRows: 8 }}
          disabled={!connectionId || loading}
          className="query-input"
          style={{
            minHeight: 120,
            background: '#1E1E2E',
            color: '#CDD6F4',
            borderColor: '#313244',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 13,
          }}
        />

        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleExecute}
          loading={loading}
          disabled={!connectionId || !sql.trim()}
          block
          style={{
            background: 'linear-gradient(135deg, #6B46C1 0%, #805AD5 100%)',
            border: 'none',
            height: 44,
            fontSize: 15,
            fontWeight: 500,
            borderRadius: 10,
          }}
        >
          执行查询
        </Button>

        {error && (
          <Alert
            type="error"
            message={error}
            showIcon
            closable
            onClose={() => setError(null)}
            style={{ borderRadius: 10 }}
          />
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin size="large" />
            <Text style={{ display: 'block', marginTop: 8, color: '#6B7280' }}>查询执行中...</Text>
          </div>
        )}
      </Space>
    </Card>
  );
}

/**
 * SqlQuery Component
 * SQL query input with connection and database selection
 */
import { Input, Button, Card, Typography, Space, Spin, Alert } from 'antd';
import { PlayCircleOutlined, SendOutlined } from '@ant-design/icons';
import { useState, useEffect } from 'react';
import { executeQuery } from '../services/api';
import type { QueryResult } from '../types';

const { TextArea } = Input;
const { Text } = Typography;

interface SqlQueryProps {
  connectionId: number | undefined;
  databaseName: string | null;
  onResult: (result: QueryResult) => void;
  /** 自然语言生成后写入编辑区；id 变化时覆盖当前 SQL */
  aiSqlInjection?: { id: number; sql: string } | null;
}

export function SqlQuery({ connectionId, databaseName, onResult, aiSqlInjection }: SqlQueryProps) {
  const [sql, setSql] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fromAi, setFromAi] = useState(false);

  useEffect(() => {
    setSql('');
    setFromAi(false);
    setError(null);
  }, [connectionId, databaseName]);

  useEffect(() => {
    if (!aiSqlInjection?.sql) {
      return;
    }
    setSql(aiSqlInjection.sql);
    setFromAi(true);
    setError(null);
  }, [aiSqlInjection]);

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
        setFromAi(false);
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
          <PlayCircleOutlined />
          <span>SQL 查询</span>
        </div>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {!connectionId && (
          <Alert type="warning" message="请先在左侧选择一个连接" showIcon />
        )}

        {fromAi && (
          <Alert
            type="success"
            showIcon
            message="已填入 AI 生成的 SQL"
            description="请核对列名、表名是否正确，修改后点击「执行查询」才会向数据库发起查询。"
            closable
            onClose={() => setFromAi(false)}
          />
        )}

        <div>
          <Text className="md-text-slate" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>
            SQL 语句
          </Text>
          <TextArea
            value={sql}
            onChange={(e) => {
              setSql(e.target.value);
            }}
            placeholder="输入 SQL 查询语句，例如: SELECT * FROM users LIMIT 100"
            autoSize={{ minRows: 5, maxRows: 16 }}
            disabled={!connectionId || loading}
            className="query-input"
          />
        </div>

        <Button
          type="primary"
          className="md-btn-primary"
          icon={<SendOutlined />}
          onClick={handleExecute}
          loading={loading}
          disabled={!connectionId || !sql.trim()}
          block
        >
          执行查询
        </Button>

        {error && (
          <Alert
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            message={error.includes('\n') || error.length > 200 ? 'SQL 执行失败' : error}
            description={
              error.includes('\n') || error.length > 200 ? (
                <pre
                  style={{
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    margin: 0,
                    fontSize: 12,
                    fontFamily: 'var(--font-family-mono)',
                  }}
                >
                  {error}
                </pre>
              ) : undefined
            }
          />
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin size="large" />
            <Text className="md-text-slate" style={{ display: 'block', marginTop: 8 }}>
              查询执行中...
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
}

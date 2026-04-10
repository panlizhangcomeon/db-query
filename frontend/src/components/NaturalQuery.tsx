/**
 * NaturalQuery Component
 * AI natural language query with connection selection
 */
import { Input, Button, Card, Typography, Space, Spin, Alert } from 'antd';
import { SendOutlined, RobotOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { executeNaturalQuery } from '../services/api';
import type { QueryResult } from '../types';

const { TextArea } = Input;
const { Text } = Typography;

interface NaturalQueryProps {
  connectionId: number | undefined;
  databaseName: string | null;
  onResult: (result: QueryResult) => void;
}

export function NaturalQuery({ connectionId, databaseName, onResult }: NaturalQueryProps) {
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async () => {
    if (!connectionId) {
      setError('请先选择连接');
      return;
    }

    if (!query.trim()) {
      setError('请输入查询内容');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await executeNaturalQuery({
        connectionId,
        database: databaseName || undefined,
        naturalLanguage: query,
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
          <RobotOutlined style={{ color: '#8B5CF6' }} />
          <span>自然语言查询</span>
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

        <Alert
          type="info"
          message="输入自然语言描述您的查询需求，AI 将自动转换为 SQL"
          showIcon
          style={{ borderRadius: 10, background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)' }}
        />

        <TextArea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如: 查询所有用户，按创建时间排序"
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
          disabled={!connectionId || !query.trim()}
          block
          style={{
            background: 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
            border: 'none',
            height: 44,
            fontSize: 15,
            fontWeight: 500,
            borderRadius: 10,
          }}
        >
          AI 生成并查询
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
            <Text style={{ display: 'block', marginTop: 8, color: '#6B7280' }}>AI 正在分析并生成 SQL...</Text>
          </div>
        )}
      </Space>
    </Card>
  );
}

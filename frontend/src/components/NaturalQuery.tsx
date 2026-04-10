/**
 * NaturalQuery Component
 * AI natural language → SQL 生成（不执行；由左侧「执行查询」运行）
 */
import { Input, Button, Card, Typography, Space, Spin, Alert, message } from 'antd';
import { SendOutlined, RobotOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { generateNaturalSql } from '../services/api';

const { TextArea } = Input;
const { Text } = Typography;

interface NaturalQueryProps {
  connectionId: number | undefined;
  databaseName: string | null;
  onGeneratedSql: (sql: string) => void;
}

export function NaturalQuery({ connectionId, databaseName, onGeneratedSql }: NaturalQueryProps) {
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
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
      const response = await generateNaturalSql({
        connectionId,
        database: databaseName || undefined,
        naturalLanguage: query,
      });

      if (response.code === 200 && response.data?.generatedSql) {
        onGeneratedSql(response.data.generatedSql);
        setError(null);
        message.success('SQL 已填入左侧「SQL 查询」，确认无误后请点击「执行查询」');
      } else {
        setError(response.message || '生成失败');
      }
    } catch (err) {
      setError('生成失败: ' + String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      className="md-card"
      title={
        <div className="md-card__title">
          <RobotOutlined />
          <span>自然语言查询</span>
        </div>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {!connectionId && (
          <Alert type="warning" message="请先在左侧选择一个连接" showIcon />
        )}

        <Alert
          type="info"
          message="用一句话描述你想查什么，系统只生成 SQL（仅 SELECT），不会立刻查库。"
          description="生成后请在左侧「SQL 查询」中检查或修改语句，再点击「执行查询」运行。"
          showIcon
          className="md-tip"
        />

        <TextArea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：最晚提交的合同"
          autoSize={{ minRows: 4, maxRows: 8 }}
          disabled={!connectionId || loading}
          className="query-input"
        />

        <Button
          type="primary"
          className="md-btn-primary"
          icon={<SendOutlined />}
          onClick={handleGenerate}
          loading={loading}
          disabled={!connectionId || !query.trim()}
          block
        >
          AI 生成 SQL
        </Button>

        {error && (
          <Alert
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            message={error.includes('\n') || error.length > 200 ? '生成 SQL 失败' : error}
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
              正在生成 SQL...
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
}

/**
 * QueryResults Component
 * Display query results with pagination and metadata
 */
import { useState } from 'react';
import { Card, Table, Typography, Tag, Modal } from 'antd';
import { FileTextOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { QueryResult } from '../types';

const { Text } = Typography;

const COLUMN_WIDTH = 160;

interface QueryResultsProps {
  result: QueryResult | null;
  loading?: boolean;
}

function formatCellValue(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

export function QueryResults({ result, loading }: QueryResultsProps) {
  const [cellDetail, setCellDetail] = useState<{ column: string; value: string } | null>(null);

  if (!result && !loading) {
    return (
      <Card
        className="md-card"
        title={
          <div className="md-card__title">
            <FileTextOutlined />
            <span>查询结果</span>
          </div>
        }
        styles={{ body: { padding: 40 } }}
      >
        <div className="empty-state">
          <div className="empty-state__icon" aria-hidden>
            📊
          </div>
          <Text className="empty-state__text">
            执行 SQL 或自然语言查询后，结果将显示在这里。
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
            <FileTextOutlined />
            <span>查询结果</span>
          </div>
        }
        styles={{ body: { padding: 40 } }}
      >
        <div style={{ textAlign: 'center' }} className="md-text-slate">
          加载中...
        </div>
      </Card>
    );
  }

  /** 各列固定宽度之和，避免使用 max-content 被单格长串撑开整表 */
  const scrollX = Math.max(result.columns.length * COLUMN_WIDTH, COLUMN_WIDTH * 2);

  const columns = result.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    width: COLUMN_WIDTH,
    ellipsis: { showTitle: false },
    render: (value: unknown) => {
      const text = formatCellValue(value);
      const display = text.length ? text : '—';
      return (
        <div
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: '100%',
            minWidth: 0,
          }}
          onDoubleClick={() => {
            if (!text.length) return;
            setCellDetail({ column: col, value: text });
          }}
        >
          {display}
        </div>
      );
    },
  }));

  const dataSource = result.rows.map((row, index) => {
    if (Array.isArray(row)) {
      const obj: Record<string, unknown> = { key: index };
      result.columns.forEach((col, i) => {
        obj[col] = row[i];
      });
      return obj;
    }
    return { key: index, ...row };
  });

  const executionTime = result.executionTimeMs;

  return (
    <Card
      className="md-card fade-in"
      title={
        <div className="md-card__title" style={{ flexWrap: 'wrap', gap: 8 }}>
          <CheckCircleOutlined style={{ color: 'var(--md-sky-strong)' }} />
          <span>查询结果</span>
          <Tag style={{ background: 'var(--md-sunbeam)', margin: 0 }}>
            {result.rowCount} 行
          </Tag>
          {executionTime !== undefined && executionTime !== null && (
            <Tag
              style={{ background: 'var(--md-soft-blue)', margin: 0 }}
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
        <div
          style={{
            padding: 'var(--space-4) var(--space-6)',
            borderBottom: '2px solid var(--md-graphite)',
            background: 'var(--md-fog)',
          }}
        >
          <Text
            className="md-text-slate"
            style={{ fontSize: 11, display: 'block', marginBottom: 4, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}
          >
            自然语言
          </Text>
          <Text className="md-text-ink">{result.naturalLanguage}</Text>
        </div>
      )}

      {(result.sql || result.generatedSql) && (
        <div style={{ padding: 'var(--space-4) var(--space-6)' }}>
          <Text
            className="md-text-slate"
            style={{ fontSize: 11, display: 'block', marginBottom: 8, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}
          >
            执行的 SQL
          </Text>
          <div className="sql-display">{result.sql || result.generatedSql}</div>
        </div>
      )}

      <Table
        dataSource={dataSource}
        columns={columns}
        rowKey="key"
        size="small"
        tableLayout="fixed"
        scroll={{ x: scrollX, y: 400 }}
        pagination={{
          pageSize: 100,
          showSizeChanger: true,
          pageSizeOptions: ['50', '100', '500', '1000'],
          showTotal: (total) => `共 ${total} 行`,
        }}
        style={{ borderRadius: 0 }}
      />

      <Modal
        title={cellDetail?.column ?? ''}
        open={!!cellDetail}
        onCancel={() => setCellDetail(null)}
        footer={null}
        width={720}
        destroyOnClose
      >
        <Text
          className="md-text-ink"
          style={{
            display: 'block',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            fontFamily: 'var(--font-family-mono, ui-monospace, monospace)',
            fontSize: 13,
            lineHeight: 1.5,
            maxHeight: 'min(60vh, 480px)',
            overflow: 'auto',
          }}
        >
          {cellDetail?.value ?? ''}
        </Text>
      </Modal>
    </Card>
  );
}

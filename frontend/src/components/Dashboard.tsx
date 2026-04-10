/**
 * Dashboard Component
 * Minimal stats dashboard showing database metrics
 */
import { Card, Row, Col, Statistic, Typography } from 'antd';
import { TableOutlined, EyeOutlined, DatabaseOutlined, ColumnWidthOutlined } from '@ant-design/icons';
import type { TableMetadata } from '../types';

const { Text } = Typography;

interface DashboardProps {
  databaseName: string | null;
  metadata: TableMetadata[];
  selectedTableRowCount?: number;
  selectedTableAutoIncrement?: string;
}

export function Dashboard({ databaseName, metadata, selectedTableRowCount, selectedTableAutoIncrement }: DashboardProps) {
  const tables = metadata.filter((m) => m.type === 'table');
  const views = metadata.filter((m) => m.type === 'view');

  // Calculate total columns
  const totalColumns = metadata.reduce((sum, t) => sum + t.columns.length, 0);

  if (!databaseName) {
    return null;
  }

  return (
    <Card
      className="md-card"
      styles={{ body: { padding: '20px 24px' } }}
    >
      <Row gutter={[24, 16]}>
        <Col xs={12} sm={6}>
          <Statistic
            title={<Text style={{ color: '#6B7280', fontSize: 12 }}>数据库表</Text>}
            value={tables.length}
            prefix={<TableOutlined style={{ color: '#6B46C1', fontSize: 18 }} />}
            valueStyle={{ color: '#1F2937', fontSize: 28, fontWeight: 600 }}
          />
        </Col>

        <Col xs={12} sm={6}>
          <Statistic
            title={<Text style={{ color: '#6B7280', fontSize: 12 }}>视图</Text>}
            value={views.length}
            prefix={<EyeOutlined style={{ color: '#8B5CF6', fontSize: 18 }} />}
            valueStyle={{ color: '#1F2937', fontSize: 28, fontWeight: 600 }}
          />
        </Col>

        <Col xs={12} sm={6}>
          <Statistic
            title={<Text style={{ color: '#6B7280', fontSize: 12 }}>总字段数</Text>}
            value={totalColumns}
            prefix={<ColumnWidthOutlined style={{ color: '#3B82F6', fontSize: 18 }} />}
            valueStyle={{ color: '#1F2937', fontSize: 28, fontWeight: 600 }}
          />
        </Col>

        <Col xs={12} sm={6}>
          <Statistic
            title={<Text style={{ color: '#6B7280', fontSize: 12 }}>当前表行数</Text>}
            value={selectedTableRowCount ?? '-'}
            suffix={selectedTableRowCount !== undefined ? '行' : ''}
            prefix={<DatabaseOutlined style={{ color: '#10B981', fontSize: 18 }} />}
            valueStyle={{ color: '#1F2937', fontSize: 28, fontWeight: 600 }}
          />
        </Col>
      </Row>

      {selectedTableAutoIncrement && (
        <div style={{ marginTop: 16, padding: '12px 16px', background: '#F9FAFB', borderRadius: 10, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Text style={{ color: '#6B7280', fontSize: 12 }}>自增ID范围:</Text>
          <Text strong style={{ color: '#1F2937', fontSize: 13 }}>{selectedTableAutoIncrement}</Text>
        </div>
      )}
    </Card>
  );
}

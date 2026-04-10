/**
 * ConnectionSelector Component
 * Dropdown to select MySQL server connections
 */
import { Select, Typography } from 'antd';
import { CloudServerOutlined } from '@ant-design/icons';
import type { Connection } from '../types';

const { Text } = Typography;

interface ConnectionSelectorProps {
  connections: Connection[];
  selectedConnection: Connection | null;
  onSelect: (connection: Connection | null) => void;
}

export function ConnectionSelector({
  connections,
  selectedConnection,
  onSelect,
}: ConnectionSelectorProps) {
  return (
    <div>
      <span className="md-sidebar-label">选择连接</span>
      <Select
        placeholder="请选择连接..."
        value={selectedConnection?.id}
        onChange={(id) => {
          const conn = connections.find((c) => c.id === id) || null;
          onSelect(conn);
        }}
        style={{ width: '100%' }}
        suffixIcon={<CloudServerOutlined className="md-text-ink" style={{ fontSize: 14 }} />}
        options={connections.map((conn) => ({
          value: conn.id,
          label: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <CloudServerOutlined style={{ color: 'var(--md-sky-strong)' }} />
              <span className="md-text-ink">{conn.name}</span>
              <Text className="md-text-slate" style={{ fontSize: 12 }}>
                {conn.host}:{conn.port}
              </Text>
            </div>
          ),
        }))}
        allowClear
        showSearch
        filterOption={(input, option) =>
          String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
        }
        className="connection-selector"
      />
    </div>
  );
}

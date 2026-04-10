/**
 * DatabaseSelector Component
 * MotherDuck-style dropdown with dark theme
 */
import { Select, Typography } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import type { DatabaseConnection } from '../types';

const { Text } = Typography;

interface DatabaseSelectorProps {
  databases: DatabaseConnection[];
  selectedDb: string | null;
  onSelect: (name: string | null) => void;
}

export function DatabaseSelector({
  databases,
  selectedDb,
  onSelect,
}: DatabaseSelectorProps) {
  return (
    <div>
      <Text strong style={{ color: '#9CA3AF', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: 8 }}>
        选择数据库
      </Text>
      <Select
        placeholder="请选择数据库..."
        value={selectedDb}
        onChange={onSelect}
        style={{ width: '100%', background: '#232442' }}
        suffixIcon={<DatabaseOutlined style={{ color: '#6B46C1' }} />}
        options={databases.map((db) => ({
          value: db.name,
          label: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <DatabaseOutlined style={{ color: '#805AD5' }} />
              <span>{db.name}</span>
            </div>
          ),
        }))}
        allowClear
        showSearch
        filterOption={(input, option) =>
          String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
        }
        className="database-selector"
      />
    </div>
  );
}

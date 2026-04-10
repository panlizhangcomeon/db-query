/**
 * DatabaseList Component
 * MotherDuck-style database list with dark theme
 * Note: Databases are discovered from the MySQL server, not manually managed
 */
import { useState } from 'react';
import { Typography, Button } from 'antd';
import { DownOutlined, RightOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface DatabaseListProps {
  databases: { name: string }[];
  selectedDb: string | null;
  onSelect: (name: string) => void;
}

export function DatabaseList({ databases, selectedDb, onSelect }: DatabaseListProps) {
  const [open, setOpen] = useState(true);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <Text strong style={{ color: '#9CA3AF', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          数据库列表 ({databases.length})
        </Text>
        <Button
          type="text"
          size="small"
          onClick={() => setOpen(!open)}
          style={{ color: '#6B7280' }}
          icon={open ? <DownOutlined /> : <RightOutlined />}
        />
      </div>

      {open && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          maxHeight: 200,
          overflowY: 'auto',
          overflowX: 'hidden',
        }}>
          {databases.length === 0 ? (
            <div style={{ color: '#6B7280', fontSize: 13, textAlign: 'center', padding: 16 }}>
              暂无数据库
            </div>
          ) : (
            databases.map((db) => (
              <div
                key={db.name}
                onClick={() => onSelect(db.name)}
                className={`db-card ${selectedDb === db.name ? 'db-card--active' : ''}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                    <div className="db-card__name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {db.name}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

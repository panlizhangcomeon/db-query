/**
 * DatabaseList Component
 * Databases discovered from the MySQL server
 */
import { useState } from 'react';
import { Button } from 'antd';
import { DownOutlined, RightOutlined } from '@ant-design/icons';

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
        <span className="md-sidebar-label" style={{ marginBottom: 0 }}>
          数据库列表 ({databases.length})
        </span>
        <Button
          type="text"
          size="small"
          onClick={() => setOpen(!open)}
          className="md-text-slate"
          icon={open ? <DownOutlined /> : <RightOutlined />}
        />
      </div>

      {open && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            maxHeight: 200,
            overflowY: 'auto',
            overflowX: 'hidden',
          }}
        >
          {databases.length === 0 ? (
            <div className="md-text-slate" style={{ fontSize: 13, textAlign: 'center', padding: 16 }}>
              暂无数据库
            </div>
          ) : (
            databases.map((db) => (
              <div
                key={db.name}
                onClick={() => onSelect(db.name)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(db.name);
                  }
                }}
                className={`db-card ${selectedDb === db.name ? 'db-card--active' : ''}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                    <div
                      className="db-card__name"
                      style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    >
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

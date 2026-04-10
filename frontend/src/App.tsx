/**
 * AI Database Query Tool - Main App Component
 * Multi-database support with connection management
 */
import { useState, useEffect, useCallback } from 'react';
import { Layout, Row, Col, message, ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ThunderboltOutlined } from '@ant-design/icons';

import { ConnectionSelector } from './components/ConnectionSelector';
import { DatabaseList } from './components/DatabaseList';
import { AddConnectionForm } from './components/AddConnection';
import { DatabaseTree } from './components/DatabaseTree';
import { SqlQuery } from './components/SqlQuery';
import { NaturalQuery } from './components/NaturalQuery';
import { QueryResults } from './components/QueryResults';

import type { Connection, Database, Table, QueryResult } from './types';
import {
  listConnections,
  getConnectionDatabases,
  getDatabaseTables,
  deleteConnection,
} from './services/api';

const { Header, Sider, Content } = Layout;

function App() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [databases, setDatabases] = useState<Database[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);
  const [tables, setTables] = useState<Table[]>([]);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  /** 自然语言返回的 SQL 注入左侧编辑器（id 递增触发同步） */
  const [aiSqlInjection, setAiSqlInjection] = useState<{ id: number; sql: string } | null>(null);

  useEffect(() => {
    fetchConnections();
  }, []);

  useEffect(() => {
    if (selectedConnection) {
      fetchDatabases(selectedConnection.id);
    } else {
      setDatabases([]);
      setSelectedDatabase(null);
    }
  }, [selectedConnection]);

  useEffect(() => {
    if (selectedConnection && selectedDatabase) {
      fetchTables(selectedConnection.id, selectedDatabase);
    } else {
      setTables([]);
    }
  }, [selectedConnection, selectedDatabase]);

  const fetchConnections = async () => {
    try {
      const response = await listConnections();
      if (response.code === 200) {
        setConnections(response.data?.connections || []);
      }
    } catch {
      message.error('获取连接列表失败');
    }
  };

  const fetchDatabases = async (connectionId: number) => {
    try {
      const response = await getConnectionDatabases(connectionId);
      if (response.code === 200) {
        setDatabases(response.data?.databases || []);
        if (response.data?.databases?.length && !selectedDatabase) {
          setSelectedDatabase(response.data.databases[0].name);
        }
      }
    } catch {
      message.error('获取数据库列表失败');
    }
  };

  const fetchTables = async (connectionId: number, database: string) => {
    try {
      const response = await getDatabaseTables(connectionId, database);
      if (response.code === 200) {
        setTables(response.data?.tables || []);
      }
    } catch {
      message.error('获取表结构失败');
    }
  };

  const handleConnectionSelect = useCallback((connection: Connection | null) => {
    setSelectedConnection(connection);
    setSelectedDatabase(null);
    setTables([]);
    setQueryResult(null);
    setAiSqlInjection(null);
  }, []);

  const handleDatabaseSelect = useCallback((database: string | null) => {
    setSelectedDatabase(database);
    setQueryResult(null);
    setAiSqlInjection(null);
  }, []);

  const handleConnectionAdded = useCallback(async (connection: Connection) => {
    await fetchConnections();
    setSelectedConnection(connection);
  }, []);

  const handleConnectionDeleted = useCallback(async () => {
    if (selectedConnection) {
      try {
        await deleteConnection(selectedConnection.id);
      } catch (error) {
        console.error('Failed to delete connection:', error);
      }
      setSelectedConnection(null);
      setSelectedDatabase(null);
      setTables([]);
      setQueryResult(null);
      await fetchConnections();
    }
  }, [selectedConnection]);

  const handleTableSelect = useCallback((tableName: string) => {
    console.log('Table selected:', tableName);
  }, []);

  const handleQueryResult = useCallback((result: QueryResult) => {
    setQueryResult(result);
  }, []);

  const handleNaturalSqlGenerated = useCallback((sql: string) => {
    const trimmed = sql.trim();
    if (!trimmed) {
      return;
    }
    setAiSqlInjection((prev) => ({
      id: (prev?.id ?? 0) + 1,
      sql: trimmed,
    }));
  }, []);

  const existingConnectionNames = connections.map((c) => c.name);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#6fc2ff',
          colorInfo: '#2ba5ff',
          colorSuccess: '#383838',
          colorWarning: '#ffde00',
          colorError: '#c53030',
          colorBgBase: '#f4efea',
          colorBgContainer: '#ffffff',
          colorBorder: '#000000',
          colorText: '#383838',
          colorTextSecondary: '#a1a1a1',
          borderRadius: 2,
          wireframe: false,
          fontFamily:
            "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          fontSize: 15,
          controlHeight: 40,
        },
        components: {
          Button: {
            primaryShadow: 'none',
            fontWeight: 700,
          },
          Card: {
            headerBg: '#ebf9ff',
            colorBorderSecondary: '#000000',
          },
          Layout: {
            headerBg: '#ffffff',
            bodyBg: '#f4efea',
            siderBg: '#ffffff',
          },
        },
      }}
    >
      <Layout className="app-layout-root" style={{ height: '100vh', overflow: 'hidden' }}>
        <header className="app-eyebrow" role="banner">
          <span className="app-eyebrow__label">SELECT * FROM CLARITY</span>
          <p className="app-eyebrow__sub">
            多库连接、受控 SELECT 与自然语言查询，结构化得像仪表盘一样顺手。
          </p>
          <a className="app-eyebrow__cta" href="#main-workspace">
            开始查询
          </a>
        </header>

        <Header className="app-header">
          <div className="app-header__logo">
            <div className="app-header__logo-icon" aria-hidden>
              <ThunderboltOutlined />
            </div>
            <span className="app-header__title">AI 数据库查询</span>
          </div>
          {selectedConnection && (
            <div className="app-header__meta">
              <span className="status-badge">
                连接 · {selectedConnection.name}
              </span>
              {selectedDatabase && (
                <span className="status-badge status-badge--success">
                  库 · {selectedDatabase}
                </span>
              )}
            </div>
          )}
        </Header>

        <Layout className="app-main-row" style={{ flex: 1, overflow: 'hidden' }}>
          <Sider
            width={320}
            className="app-sidebar"
            style={{
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="app-sidebar__section">
                <ConnectionSelector
                  connections={connections}
                  selectedConnection={selectedConnection}
                  onSelect={handleConnectionSelect}
                />
              </div>

              <div className="app-sidebar__divider" />

              {selectedConnection && (
                <div className="app-sidebar__scroll">
                  <div style={{ padding: 'var(--space-3) var(--space-4) var(--space-2)' }}>
                    <DatabaseList
                      databases={databases.map((d) => ({ name: d.name }))}
                      selectedDb={selectedDatabase}
                      onSelect={handleDatabaseSelect}
                    />
                  </div>

                  <div className="app-sidebar__scroll-inner">
                    <DatabaseTree
                      databaseName={selectedDatabase}
                      tables={tables}
                      onTableSelect={handleTableSelect}
                    />
                  </div>
                </div>
              )}

              <div className="app-sidebar__divider" />

              <div className="app-sidebar__section">
                <AddConnectionForm
                  onSuccess={handleConnectionAdded}
                  existingNames={existingConnectionNames}
                  onDelete={selectedConnection ? () => handleConnectionDeleted() : undefined}
                />
              </div>
            </div>
          </Sider>

          <Content
            id="main-workspace"
            className="app-content"
            style={{ overflow: 'auto' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <SqlQuery
                  connectionId={selectedConnection?.id}
                  databaseName={selectedDatabase}
                  onResult={handleQueryResult}
                  aiSqlInjection={aiSqlInjection}
                />
              </Col>

              <Col xs={24} lg={12}>
                <NaturalQuery
                  connectionId={selectedConnection?.id}
                  databaseName={selectedDatabase}
                  onGeneratedSql={handleNaturalSqlGenerated}
                />
              </Col>

              <Col span={24}>
                <QueryResults result={queryResult} />
              </Col>
            </Row>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;

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
  const [loading, setLoading] = useState(false);

  // Fetch all connections on mount
  useEffect(() => {
    fetchConnections();
  }, []);

  // When connection changes, fetch databases
  useEffect(() => {
    if (selectedConnection) {
      fetchDatabases(selectedConnection.id);
    } else {
      setDatabases([]);
      setSelectedDatabase(null);
    }
  }, [selectedConnection]);

  // When database changes, fetch tables
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
    } catch (error) {
      message.error('获取连接列表失败');
    }
  };

  const fetchDatabases = async (connectionId: number) => {
    try {
      setLoading(true);
      const response = await getConnectionDatabases(connectionId);
      if (response.code === 200) {
        setDatabases(response.data?.databases || []);
        // Auto-select first database if none selected
        if (response.data?.databases?.length && !selectedDatabase) {
          setSelectedDatabase(response.data.databases[0].name);
        }
      }
    } catch (error) {
      message.error('获取数据库列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchTables = async (connectionId: number, database: string) => {
    try {
      setLoading(true);
      const response = await getDatabaseTables(connectionId, database);
      if (response.code === 200) {
        setTables(response.data?.tables || []);
      }
    } catch (error) {
      message.error('获取表结构失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionSelect = useCallback((connection: Connection | null) => {
    setSelectedConnection(connection);
    setSelectedDatabase(null);
    setTables([]);
    setQueryResult(null);
  }, []);

  const handleDatabaseSelect = useCallback((database: string | null) => {
    setSelectedDatabase(database);
    setQueryResult(null);
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
    // Could implement inserting table name into query
    console.log('Table selected:', tableName);
  }, []);

  const handleQueryResult = useCallback((result: QueryResult) => {
    setQueryResult(result);
  }, []);

  const existingConnectionNames = connections.map((c) => c.name);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#6B46C1',
          borderRadius: 10,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        },
      }}
    >
      <Layout style={{ height: '100vh', overflow: 'hidden' }}>
        <Header className="app-header">
          <div className="app-header__logo">
            <div className="app-header__logo-icon">
              <ThunderboltOutlined style={{ color: 'white' }} />
            </div>
            <span style={{ color: 'white', fontSize: 18, fontWeight: 600 }}>
              AI 数据库查询
            </span>
          </div>
          {selectedConnection && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span className="status-badge">
                连接: {selectedConnection.name} ({selectedConnection.host})
              </span>
              {selectedDatabase && (
                <span className="status-badge status-badge--success">
                  数据库: {selectedDatabase}
                </span>
              )}
            </div>
          )}
        </Header>

        <Layout style={{ flex: 1 }}>
          <Sider
            width={320}
            className="app-sidebar"
            style={{
              background: '#1A1B3A',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              {/* Connection Selector */}
              <div className="app-sidebar__section" style={{ padding: 16 }}>
                <ConnectionSelector
                  connections={connections}
                  selectedConnection={selectedConnection}
                  onSelect={handleConnectionSelect}
                />
              </div>

              <div className="app-sidebar__divider" />

              {/* Database List */}
              {selectedConnection && (
                <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ padding: '12px 16px 8px' }}>
                    <DatabaseList
                      databases={databases.map((d) => ({ name: d.name }))}
                      selectedDb={selectedDatabase}
                      onSelect={handleDatabaseSelect}
                    />
                  </div>

                  {/* Table Tree */}
                  <div style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
                    <DatabaseTree
                      databaseName={selectedDatabase}
                      tables={tables}
                      onTableSelect={handleTableSelect}
                    />
                  </div>
                </div>
              )}

              <div className="app-sidebar__divider" />

              {/* Add Connection Form */}
              <div style={{ padding: 16 }}>
                <AddConnectionForm
                  onSuccess={handleConnectionAdded}
                  existingNames={existingConnectionNames}
                  onDelete={selectedConnection ? () => handleConnectionDeleted() : undefined}
                />
              </div>
            </div>
          </Sider>

          <Content className="app-content" style={{ overflow: 'auto', padding: 16 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <SqlQuery
                  connectionId={selectedConnection?.id}
                  databaseName={selectedDatabase}
                  onResult={handleQueryResult}
                />
              </Col>

              <Col xs={24} lg={12}>
                <NaturalQuery
                  connectionId={selectedConnection?.id}
                  databaseName={selectedDatabase}
                  onResult={handleQueryResult}
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

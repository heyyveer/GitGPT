import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import RepoDiscovery from './components/RepoDiscovery';
import GitHubSearchPage from './components/GitHubSearchPage';
import IngestionPipeline from './components/IngestionPipeline';
import ChatStudio from './components/ChatStudio';
import CodeExplorer from './components/CodeExplorer';
import ArchitectureView from './components/ArchitectureView';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState(() => {
    const pathname = window.location.pathname.toLowerCase();
    const hash = window.location.hash.toLowerCase();
    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get('tab')) return searchParams.get('tab');
    if (pathname.includes('/search') || hash === '#search') return 'search';
    return 'search';
  });
  const [systemStatus, setSystemStatus] = useState(null);
  const [activeRepo, setActiveRepo] = useState(null);
  const [selectedModel, setSelectedModel] = useState('openai/gpt-oss-20b');
  const [messages, setMessages] = useState([]);

  // Ingestion state
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState({
    progress: 0,
    step: '',
    error: null
  });

  // Navigation into Code Explorer with line jump
  const [navTargetFile, setNavTargetFile] = useState(null);
  const [navTargetLine, setNavTargetLine] = useState(null);

  const pollTimerRef = useRef(null);

  // Fetch initial system status
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        if (data.active_repo) {
          setActiveRepo(data.active_repo);
        }
        if (data.selected_model) {
          setSelectedModel(data.selected_model);
        }
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  // Poll ingestion progress when ingesting
  useEffect(() => {
    if (ingesting) {
      pollTimerRef.current = setInterval(async () => {
        try {
          const res = await fetch('/api/ingest/status');
          if (res.ok) {
            const data = await res.json();
            setIngestStatus({
              progress: data.progress || 0,
              step: data.step || '',
              error: data.error || null
            });
            if (!data.ingesting && data.active_repo) {
              setIngesting(false);
              setActiveRepo(data.active_repo);
              clearInterval(pollTimerRef.current);
            }
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 750);
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [ingesting]);

  // Handle repository ingestion
  const handleIngestRepo = async (url, forceReclone = false) => {
    if (!url || !url.trim()) return;
    
    setIngesting(true);
    setIngestStatus({ progress: 10, step: 'Starting ingestion pipeline...', error: null });
    setActiveTab('ingest');

    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), force_reclone: forceReclone })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Ingestion failed');
      }

      const data = await res.json();
      setActiveRepo(data.repo);
      setIngestStatus({ progress: 100, step: 'Completed', error: null });

      // Add welcoming assistant message
      setMessages([
        {
          role: 'assistant',
          content: `👋 **Repository [${data.repo.name}](${data.repo.url}) is now loaded and indexed!**\n\n` +
                   `- 📦 **${data.repo.files_count}** Code Files | **${data.repo.stats?.total_lines?.toLocaleString() || 0}** Lines of Code\n` +
                   `- 🧩 **${data.repo.chunks_count}** AST & Semantic Chunks stored in Vector Memory\n` +
                   `- 🤖 **Specialized Agents Ready**: CodeSearch, Documentation, Debugging, Architecture & Verifier.\n\n` +
                   `Ask any question about the codebase, or try one of the quick prompt starters above!`,
          agent: 'SystemCoordinator',
          route: 'GENERAL',
          latency: 0.0,
          verification: { verified: true, confidence: 1.0, reason: 'Repository indexed successfully.' },
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      fetchStatus();
    } catch (err) {
      setIngestStatus((prev) => ({ ...prev, error: err.message, step: 'Failed' }));
    } finally {
      setIngesting(false);
    }
  };

  // Handle unload repository
  const handleUnloadRepo = async () => {
    try {
      await fetch('/api/repo/unload', { method: 'POST' });
      setActiveRepo(null);
      setMessages([]);
      setActiveTab('discovery');
      fetchStatus();
    } catch (err) {
      console.error('Failed to unload repo:', err);
    }
  };

  // Handle Model Change
  const handleModelChange = async (modelId) => {
    setSelectedModel(modelId);
    try {
      await fetch('/api/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId })
      });
      fetchStatus();
    } catch (err) {
      console.error('Failed to update model:', err);
    }
  };

  // Handle jump to file from chat citations
  const handleNavigateToFile = (filePath, lineNumber) => {
    setNavTargetFile(filePath);
    setNavTargetLine(lineNumber);
    setActiveTab('explorer');
  };

  return (
    <div className="app-shell">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeRepo={activeRepo}
        systemStatus={systemStatus}
        selectedModel={selectedModel}
        onModelChange={handleModelChange}
        onUnloadRepo={handleUnloadRepo}
      />

      {/* Main View Container */}
      <main className="main-content-container">
        {activeTab === 'search' && (
          <GitHubSearchPage />
        )}

        {activeTab === 'discovery' && (
          <RepoDiscovery
            onIngestRepo={handleIngestRepo}
            ingesting={ingesting}
            activeRepo={activeRepo}
            onSwitchToChat={() => setActiveTab('chat')}
          />
        )}

        {activeTab === 'ingest' && (
          <IngestionPipeline
            activeRepo={activeRepo}
            ingesting={ingesting}
            ingestStatus={ingestStatus}
            onIngestRepo={handleIngestRepo}
            onUnloadRepo={handleUnloadRepo}
            onSwitchToChat={() => setActiveTab('chat')}
            onSwitchToExplorer={() => setActiveTab('explorer')}
          />
        )}

        {activeTab === 'chat' && (
          <ChatStudio
            activeRepo={activeRepo}
            messages={messages}
            setMessages={setMessages}
            onNavigateToFile={handleNavigateToFile}
          />
        )}

        {activeTab === 'explorer' && (
          <CodeExplorer
            activeRepo={activeRepo}
            initialFilePath={navTargetFile}
            initialLineNumber={navTargetLine}
          />
        )}

        {activeTab === 'architecture' && (
          <ArchitectureView
            systemStatus={systemStatus}
            onRefreshStatus={fetchStatus}
            onCacheCleared={() => {
              setActiveRepo(null);
              setMessages([]);
            }}
          />
        )}
      </main>
    </div>
  );
}

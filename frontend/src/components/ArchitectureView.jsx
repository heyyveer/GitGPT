import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Search, 
  FileText, 
  Bug, 
  Layers, 
  ShieldCheck, 
  Database, 
  HardDrive, 
  Trash2, 
  CheckCircle2, 
  Activity, 
  ArrowRight, 
  Cpu, 
  RefreshCw,
  FolderGit2
} from 'lucide-react';

export default function ArchitectureView({ 
  systemStatus, 
  onRefreshStatus, 
  onCacheCleared 
}) {
  const [cacheData, setCacheData] = useState(null);
  const [loadingCache, setLoadingCache] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearMessage, setClearMessage] = useState(null);

  const fetchCache = async () => {
    setLoadingCache(true);
    try {
      const res = await fetch('/api/cache');
      if (res.ok) {
        const data = await res.json();
        setCacheData(data);
      }
    } catch (err) {
      console.error('Error fetching cache:', err);
    } finally {
      setLoadingCache(false);
    }
  };

  useEffect(() => {
    fetchCache();
  }, []);

  const handleClearCache = async () => {
    if (!window.confirm('Are you sure you want to clear all cloned repositories and FAISS vector indices from disk?')) {
      return;
    }

    setClearing(true);
    try {
      const res = await fetch('/api/cache', { method: 'DELETE' });
      if (res.ok) {
        const data = await res.json();
        setClearMessage(data.message);
        fetchCache();
        if (onRefreshStatus) onRefreshStatus();
        if (onCacheCleared) onCacheCleared();
      }
    } catch (err) {
      console.error('Error clearing cache:', err);
    } finally {
      setClearing(false);
    }
  };

  const agents = [
    {
      name: 'QueryRouter',
      role: 'Intelligent Intent Classifier',
      icon: Cpu,
      color: 'badge-primary',
      desc: 'Classifies user queries with temperature=0 into CODE_SEARCH, DOCUMENTATION, DEBUGGING, ARCHITECTURE, or GENERAL.'
    },
    {
      name: 'CodeSearchAgent',
      role: 'AST & Symbol Specialist',
      icon: Search,
      color: 'badge-cyan',
      desc: 'Retrieves exact code definitions, function signatures, classes, and variable references across AST nodes.'
    },
    {
      name: 'DocumentationAgent',
      role: 'Guide & Setup Specialist',
      icon: FileText,
      color: 'badge-amber',
      desc: 'Answers installation, usage, configuration (.env, pyproject.toml, package.json), and environment setup queries.'
    },
    {
      name: 'DebuggingAgent',
      role: 'Root Cause & Error Analyst',
      icon: Bug,
      color: 'badge-rose',
      desc: 'Pinpoints exception sources, runtime pitfalls, parameter bugs, and proposes verified code patches.'
    },
    {
      name: 'AnalysisAgent',
      role: 'System Architect',
      icon: Layers,
      color: 'badge-purple',
      desc: 'Synthesizes high-level system diagrams, component interactions, data pipelines, and architectural patterns.'
    },
    {
      name: 'VerificationAgent',
      role: 'Hallucination Guardrail',
      icon: ShieldCheck,
      color: 'badge-emerald',
      desc: 'Inspects generated answers against retrieved AST evidence to verify that every cited function and file strictly exists.'
    }
  ];

  return (
    <div className="architecture-container animate-fade-in">
      {/* Header */}
      <div className="arch-header glass-panel">
        <div className="arch-header-left">
          <div className="badge badge-primary">
            <Activity size={13} /> Architecture & Health
          </div>
          <h2>Multi-Agent Reasoning Swarm & Diagnostics</h2>
          <p>
            Autonomous pipeline orchestration combining AST parsing, semantic FAISS memory, specialized agent dispatch, and grounding verification.
          </p>
        </div>
      </div>

      {/* Visual Swarm Flowchart */}
      <div className="swarm-flow-card glass-panel">
        <h3>🧠 Autonomous Swarm Data Flow</h3>
        <div className="swarm-flow-diagram">
          {/* Node 1: User Input */}
          <div className="flow-node user-node">
            <div className="node-icon"><Bot size={18} /></div>
            <div className="node-info">
              <strong>User Query</strong>
              <span>Natural language prompt</span>
            </div>
          </div>

          <div className="flow-arrow"><ArrowRight size={18} /></div>

          {/* Node 2: Query Router */}
          <div className="flow-node router-node">
            <div className="node-icon"><Cpu size={18} /></div>
            <div className="node-info">
              <strong>Query Router</strong>
              <span>Zero-shot classification</span>
            </div>
          </div>

          <div className="flow-arrow"><ArrowRight size={18} /></div>

          {/* Node 3: Swarm */}
          <div className="flow-node swarm-node">
            <div className="node-icon"><Layers size={18} /></div>
            <div className="node-info">
              <strong>Specialized Agents</strong>
              <span>CodeSearch / Docs / Debug / Arch</span>
            </div>
          </div>

          <div className="flow-arrow"><ArrowRight size={18} /></div>

          {/* Node 4: Verifier */}
          <div className="flow-node verifier-node">
            <div className="node-icon"><ShieldCheck size={18} /></div>
            <div className="node-info">
              <strong>Verification Agent</strong>
              <span>Anti-hallucination check</span>
            </div>
          </div>

          <div className="flow-arrow"><ArrowRight size={18} /></div>

          {/* Node 5: Output */}
          <div className="flow-node output-node">
            <div className="node-icon"><CheckCircle2 size={18} /></div>
            <div className="node-info">
              <strong>Grounded Answer</strong>
              <span>With verified sources & citations</span>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Breakdown Grid */}
      <div className="agents-grid-section">
        <h3>🤖 Specialized Agent Capabilities</h3>
        <div className="agents-grid">
          {agents.map((agent, idx) => {
            const Icon = agent.icon;
            return (
              <div key={idx} className="agent-card glass-panel">
                <div className="agent-card-header">
                  <div className="agent-icon-box">
                    <Icon size={20} />
                  </div>
                  <div>
                    <h4 className="agent-name">{agent.name}</h4>
                    <span className={`badge ${agent.color}`}>{agent.role}</span>
                  </div>
                </div>
                <p className="agent-desc">{agent.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Storage & Vector Memory Cache Manager */}
      <div className="cache-manager-section glass-panel">
        <div className="cache-header-row">
          <div className="cache-title">
            <HardDrive size={20} className="brand-color" />
            <div>
              <h3>Local Storage & FAISS Vector Cache</h3>
              <p>View and manage locally isolated git repositories and FAISS vector embeddings on disk.</p>
            </div>
          </div>

          <div className="cache-actions">
            <button className="btn-secondary" onClick={fetchCache} disabled={loadingCache}>
              <RefreshCw size={14} className={loadingCache ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
            <button 
              className="btn-primary clear-cache-btn" 
              onClick={handleClearCache} 
              disabled={clearing}
            >
              <Trash2 size={14} />
              <span>{clearing ? 'Clearing...' : 'Purge All Local Cache'}</span>
            </button>
          </div>
        </div>

        {clearMessage && (
          <div className="cache-success-alert animate-fade-in">
            <CheckCircle2 size={16} className="text-emerald" />
            <span>{clearMessage}</span>
          </div>
        )}

        <div className="cache-lists-grid">
          {/* Cloned Repos */}
          <div className="cache-list-box">
            <div className="list-box-header">
              <FolderGit2 size={16} className="text-cyan" />
              <h4>Cloned Repositories ({cacheData?.cloned_repositories?.length || 0})</h4>
            </div>
            <div className="list-items-container">
              {cacheData?.cloned_repositories && cacheData.cloned_repositories.length > 0 ? (
                cacheData.cloned_repositories.map((repo, idx) => (
                  <div key={idx} className="cache-item-row">
                    <div className="cache-item-name">
                      📁 <strong>{repo.name}</strong>
                    </div>
                    <span className="badge badge-primary">{repo.formatted_size}</span>
                  </div>
                ))
              ) : (
                <div className="empty-cache-note">No cloned repositories on disk.</div>
              )}
            </div>
          </div>

          {/* Vector Indices */}
          <div className="cache-list-box">
            <div className="list-box-header">
              <Database size={16} className="text-purple" />
              <h4>FAISS Vector Indices ({cacheData?.vector_indices?.length || 0})</h4>
            </div>
            <div className="list-items-container">
              {cacheData?.vector_indices && cacheData.vector_indices.length > 0 ? (
                cacheData.vector_indices.map((idxItem, idx) => (
                  <div key={idx} className="cache-item-row">
                    <div className="cache-item-name">
                      🧩 <strong>{idxItem.name}</strong>
                    </div>
                    <span className="badge badge-purple">{idxItem.formatted_size}</span>
                  </div>
                ))
              ) : (
                <div className="empty-cache-note">No cached vector indices on disk.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

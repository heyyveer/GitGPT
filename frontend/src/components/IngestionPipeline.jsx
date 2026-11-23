import React, { useState } from 'react';
import { 
  GitBranch, 
  Layers, 
  FileCode2, 
  Database, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ArrowRight, 
  ExternalLink,
  HardDrive,
  Code2,
  RefreshCw,
  FolderOpen,
  MessageSquare,
  Sparkles,
  Zap,
  Trash2
} from 'lucide-react';

export default function IngestionPipeline({ 
  activeRepo, 
  ingesting, 
  ingestStatus, 
  onIngestRepo, 
  onUnloadRepo,
  onSwitchToChat,
  onSwitchToExplorer
}) {
  const [customUrl, setCustomUrl] = useState('https://github.com/Faridghr/Simple-RAG-Chatbot');
  const [forceReclone, setForceReclone] = useState(false);

  const steps = [
    { 
      id: 1, 
      title: 'Git Shallow Clone', 
      desc: 'Clones latest repository revision (depth=1) into local isolation storage.',
      threshold: 25,
      icon: GitBranch 
    },
    { 
      id: 2, 
      title: 'AST Discovery & File Filtering', 
      desc: 'Scans source trees, excludes lockfiles/binaries, computes LOC metrics.',
      threshold: 50,
      icon: FolderOpen 
    },
    { 
      id: 3, 
      title: 'AST Semantic Chunking', 
      desc: 'Parses Python AST definitions, methods, classes, and code boundaries.',
      threshold: 75,
      icon: FileCode2 
    },
    { 
      id: 4, 
      title: 'FAISS Vector Indexing & Swarm Init', 
      desc: 'Generates Gemini 768-dim embeddings and initializes multi-agent coordinator.',
      threshold: 100,
      icon: Database 
    },
  ];

  const getStepStatus = (stepThreshold) => {
    if (!ingesting && !activeRepo) return 'idle';
    if (ingestStatus?.error) return 'error';
    if (ingesting) {
      if (ingestStatus.progress >= stepThreshold) return 'completed';
      if (ingestStatus.progress >= stepThreshold - 25) return 'running';
      return 'pending';
    }
    if (activeRepo) return 'completed';
    return 'idle';
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="ingest-hub-container animate-fade-in">
      {/* Top Header */}
      <div className="ingest-header glass-panel">
        <div className="ingest-header-left">
          <div className="badge badge-primary">
            <Zap size={13} /> Pipeline Engine
          </div>
          <h2>Repository Ingestion & Vector Indexing</h2>
          <p>
            Transforms raw GitHub source code into structured AST nodes and semantic vector memory for high-precision agent retrieval.
          </p>
        </div>

        <div className="ingest-header-right">
          {activeRepo ? (
            <div className="repo-status-badge active">
              <span className="status-dot active"></span>
              <span>Loaded: <strong>{activeRepo.name}</strong></span>
            </div>
          ) : (
            <div className="repo-status-badge inactive">
              <span className="status-dot warning"></span>
              <span>No Codebase Loaded</span>
            </div>
          )}
        </div>
      </div>

      {/* Ingestion URL Bar */}
      <div className="ingest-input-card glass-panel">
        <h3>📥 Index Any Public GitHub Codebase</h3>
        <div className="ingest-input-row">
          <div className="input-with-icon">
            <GitBranch size={18} className="input-icon" />
            <input
              type="text"
              placeholder="https://github.com/owner/repository"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              disabled={ingesting}
            />
          </div>

          <label className="checkbox-label" title="Delete local cache and re-clone repository">
            <input
              type="checkbox"
              checked={forceReclone}
              onChange={(e) => setForceReclone(e.target.checked)}
              disabled={ingesting}
            />
            <span>Force Re-index</span>
          </label>

          <button
            className="btn-primary start-ingest-btn"
            onClick={() => onIngestRepo(customUrl, forceReclone)}
            disabled={ingesting || !customUrl.trim()}
          >
            {ingesting ? (
              <>
                <Clock size={16} className="animate-spin" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <Zap size={16} />
                <span>Start Ingestion</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Pipeline Tracker */}
      <div className="pipeline-tracker-card glass-panel">
        <div className="pipeline-tracker-header">
          <div className="tracker-title-row">
            <Layers size={18} className="brand-color" />
            <h3>Pipeline Stages & Execution Status</h3>
          </div>
          <span className="progress-percentage">
            {ingesting ? `${ingestStatus?.progress || 0}%` : activeRepo ? '100% Ready' : 'Standby'}
          </span>
        </div>

        {/* Global Progress Bar */}
        <div className="pipeline-progress-track">
          <div 
            className="pipeline-progress-bar"
            style={{ 
              width: `${ingesting ? (ingestStatus?.progress || 10) : activeRepo ? 100 : 0}%`,
              background: ingestStatus?.error ? 'var(--brand-rose)' : 'var(--gradient-brand)'
            }}
          ></div>
        </div>

        {ingestStatus?.step && ingesting && (
          <div className="pipeline-current-step animate-fade-in">
            <Clock size={14} className="animate-spin text-cyan" />
            <span>{ingestStatus.step}</span>
          </div>
        )}

        {ingestStatus?.error && (
          <div className="pipeline-error-box animate-fade-in">
            <AlertCircle size={16} className="text-rose" />
            <span>Ingestion Error: {ingestStatus.error}</span>
          </div>
        )}

        {/* Steps Grid */}
        <div className="pipeline-steps-grid">
          {steps.map((step) => {
            const Icon = step.icon;
            const status = getStepStatus(step.threshold);
            return (
              <div key={step.id} className={`pipeline-step-item ${status}`}>
                <div className="step-header">
                  <div className="step-number-icon">
                    <Icon size={16} />
                  </div>
                  <div className="step-status-tag">
                    {status === 'completed' && <span className="tag-complete"><CheckCircle2 size={13} /> Complete</span>}
                    {status === 'running' && <span className="tag-running"><Clock size={13} className="animate-spin" /> Running</span>}
                    {status === 'pending' && <span className="tag-pending">Pending</span>}
                    {status === 'error' && <span className="tag-error"><AlertCircle size={13} /> Error</span>}
                    {status === 'idle' && <span className="tag-idle">Stage {step.id}</span>}
                  </div>
                </div>

                <h4 className="step-title">{step.title}</h4>
                <p className="step-desc">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Codebase Analytics Section (when loaded) */}
      {activeRepo && (
        <div className="active-codebase-analytics glass-panel animate-fade-in">
          <div className="analytics-header">
            <div className="analytics-title">
              <Sparkles size={20} className="brand-color" />
              <div>
                <h3>Active Codebase: <span className="gradient-text">{activeRepo.name}</span></h3>
                <a href={activeRepo.url} target="_blank" rel="noopener noreferrer" className="repo-link">
                  {activeRepo.url} <ExternalLink size={12} />
                </a>
              </div>
            </div>

            <div className="analytics-actions">
              <button className="btn-primary" onClick={onSwitchToChat}>
                <MessageSquare size={16} />
                <span>Launch Chat Studio</span>
                <ArrowRight size={14} />
              </button>
              <button className="btn-secondary" onClick={onSwitchToExplorer}>
                <FileCode2 size={16} />
                <span>Explore Code & AST</span>
              </button>
              <button className="btn-ghost text-rose" onClick={onUnloadRepo} title="Unload from memory">
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {/* Metric Tiles */}
          <div className="metrics-grid">
            <div className="metric-tile">
              <div className="metric-icon-box cyan">
                <FolderOpen size={20} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Source Files</span>
                <span className="metric-value">{activeRepo.files_count}</span>
                <span className="metric-sub">Processed & parsed</span>
              </div>
            </div>

            <div className="metric-tile">
              <div className="metric-icon-box primary">
                <Code2 size={20} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Lines of Code</span>
                <span className="metric-value">{activeRepo.stats?.total_lines?.toLocaleString() || 0}</span>
                <span className="metric-sub">Total source lines</span>
              </div>
            </div>

            <div className="metric-tile">
              <div className="metric-icon-box emerald">
                <Database size={20} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Vector Chunks</span>
                <span className="metric-value">{activeRepo.chunks_count?.toLocaleString() || 0}</span>
                <span className="metric-sub">AST & Semantic embeddings</span>
              </div>
            </div>

            <div className="metric-tile">
              <div className="metric-icon-box amber">
                <HardDrive size={20} />
              </div>
              <div className="metric-info">
                <span className="metric-label">Disk Storage</span>
                <span className="metric-value">{formatBytes(activeRepo.stats?.total_size_bytes)}</span>
                <span className="metric-sub">Local cloned repo</span>
              </div>
            </div>
          </div>

          {/* Languages Breakdown */}
          {activeRepo.stats?.languages && Object.keys(activeRepo.stats.languages).length > 0 && (
            <div className="language-breakdown-section">
              <h4>💻 File Type & Language Distribution</h4>
              <div className="lang-chips-grid">
                {Object.entries(activeRepo.stats.languages)
                  .sort((a, b) => b[1] - a[1])
                  .map(([ext, count], idx) => (
                    <div key={idx} className="lang-stat-card">
                      <div className="lang-stat-header">
                        <span className="lang-ext-badge">{ext || 'other'}</span>
                        <span className="lang-count">{count} files</span>
                      </div>
                      <div className="lang-bar-track">
                        <div 
                          className="lang-bar-fill" 
                          style={{ width: `${Math.min(100, Math.max(15, (count / activeRepo.files_count) * 100))}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

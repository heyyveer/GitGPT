import React, { useState } from 'react';
import { 
  Bot, 
  GitBranch, 
  Sparkles, 
  Cpu, 
  Layers, 
  FolderGit2, 
  MessageSquare, 
  FileCode2, 
  Activity, 
  Search,
  ExternalLink,
  ChevronDown,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  X
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  activeRepo, 
  systemStatus, 
  selectedModel, 
  onModelChange, 
  onUnloadRepo 
}) {
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  const navItems = [
    { id: 'search', label: '🔍 Search Repos', icon: Search },
    { id: 'discovery', label: '1. Discover Repos', icon: FolderGit2 },
    { id: 'ingest', label: '2. Ingestion Hub', icon: GitBranch, badge: activeRepo ? 'Loaded' : null },
    { id: 'chat', label: '3. Multi-Agent Studio', icon: MessageSquare, highlight: !!activeRepo },
    { id: 'explorer', label: '4. Code & AST Explorer', icon: FileCode2, disabled: !activeRepo },
    { id: 'architecture', label: '5. Swarm & Health', icon: Activity },
  ];

  return (
    <header className="navbar-container">
      <div className="navbar-left">
        <div className="brand-logo" onClick={() => setActiveTab('discovery')}>
          <div className="logo-icon-wrapper">
            <Bot size={22} className="logo-bot-icon" />
            <Sparkles size={12} className="logo-sparkle" />
          </div>
          <div className="brand-titles">
            <div className="brand-name">
              <span>TalkTo</span><span className="gradient-text">GitHub</span>
            </div>
            <span className="brand-tagline">Multi-Agent Code Intelligence</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-tab-btn ${isActive ? 'active' : ''} ${item.disabled ? 'disabled' : ''} ${item.highlight && !isActive ? 'glow-tab' : ''}`}
                onClick={() => !item.disabled && setActiveTab(item.id)}
                disabled={item.disabled}
                title={item.disabled ? 'Ingest a repository to view code' : item.label}
              >
                <Icon size={16} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="tab-pill badge-emerald">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="navbar-right">
        {/* Active Repo Quick Chip */}
        {activeRepo ? (
          <div className="active-repo-chip" title={activeRepo.url}>
            <GitBranch size={14} className="repo-chip-icon" />
            <span className="repo-chip-name">{activeRepo.name}</span>
            <span className="repo-chip-files">{activeRepo.files_count} files</span>
            <button 
              className="repo-chip-unload" 
              onClick={(e) => { e.stopPropagation(); onUnloadRepo(); }} 
              title="Unload Repository"
            >
              <X size={13} />
            </button>
          </div>
        ) : (
          <div className="no-repo-chip" onClick={() => setActiveTab('discovery')}>
            <span className="status-dot warning"></span>
            <span>No Repo Loaded</span>
          </div>
        )}

        {/* Model Selector Dropdown */}
        <div className="model-selector-wrapper">
          <button 
            className="model-select-btn" 
            onClick={() => setShowModelDropdown(!showModelDropdown)}
          >
            <Cpu size={14} className="model-icon" />
            <span className="model-name">
              {systemStatus?.available_models?.find(m => m.id === selectedModel)?.name || selectedModel || 'Select Model'}
            </span>
            <ChevronDown size={14} />
          </button>

          {showModelDropdown && (
            <div className="model-dropdown-menu">
              <div className="dropdown-header">Inference & Reasoning LLM</div>
              {systemStatus?.available_models?.map((model) => (
                <div
                  key={model.id}
                  className={`model-option ${selectedModel === model.id ? 'selected' : ''}`}
                  onClick={() => {
                    onModelChange(model.id);
                    setShowModelDropdown(false);
                  }}
                >
                  <div className="model-option-info">
                    <span className="model-opt-name">{model.name}</span>
                    <span className="model-opt-id">{model.id}</span>
                  </div>
                  <span className="badge badge-primary">{model.provider}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Health / API Status Button */}
        <button 
          className="health-status-btn"
          onClick={() => setShowStatusModal(true)}
          title="View Service Status"
        >
          <span className={`status-dot ${systemStatus?.services?.groq && systemStatus?.services?.gemini ? 'active' : 'warning'}`}></span>
          <span className="status-text">Services</span>
        </button>
      </div>

      {/* Service Status Modal */}
      {showStatusModal && (
        <div className="modal-backdrop" onClick={() => setShowStatusModal(false)}>
          <div className="modal-card glass-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <Activity size={18} className="brand-color" />
                <h3>System Services & API Status</h3>
              </div>
              <button className="btn-ghost" onClick={() => setShowStatusModal(false)}>
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <div className="service-row">
                <div className="service-info">
                  <strong>Groq LLM Engine</strong>
                  <span>High-speed query routing & specialized agent reasoning</span>
                </div>
                {systemStatus?.services?.groq ? (
                  <span className="badge badge-emerald"><CheckCircle2 size={13} /> Active</span>
                ) : (
                  <span className="badge badge-rose"><AlertCircle size={13} /> Missing Key</span>
                )}
              </div>

              <div className="service-row">
                <div className="service-info">
                  <strong>Google Gemini</strong>
                  <span>Multimodal embeddings & Gemini reasoning models</span>
                </div>
                {systemStatus?.services?.gemini ? (
                  <span className="badge badge-emerald"><CheckCircle2 size={13} /> Active</span>
                ) : (
                  <span className="badge badge-rose"><AlertCircle size={13} /> Missing Key</span>
                )}
              </div>

              <div className="service-row">
                <div className="service-info">
                  <strong>GitHub API Access</strong>
                  <span>Code search, metadata parsing & repository cloning</span>
                </div>
                {systemStatus?.services?.github ? (
                  <span className="badge badge-emerald"><CheckCircle2 size={13} /> Authenticated</span>
                ) : (
                  <span className="badge badge-amber"><AlertCircle size={13} /> Public Limit</span>
                )}
              </div>

              <div className="cache-info-box">
                <h4>Storage & Vector Memory</h4>
                <div className="cache-stats-row">
                  <div>Cloned Codebases: <strong>{systemStatus?.cache_stats?.cloned_count ?? 0}</strong></div>
                  <div>FAISS Vector Stores: <strong>{systemStatus?.cache_stats?.indices_count ?? 0}</strong></div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={() => setShowStatusModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

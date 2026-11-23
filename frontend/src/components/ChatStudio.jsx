import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Bot, 
  User, 
  Send, 
  Sparkles, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Code2, 
  Layers, 
  Copy, 
  Check, 
  Trash2, 
  Download, 
  ChevronDown, 
  ChevronUp, 
  FileCode, 
  ExternalLink,
  HelpCircle,
  Cpu,
  Search
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  { label: '📖 Installation & Setup', prompt: 'How do I install, configure dependencies, and run this project?' },
  { label: '🔍 Vector Store & Embeddings', prompt: 'Where is the vector store or database initialized and used in the code?' },
  { label: '🏛️ System Architecture', prompt: 'Explain the overall architecture, data flow, and key components of this codebase.' },
  { label: '🐛 Bugs & Exception Handling', prompt: 'What potential errors or exceptions might occur in the main execution flow and how to fix them?' },
  { label: '⚡ Core Algorithms', prompt: 'What are the core algorithms or pipelines implemented in this repository?' }
];

export default function ChatStudio({ 
  activeRepo, 
  messages, 
  setMessages, 
  onNavigateToFile 
}) {
  const [inputPrompt, setInputPrompt] = useState('');
  const [routingMode, setRoutingMode] = useState('AUTO');
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const [expandedChunks, setExpandedChunks] = useState({});

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend = null) => {
    const query = (textToSend || inputPrompt).trim();
    if (!query || loading || !activeRepo) return;

    const userMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputPrompt('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          manual_route: routingMode === 'AUTO' ? null : routingMode,
          history: messages.map(m => ({ role: m.role, content: m.content })).slice(-6)
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Agent response failed');
      }

      const data = await res.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        agent: data.agent,
        route: data.route,
        latency: data.latency_seconds,
        sources: data.sources || [],
        documents: data.documents || [],
        verification: data.verification || { verified: true, confidence: 1.0 },
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ **Error during agent execution**: ${err.message}\n\nPlease check that your API keys are configured and try again.`,
        agent: 'SystemCoordinator',
        route: 'ERROR',
        latency: 0,
        verification: { verified: false, confidence: 0, reason: err.message },
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const toggleSources = (idx) => {
    setExpandedSources((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleChunks = (idx) => {
    setExpandedChunks((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const clearChat = () => {
    if (window.confirm('Clear all conversation history?')) {
      setMessages([]);
    }
  };

  const exportChat = () => {
    const mdContent = messages.map(m => `### ${m.role.toUpperCase()} (${m.agent || 'User'}):\n\n${m.content}\n\n---\n`).join('\n');
    const blob = new Blob([mdContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `TalkToGitHub_${activeRepo?.name || 'chat'}_transcript.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!activeRepo) {
    return (
      <div className="chat-empty-state glass-panel animate-fade-in">
        <Bot size={48} className="empty-bot-icon" />
        <h2>No Repository Loaded</h2>
        <p>
          Please search for a repository in <strong>Discover Repos</strong> or ingest a custom GitHub URL 
          in <strong>Ingestion Hub</strong> to start conversing with the specialized multi-agent swarm.
        </p>
      </div>
    );
  }

  return (
    <div className="chat-studio-container animate-fade-in">
      {/* Studio Header Bar */}
      <div className="chat-studio-header glass-panel">
        <div className="studio-header-left">
          <div className="active-repo-badge">
            <span className="status-dot active"></span>
            <span>Codebase: <strong>{activeRepo.name}</strong></span>
          </div>

          {/* Routing Selector */}
          <div className="route-select-wrapper">
            <label>Agent Routing:</label>
            <select 
              value={routingMode} 
              onChange={(e) => setRoutingMode(e.target.value)}
              className="route-select"
            >
              <option value="AUTO">🤖 AUTO (Smart Query Router)</option>
              <option value="CODE_SEARCH">🔍 CodeSearchAgent</option>
              <option value="DOCUMENTATION">📖 DocumentationAgent</option>
              <option value="DEBUGGING">🐛 DebuggingAgent</option>
              <option value="ARCHITECTURE">🏛️ AnalysisAgent (Architecture)</option>
            </select>
          </div>
        </div>

        <div className="studio-header-right">
          <button className="btn-ghost" onClick={exportChat} title="Export transcript as Markdown">
            <Download size={15} />
            <span>Export</span>
          </button>
          <button className="btn-ghost text-rose" onClick={clearChat} title="Clear conversation history">
            <Trash2 size={15} />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Suggested Prompts Banner */}
      <div className="suggested-prompts-bar">
        <span className="prompts-label"><Sparkles size={13} /> Quick Prompts:</span>
        <div className="prompts-scroll-row">
          {SUGGESTED_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              className="suggested-prompt-btn"
              onClick={() => handleSendMessage(item.prompt)}
              disabled={loading}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages-viewport">
        {messages.length === 0 ? (
          <div className="chat-welcome-placeholder">
            <div className="welcome-avatar">
              <Bot size={36} />
            </div>
            <h3>Ready for Multi-Agent Code Intelligence</h3>
            <p>
              Ask any question about <strong>{activeRepo.name}</strong>. The coordinator will route 
              to specialized agents, perform AST & vector retrieval, and verify answers for hallucination-free code insights.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const isVerified = msg.verification?.verified !== false;
            const confidence = msg.verification?.confidence ? Math.round(msg.verification.confidence * 100) : 100;

            return (
              <div 
                key={idx} 
                className={`chat-message-row ${isUser ? 'user-row' : 'assistant-row'} animate-fade-in`}
              >
                <div className="message-avatar">
                  {isUser ? <User size={18} /> : <Bot size={18} />}
                </div>

                <div className="message-content-wrapper">
                  {/* Assistant Agent Telemetry Header */}
                  {!isUser && (
                    <div className="agent-telemetry-header">
                      <div className="telemetry-tags">
                        <span className="badge badge-primary">
                          <Bot size={12} /> {msg.agent || 'MultiAgentCoordinator'}
                        </span>
                        {msg.route && (
                          <span className="badge badge-cyan">
                            🎯 Route: {msg.route}
                          </span>
                        )}
                        <span className={`badge ${isVerified ? 'badge-emerald' : 'badge-rose'}`} title={msg.verification?.reason}>
                          {isVerified ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                          {isVerified ? `Verified (${confidence}%)` : 'Unverified Notice'}
                        </span>
                        {msg.latency !== undefined && (
                          <span className="badge badge-amber">
                            <Clock size={12} /> {msg.latency}s
                          </span>
                        )}
                      </div>

                      <button
                        className="btn-ghost copy-msg-btn"
                        onClick={() => handleCopy(msg.content, idx)}
                        title="Copy answer"
                      >
                        {copiedIndex === idx ? <Check size={13} className="text-emerald" /> : <Copy size={13} />}
                      </button>
                    </div>
                  )}

                  {/* Message Body */}
                  <div className="message-bubble glass-panel">
                    <div className="markdown-render">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Verified Code References Drawer */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-drawer">
                        <button 
                          className="sources-toggle-btn"
                          onClick={() => toggleSources(idx)}
                        >
                          <div className="toggle-left">
                            <FileCode size={14} className="text-cyan" />
                            <span>📍 Verified Code References ({msg.sources.length} sources)</span>
                          </div>
                          {expandedSources[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>

                        {expandedSources[idx] && (
                          <div className="sources-list animate-fade-in">
                            {msg.sources.map((src, sidx) => (
                              <div key={sidx} className="source-item-card">
                                <div className="source-item-header">
                                  <span className="source-file-path">
                                    📁 <strong>{src.file_path}</strong> (Lines {src.start_line || 1}-{src.end_line || 1})
                                  </span>
                                  {src.symbol && (
                                    <span className="source-symbol-tag">
                                      Symbol: <code>{src.symbol}</code>
                                    </span>
                                  )}
                                  {onNavigateToFile && (
                                    <button 
                                      className="source-jump-btn"
                                      onClick={() => onNavigateToFile(src.file_path, src.start_line)}
                                      title="Open in Code Explorer"
                                    >
                                      <ExternalLink size={12} /> View Code
                                    </button>
                                  )}
                                </div>
                                {src.full_chunk && (
                                  <pre className="source-code-snippet">
                                    <code>{src.full_chunk.slice(0, 350)}{src.full_chunk.length > 350 ? '...' : ''}</code>
                                  </pre>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Technical Context Chunks Drawer */}
                    {msg.documents && msg.documents.length > 0 && (
                      <div className="chunks-drawer">
                        <button 
                          className="chunks-toggle-btn"
                          onClick={() => toggleChunks(idx)}
                        >
                          <div className="toggle-left">
                            <Layers size={14} className="text-purple" />
                            <span>🔍 Technical Evidence: Vector Chunks ({msg.documents.length})</span>
                          </div>
                          {expandedChunks[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>

                        {expandedChunks[idx] && (
                          <div className="chunks-list animate-fade-in">
                            {msg.documents.map((doc, didx) => (
                              <div key={didx} className="chunk-item-card">
                                <div className="chunk-header">
                                  <span>Chunk #{didx + 1} — <code>{doc.metadata?.file_path || 'unknown'}</code></span>
                                </div>
                                <pre className="chunk-code-preview">
                                  <code>{doc.page_content}</code>
                                </pre>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <span className="message-time">{msg.timestamp}</span>
                </div>
              </div>
            );
          })
        )}

        {/* Loading Spinner during Agent Reasoning */}
        {loading && (
          <div className="chat-message-row assistant-row animate-fade-in">
            <div className="message-avatar">
              <Bot size={18} />
            </div>
            <div className="message-content-wrapper">
              <div className="thinking-bubble glass-panel">
                <div className="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="thinking-text">
                  Swarm coordinating agents, running AST retrieval & verifying code claims...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="chat-input-container glass-panel">
        <div className="input-box-wrapper">
          <textarea
            ref={inputRef}
            className="chat-textarea"
            rows="1"
            placeholder={`Ask anything about ${activeRepo.name} (e.g. Where is the main router defined?)...`}
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={loading}
          />

          <button
            className="btn-primary send-button"
            onClick={() => handleSendMessage()}
            disabled={loading || !inputPrompt.trim()}
          >
            {loading ? <Clock size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}

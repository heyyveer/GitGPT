import React, { useState } from 'react';
import { 
  Search, 
  Sparkles, 
  Star, 
  GitFork, 
  Code2, 
  ExternalLink, 
  Zap, 
  ArrowRight,
  Filter,
  CheckCircle,
  Clock,
  Flame
} from 'lucide-react';

const QUICK_TOPICS = [
  { label: '🤖 RAG LangChain Chatbot', query: 'RAG chatbot LangChain vector database', lang: 'Python' },
  { label: '⚡ FastAPI Microservice', query: 'FastAPI async backend microservice API', lang: 'Python' },
  { label: '🧠 Multi-Agent AI Swarm', query: 'multi agent reasoning autonomous swarm LLM', lang: 'Python' },
  { label: '👁️ Computer Vision PyTorch', query: 'PyTorch deep learning computer vision transformer', lang: 'Python' },
  { label: '⚡ Next.js Fullstack AI App', query: 'Next.js React AI chatbot typescript tailwind', lang: 'TypeScript' }
];

const POPULAR_REPOS = [
  { name: 'Faridghr/Simple-RAG-Chatbot', url: 'https://github.com/Faridghr/Simple-RAG-Chatbot', desc: 'Lightweight LangChain + FAISS + Gemini RAG chatbot' },
  { name: 'tiangolo/fastapi', url: 'https://github.com/tiangolo/fastapi', desc: 'Modern, fast (high-performance), web framework for building APIs' },
  { name: 'hwchase17/langchain', url: 'https://github.com/langchain-ai/langchain', desc: 'Building applications with LLMs through composability' }
];

export default function RepoDiscovery({ 
  onIngestRepo, 
  ingesting, 
  activeRepo, 
  onSwitchToChat 
}) {
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('All');
  const [minStars, setMinStars] = useState(0);
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  // Direct URL Ingestion state
  const [directUrl, setDirectUrl] = useState('https://github.com/Faridghr/Simple-RAG-Chatbot');
  const [forceReclone, setForceReclone] = useState(false);

  const handleSearch = async (overrideQuery = null, overrideLang = null) => {
    const q = (overrideQuery !== null ? overrideQuery : query).trim();
    if (!q) {
      setError('Please enter what you want to build or explore.');
      return;
    }
    setError(null);
    setSearching(true);

    try {
      const langParam = overrideLang || language;
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          language: langParam === 'All' ? null : langParam,
          min_stars: Number(minStars) || 0,
          top_k: 8
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to search GitHub');
      }

      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  };

  const handleQuickTopic = (topic) => {
    setQuery(topic.query);
    if (topic.lang) setLanguage(topic.lang);
    handleSearch(topic.query, topic.lang);
  };

  return (
    <div className="discovery-container animate-fade-in">
      {/* Hero Welcome Banner */}
      <section className="discovery-hero glass-panel">
        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles size={14} className="sparkle-spin" />
            <span>Autonomous Multi-Agent Code Intelligence</span>
          </div>
          <h1 className="hero-heading">
            Talk to Any <span className="gradient-text">GitHub Repository</span>
          </h1>
          <p className="hero-subtext">
            Search, discover, AST-index, and converse with full codebases using an autonomous swarm of 
            Code Search, Documentation, Debugging, Architecture, and Verification agents.
          </p>

          {/* Direct URL Ingest Bar */}
          <div className="direct-ingest-box">
            <div className="direct-input-group">
              <span className="input-prefix">https://github.com/</span>
              <input
                type="text"
                placeholder="owner/repository-name (e.g. Faridghr/Simple-RAG-Chatbot)"
                value={directUrl.replace('https://github.com/', '')}
                onChange={(e) => {
                  const val = e.target.value;
                  setDirectUrl(val.startsWith('http') ? val : `https://github.com/${val}`);
                }}
                onKeyDown={(e) => e.key === 'Enter' && onIngestRepo(directUrl, forceReclone)}
              />
              <label className="checkbox-label" title="Clear local cache and clone fresh">
                <input
                  type="checkbox"
                  checked={forceReclone}
                  onChange={(e) => setForceReclone(e.target.checked)}
                />
                <span>Force Re-index</span>
              </label>
              <button
                className="btn-primary ingest-btn"
                onClick={() => onIngestRepo(directUrl, forceReclone)}
                disabled={ingesting || !directUrl.trim()}
              >
                {ingesting ? (
                  <>
                    <Zap size={16} className="animate-spin" />
                    <span>Ingesting...</span>
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    <span>Ingest & Chat</span>
                  </>
                )}
              </button>
            </div>

            {/* Quick Pick Samples */}
            <div className="sample-repos-row">
              <span className="sample-label">Quick load:</span>
              {POPULAR_REPOS.map((r, i) => (
                <button
                  key={i}
                  className="sample-repo-pill"
                  onClick={() => {
                    setDirectUrl(r.url);
                    onIngestRepo(r.url, false);
                  }}
                  title={r.desc}
                >
                  {r.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Semantic Repository Search Section */}
      <section className="search-section">
        <div className="section-title-row">
          <div className="section-header-left">
            <Flame size={20} className="flame-icon" />
            <h2>Discover & Rank Repositories by Goal</h2>
          </div>
          <span className="section-subtitle">
            Semantic match powered by GitHub Search API & Multi-Factor Ranking
          </span>
        </div>

        {/* Search & Filter Controls */}
        <div className="search-bar-card glass-panel">
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input-field"
              placeholder="What do you want to build or explore? (e.g., Simple RAG Chatbot with LangChain and FAISS)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>

          <div className="filter-controls-row">
            <div className="filter-item">
              <label>Language:</label>
              <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
                className="custom-select"
              >
                <option value="All">All Languages</option>
                <option value="Python">Python</option>
                <option value="TypeScript">TypeScript</option>
                <option value="JavaScript">JavaScript</option>
                <option value="Go">Go</option>
                <option value="Rust">Rust</option>
                <option value="C++">C++</option>
                <option value="Java">Java</option>
              </select>
            </div>

            <div className="filter-item">
              <label>Min Stars:</label>
              <input
                type="number"
                min="0"
                step="50"
                className="number-input"
                value={minStars}
                onChange={(e) => setMinStars(e.target.value)}
              />
            </div>

            <button 
              className="btn-primary search-action-btn"
              onClick={() => handleSearch()}
              disabled={searching}
            >
              {searching ? (
                <>
                  <Clock size={16} className="animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search size={16} />
                  <span>Search GitHub</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Topic Chips */}
          <div className="quick-topics-row">
            <span className="quick-topics-label">Suggested Goals:</span>
            {QUICK_TOPICS.map((topic, idx) => (
              <button
                key={idx}
                className="quick-topic-chip"
                onClick={() => handleQuickTopic(topic)}
              >
                {topic.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="error-alert animate-fade-in">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Search Results List */}
        {results.length > 0 && (
          <div className="search-results-grid animate-fade-in">
            <div className="results-header">
              <h3>🏆 Top {results.length} Ranked Codebases</h3>
              <span className="results-badge">{results.length} Repositories Ready</span>
            </div>

            <div className="results-cards">
              {results.map((repo, idx) => {
                const isCurrentActive = activeRepo && activeRepo.name.toLowerCase() === repo.name.toLowerCase();
                return (
                  <div key={idx} className={`repo-card glass-panel ${isCurrentActive ? 'active-repo-border' : ''}`}>
                    <div className="repo-card-top">
                      <div className="repo-card-header">
                        <span className="rank-badge">#{idx + 1}</span>
                        <h4 className="repo-title">
                          <a href={repo.url} target="_blank" rel="noopener noreferrer">
                            {repo.name}
                            <ExternalLink size={13} className="ext-icon" />
                          </a>
                        </h4>
                      </div>

                      <div className="repo-metrics-row">
                        <span className="badge badge-primary">
                          <Star size={13} fill="currentColor" /> {Number(repo.stars).toLocaleString()}
                        </span>
                        <span className="badge badge-cyan">
                          <GitFork size={13} /> {Number(repo.forks).toLocaleString()}
                        </span>
                        {repo.language && (
                          <span className="badge badge-amber">
                            <Code2 size={13} /> {repo.language}
                          </span>
                        )}
                        <span className="badge badge-emerald" title="Multi-factor semantic score">
                          Score: {repo.relevance_score || '90'}
                        </span>
                      </div>
                    </div>

                    <p className="repo-desc">
                      {repo.description || 'No description provided by repository owner.'}
                    </p>

                    {repo.topics && repo.topics.length > 0 && (
                      <div className="repo-topics-list">
                        {repo.topics.slice(0, 5).map((topic, tidx) => (
                          <span key={tidx} className="topic-pill">
                            #{topic}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="repo-card-footer">
                      {isCurrentActive ? (
                        <button className="btn-secondary active-loaded-btn" onClick={onSwitchToChat}>
                          <CheckCircle size={15} className="text-emerald" />
                          <span>Currently Active — Chat Now</span>
                          <ArrowRight size={14} />
                        </button>
                      ) : (
                        <button
                          className="btn-primary ingest-card-btn"
                          onClick={() => onIngestRepo(repo.url, false)}
                          disabled={ingesting}
                        >
                          <Zap size={15} />
                          <span>Ingest & Start Multi-Agent Reasoning</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

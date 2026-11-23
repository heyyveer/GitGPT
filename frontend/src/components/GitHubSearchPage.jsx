import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Sparkles, 
  Star, 
  GitFork, 
  Code2, 
  ExternalLink, 
  Copy, 
  Check, 
  AlertCircle, 
  Clock, 
  FolderGit2, 
  Scale, 
  CircleDot, 
  X, 
  SlidersHorizontal,
  Flame,
  ArrowUpRight
} from 'lucide-react';

const LANGUAGE_COLORS = {
  python: '#3572A5',
  typescript: '#3178c6',
  javascript: '#f1e05a',
  go: '#00ADD8',
  rust: '#dea584',
  'c++': '#f34b7d',
  c: '#555555',
  java: '#b07219',
  'c#': '#178600',
  php: '#4F5D95',
  swift: '#F05138',
  kotlin: '#A97BFF',
  ruby: '#701516',
  shell: '#89e051',
  html: '#e34c26',
  css: '#563d7c'
};

const SUGGESTED_TOPICS = [
  { label: '🤖 RAG LangChain', query: 'RAG LangChain vector database', lang: 'Python' },
  { label: '⚡ FastAPI Microservice', query: 'FastAPI async microservice', lang: 'Python' },
  { label: '🧠 Multi-Agent AI', query: 'multi agent swarm LLM autonomous', lang: 'Python' },
  { label: '🌐 Next.js AI Template', query: 'nextjs react ai fullstack tailwind', lang: 'TypeScript' },
  { label: '🦀 High-Performance Rust', query: 'rust cli async tokio performance', lang: 'Rust' },
  { label: '🚀 Golang Microservices', query: 'golang grpc microservice backend', lang: 'Go' },
  { label: '👁️ Computer Vision', query: 'pytorch computer vision transformer', lang: 'Python' },
];

export default function GitHubSearchPage() {
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('All');
  const [minStars, setMinStars] = useState(0);
  const [sort, setSort] = useState('best-match');
  const [topK, setTopK] = useState(12);
  const [results, setResults] = useState([]);
  const [lastSearchedQuery, setLastSearchedQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [copiedUrl, setCopiedUrl] = useState(null);
  const [copiedClone, setCopiedClone] = useState(null);

  // Perform repository search
  const handleSearch = async (overrideQuery = null, overrideLang = null) => {
    const q = (overrideQuery !== null ? overrideQuery : query).trim();
    if (!q) {
      setError('Please enter keywords, a topic, or repository name to search.');
      return;
    }

    setError(null);
    setSearching(true);
    setLastSearchedQuery(q);

    try {
      const activeLang = overrideLang !== null ? overrideLang : language;
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          language: activeLang === 'All' ? null : activeLang,
          min_stars: Number(minStars) || 0,
          sort: sort,
          top_k: Number(topK) || 12
        })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Search request failed' }));
        throw new Error(data.detail || 'Failed to search GitHub');
      }

      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || 'An error occurred while querying GitHub API.');
    } finally {
      setSearching(false);
    }
  };

  const handleQuickTopic = (topic) => {
    setQuery(topic.query);
    if (topic.lang) {
      setLanguage(topic.lang);
    }
    handleSearch(topic.query, topic.lang);
  };

  const handleCopyLink = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  const handleCopyClone = (cloneUrl, id) => {
    const cmd = `git clone ${cloneUrl}`;
    navigator.clipboard.writeText(cmd);
    setCopiedClone(id);
    setTimeout(() => setCopiedClone(null), 2000);
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toLocaleString();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return null;
    }
  };

  const getLanguageColor = (lang) => {
    if (!lang) return '#94a3b8';
    return LANGUAGE_COLORS[lang.toLowerCase()] || '#818cf8';
  };

  return (
    <div className="pure-search-page-container animate-fade-in">
      {/* Top Banner */}
      <header className="pure-search-hero glass-panel">
        <div className="pure-search-hero-content">
          <div className="pure-search-tag">
            <Sparkles size={14} className="sparkle-spin" />
            <span>GitHub Repository Discovery Engine</span>
          </div>
          <h1 className="pure-search-title">
            Search <span className="gradient-text">GitHub Repositories</span>
          </h1>
          <p className="pure-search-subtitle">
            Find and explore public open-source projects, libraries, and frameworks directly from GitHub with smart ranking.
          </p>
        </div>
      </header>

      {/* Search & Filter Card */}
      <section className="pure-search-controls-card glass-panel">
        {/* Main Search Input */}
        <div className="pure-search-input-group">
          <div className="pure-search-input-wrapper">
            <Search size={20} className="pure-search-input-icon" />
            <input
              type="text"
              className="pure-search-main-input"
              placeholder="Search by keywords, topic, library (e.g. LangChain, FastAPI, PyTorch, React, Vector DB)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              autoFocus
            />
            {query && (
              <button 
                type="button"
                className="pure-search-clear-btn"
                onClick={() => setQuery('')}
                title="Clear input"
              >
                <X size={16} />
              </button>
            )}
          </div>
          <button 
            type="button"
            className="btn-primary pure-search-btn"
            onClick={() => handleSearch()}
            disabled={searching}
          >
            {searching ? (
              <>
                <Clock size={18} className="animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Search size={18} />
                <span>Search Repos</span>
              </>
            )}
          </button>
        </div>

        {/* Filter Controls Bar */}
        <div className="pure-search-filters-bar">
          <div className="filter-group">
            <label className="filter-label">
              <Code2 size={14} />
              <span>Language:</span>
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="pure-filter-select"
            >
              <option value="All">All Languages</option>
              <option value="Python">Python</option>
              <option value="TypeScript">TypeScript</option>
              <option value="JavaScript">JavaScript</option>
              <option value="Go">Go</option>
              <option value="Rust">Rust</option>
              <option value="C++">C++</option>
              <option value="Java">Java</option>
              <option value="C#">C#</option>
              <option value="PHP">PHP</option>
              <option value="Swift">Swift</option>
              <option value="Kotlin">Kotlin</option>
              <option value="Ruby">Ruby</option>
              <option value="Shell">Shell</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">
              <SlidersHorizontal size={14} />
              <span>Sort By:</span>
            </label>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="pure-filter-select"
            >
              <option value="best-match">Best Match</option>
              <option value="stars">Most Stars</option>
              <option value="forks">Most Forks</option>
              <option value="updated">Recently Updated</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">
              <Star size={14} />
              <span>Min Stars:</span>
            </label>
            <select
              value={minStars}
              onChange={(e) => setMinStars(Number(e.target.value))}
              className="pure-filter-select"
            >
              <option value="0">Any Stars</option>
              <option value="50">50+ Stars</option>
              <option value="100">100+ Stars</option>
              <option value="500">500+ Stars</option>
              <option value="1000">1,000+ Stars</option>
              <option value="5000">5,000+ Stars</option>
              <option value="10000">10,000+ Stars</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">
              <span>Limit:</span>
            </label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="pure-filter-select"
            >
              <option value="8">8 Repos</option>
              <option value="12">12 Repos</option>
              <option value="20">20 Repos</option>
              <option value="30">30 Repos</option>
            </select>
          </div>
        </div>

        {/* Suggested Quick Searches */}
        <div className="pure-search-quick-topics">
          <div className="quick-topics-title">
            <Flame size={14} className="flame-icon" />
            <span>Popular Searches:</span>
          </div>
          <div className="quick-topics-chips">
            {SUGGESTED_TOPICS.map((topic, idx) => (
              <button
                key={idx}
                type="button"
                className="pure-topic-chip"
                onClick={() => handleQuickTopic(topic)}
              >
                {topic.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Error Alert */}
      {error && (
        <div className="pure-search-error-alert animate-fade-in">
          <AlertCircle size={18} className="error-icon" />
          <div className="error-text">
            <strong>Search Warning:</strong> {error}
          </div>
          <button 
            className="error-dismiss-btn"
            onClick={() => setError(null)}
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Results Section */}
      <section className="pure-search-results-section">
        {searching ? (
          <div className="pure-search-loading-state glass-panel">
            <div className="loading-spinner-ring"></div>
            <h3>Searching GitHub Repositories...</h3>
            <p>Querying GitHub API and computing semantic relevance ranking</p>
          </div>
        ) : results.length > 0 ? (
          <div className="pure-search-results-container animate-fade-in">
            {/* Results Header */}
            <div className="pure-results-summary-bar">
              <div className="summary-left">
                <FolderGit2 size={18} className="summary-icon" />
                <span className="summary-title">
                  Found <strong>{results.length}</strong> repositories for <em>"{lastSearchedQuery}"</em>
                </span>
              </div>
              <div className="summary-badges">
                {language !== 'All' && (
                  <span className="summary-pill">Lang: {language}</span>
                )}
                {minStars > 0 && (
                  <span className="summary-pill">Min Stars: {minStars}+</span>
                )}
                <span className="summary-pill">Sort: {sort}</span>
              </div>
            </div>

            {/* Repositories Cards Grid */}
            <div className="pure-cards-grid">
              {results.map((repo, idx) => {
                const langColor = getLanguageColor(repo.language);
                const updatedFormatted = formatDate(repo.updated_at);
                const cardId = `repo-${idx}-${repo.name}`;
                const isCloneCopied = copiedClone === cardId;
                const isLinkCopied = copiedUrl === repo.url;

                return (
                  <article key={idx} className="pure-repo-card glass-panel">
                    {/* Card Top: Rank, Title, Link */}
                    <div className="pure-card-header">
                      <div className="pure-header-left">
                        {repo.owner_avatar ? (
                          <img 
                            src={repo.owner_avatar} 
                            alt={repo.name} 
                            className="pure-owner-avatar"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <span className="pure-rank-badge">#{idx + 1}</span>
                        )}
                        <div className="pure-title-col">
                          <h3 className="pure-repo-name">
                            <a 
                              href={repo.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="pure-repo-link"
                              title="Open on GitHub"
                            >
                              <span>{repo.name}</span>
                              <ExternalLink size={14} className="pure-ext-icon" />
                            </a>
                          </h3>
                        </div>
                      </div>

                      <div className="pure-header-right">
                        <span className="pure-rank-chip">Rank #{idx + 1}</span>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="pure-repo-description">
                      {repo.description || 'No description provided by repository owner.'}
                    </p>

                    {/* Topics Pills */}
                    {repo.topics && repo.topics.length > 0 && (
                      <div className="pure-topics-list">
                        {repo.topics.slice(0, 6).map((topic, tidx) => (
                          <button
                            key={tidx}
                            type="button"
                            className="pure-topic-badge"
                            onClick={() => {
                              setQuery(topic);
                              handleSearch(topic, null);
                            }}
                            title={`Search for #${topic}`}
                          >
                            #{topic}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Metadata Badges Row */}
                    <div className="pure-metrics-row">
                      {/* Language */}
                      {repo.language && repo.language !== 'Unknown' && (
                        <span className="pure-metric-badge lang-badge" title="Primary Language">
                          <span 
                            className="lang-dot" 
                            style={{ backgroundColor: langColor }}
                          ></span>
                          <span>{repo.language}</span>
                        </span>
                      )}

                      {/* Stars */}
                      <span className="pure-metric-badge stars-badge" title="Total Stars">
                        <Star size={13} className="badge-star-icon" fill="currentColor" />
                        <span>{formatNumber(repo.stars)}</span>
                      </span>

                      {/* Forks */}
                      <span className="pure-metric-badge forks-badge" title="Total Forks">
                        <GitFork size={13} />
                        <span>{formatNumber(repo.forks)}</span>
                      </span>

                      {/* Open Issues */}
                      {repo.open_issues !== undefined && (
                        <span className="pure-metric-badge issues-badge" title="Open Issues">
                          <CircleDot size={13} />
                          <span>{formatNumber(repo.open_issues)} issues</span>
                        </span>
                      )}

                      {/* License */}
                      {repo.license && (
                        <span className="pure-metric-badge license-badge" title={`License: ${repo.license}`}>
                          <Scale size={13} />
                          <span>{repo.license}</span>
                        </span>
                      )}

                      {/* Updated Date */}
                      {updatedFormatted && (
                        <span className="pure-metric-badge updated-badge" title={`Last Updated: ${updatedFormatted}`}>
                          <Clock size={13} />
                          <span>{updatedFormatted}</span>
                        </span>
                      )}
                    </div>

                    {/* Card Actions Footer */}
                    <div className="pure-card-footer">
                      <a
                        href={repo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="pure-action-btn primary"
                      >
                        <span>View on GitHub</span>
                        <ArrowUpRight size={15} />
                      </a>

                      <button
                        type="button"
                        className={`pure-action-btn secondary ${isCloneCopied ? 'copied' : ''}`}
                        onClick={() => handleCopyClone(repo.clone_url || repo.url, cardId)}
                        title="Copy 'git clone' command to clipboard"
                      >
                        {isCloneCopied ? (
                          <>
                            <Check size={14} className="text-emerald" />
                            <span>Copied Clone!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={14} />
                            <span>git clone</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        className={`pure-action-btn secondary ${isLinkCopied ? 'copied' : ''}`}
                        onClick={() => handleCopyLink(repo.url)}
                        title="Copy repository link"
                      >
                        {isLinkCopied ? (
                          <>
                            <Check size={14} className="text-emerald" />
                            <span>Copied URL!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={14} />
                            <span>Copy Link</span>
                          </>
                        )}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        ) : (
          /* Empty / Initial State */
          <div className="pure-search-empty-state glass-panel animate-fade-in">
            <div className="empty-state-icon-box">
              <Search size={36} className="empty-search-icon" />
            </div>
            <h2>Search Any GitHub Repository</h2>
            <p>
              Type your desired topic, framework, algorithm, or library above to explore repositories directly.
            </p>
            <div className="empty-features-grid">
              <div className="feature-tip-card">
                <Star size={18} className="tip-icon gold" />
                <h4>Smart Ranking</h4>
                <p>Filter by stars, forks, and relevance to find well-maintained codebases.</p>
              </div>
              <div className="feature-tip-card">
                <Code2 size={18} className="tip-icon cyan" />
                <h4>Multi-Language</h4>
                <p>Narrow searches across Python, TypeScript, Rust, Go, C++, and more.</p>
              </div>
              <div className="feature-tip-card">
                <Copy size={18} className="tip-icon emerald" />
                <h4>One-Click Clone</h4>
                <p>Easily copy clone commands and links to integrate into your workflow.</p>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

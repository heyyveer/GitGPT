import React, { useState, useEffect, useRef } from 'react';
import { 
  FolderTree, 
  FileCode2, 
  Search, 
  FileText, 
  Layers, 
  Copy, 
  Check, 
  ExternalLink,
  Code,
  Box,
  Braces,
  Hash,
  ChevronRight
} from 'lucide-react';

export default function CodeExplorer({ 
  activeRepo, 
  initialFilePath = null, 
  initialLineNumber = null 
}) {
  const [fileList, setFileList] = useState([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [highlightedLine, setHighlightedLine] = useState(null);

  const codeContainerRef = useRef(null);

  // Fetch file list on load or activeRepo change
  useEffect(() => {
    if (!activeRepo) return;

    const fetchFiles = async () => {
      setLoadingFiles(true);
      try {
        const res = await fetch('/api/files');
        if (res.ok) {
          const data = await res.json();
          setFileList(data.files || []);
          if (data.files && data.files.length > 0) {
            const defaultFile = initialFilePath && data.files.includes(initialFilePath)
              ? initialFilePath
              : data.files[0];
            setSelectedFile(defaultFile);
          }
        }
      } catch (err) {
        console.error('Error fetching file list:', err);
      } finally {
        setLoadingFiles(false);
      }
    };

    fetchFiles();
  }, [activeRepo]);

  // Load specific file when initialFilePath changes
  useEffect(() => {
    if (initialFilePath && fileList.includes(initialFilePath)) {
      setSelectedFile(initialFilePath);
    }
    if (initialLineNumber) {
      setHighlightedLine(initialLineNumber);
    }
  }, [initialFilePath, initialLineNumber, fileList]);

  // Fetch file content and AST symbols when selectedFile changes
  useEffect(() => {
    if (!selectedFile) return;

    const fetchContent = async () => {
      setLoadingContent(true);
      try {
        const res = await fetch(`/api/file?path=${encodeURIComponent(selectedFile)}`);
        if (res.ok) {
          const data = await res.json();
          setFileData(data);
        }
      } catch (err) {
        console.error('Error fetching file content:', err);
      } finally {
        setLoadingContent(false);
      }
    };

    fetchContent();
  }, [selectedFile]);

  // Scroll to highlighted line
  useEffect(() => {
    if (highlightedLine && codeContainerRef.current) {
      const lineEl = document.getElementById(`code-line-${highlightedLine}`);
      if (lineEl) {
        lineEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [highlightedLine, fileData]);

  const handleCopyCode = () => {
    if (!fileData?.content) return;
    navigator.clipboard.writeText(fileData.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const jumpToLine = (startLine) => {
    setHighlightedLine(startLine);
    const lineEl = document.getElementById(`code-line-${startLine}`);
    if (lineEl) {
      lineEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const filteredFiles = fileList.filter(f => 
    f.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.py')) return <FileCode2 size={15} className="text-cyan" />;
    if (fileName.endsWith('.md')) return <FileText size={15} className="text-amber" />;
    if (fileName.endsWith('.json') || fileName.endsWith('.toml') || fileName.endsWith('.yaml') || fileName.endsWith('.yml')) 
      return <Braces size={15} className="text-purple" />;
    if (fileName.endsWith('.js') || fileName.endsWith('.ts') || fileName.endsWith('.jsx') || fileName.endsWith('.tsx')) 
      return <Code size={15} className="text-emerald" />;
    return <FileText size={15} className="text-muted" />;
  };

  if (!activeRepo) {
    return (
      <div className="explorer-empty glass-panel animate-fade-in">
        <FolderTree size={48} className="empty-bot-icon" />
        <h2>Codebase Explorer</h2>
        <p>Ingest a repository to browse files and inspect AST symbols.</p>
      </div>
    );
  }

  return (
    <div className="code-explorer-layout animate-fade-in">
      {/* Left Sidebar: File Tree & Search */}
      <div className="explorer-sidebar glass-panel">
        <div className="sidebar-header">
          <div className="sidebar-title-row">
            <FolderTree size={16} className="brand-color" />
            <h3>Files ({filteredFiles.length})</h3>
          </div>
          <div className="file-search-box">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Filter files..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
          </div>
        </div>

        <div className="files-list-viewport">
          {loadingFiles ? (
            <div className="files-loading">Loading repository files...</div>
          ) : filteredFiles.length === 0 ? (
            <div className="no-files-found">No matching files found.</div>
          ) : (
            filteredFiles.map((file, idx) => {
              const isSelected = selectedFile === file;
              return (
                <div
                  key={idx}
                  className={`file-tree-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedFile(file);
                    setHighlightedLine(null);
                  }}
                  title={file}
                >
                  {getFileIcon(file)}
                  <span className="file-item-name">{file}</span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Center: Main Code Viewer */}
      <div className="explorer-code-pane glass-panel">
        {/* Code Pane Header */}
        <div className="code-pane-header">
          <div className="breadcrumb-row">
            <span className="repo-breadcrumb">{activeRepo.name}</span>
            <ChevronRight size={13} className="text-muted" />
            <span className="file-breadcrumb">{selectedFile || 'Select a file'}</span>
          </div>

          <div className="code-pane-actions">
            {fileData && (
              <>
                <span className="badge badge-primary">
                  {fileData.line_count} lines
                </span>
                <span className="badge badge-cyan">
                  {(fileData.size_bytes / 1024).toFixed(1)} KB
                </span>
              </>
            )}
            <button className="btn-ghost copy-code-btn" onClick={handleCopyCode} title="Copy code">
              {copied ? <Check size={14} className="text-emerald" /> : <Copy size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        </div>

        {/* Code Content Container with Line Numbers */}
        <div className="code-viewer-viewport" ref={codeContainerRef}>
          {loadingContent ? (
            <div className="code-loading">Reading file content...</div>
          ) : fileData ? (
            <div className="code-editor-layout">
              <pre className="code-pre">
                <code>
                  {fileData.content.split('\n').map((line, idx) => {
                    const lineNum = idx + 1;
                    const isTarget = highlightedLine === lineNum;
                    return (
                      <div 
                        key={idx} 
                        id={`code-line-${lineNum}`}
                        className={`code-line-row ${isTarget ? 'highlighted-line' : ''}`}
                      >
                        <span className="line-number-cell">{lineNum}</span>
                        <span className="line-content-cell">{line || ' '}</span>
                      </div>
                    );
                  })}
                </code>
              </pre>
            </div>
          ) : (
            <div className="no-file-selected">Select a file from the sidebar to inspect.</div>
          )}
        </div>
      </div>

      {/* Right: AST Symbol Navigator */}
      <div className="explorer-ast-pane glass-panel">
        <div className="ast-header">
          <div className="ast-title-row">
            <Layers size={16} className="text-purple" />
            <h3>AST Symbols</h3>
          </div>
          <span className="badge badge-purple">
            {fileData?.ast_symbols?.length || 0} Symbols
          </span>
        </div>

        <div className="ast-symbols-viewport">
          {fileData?.ast_symbols && fileData.ast_symbols.length > 0 ? (
            fileData.ast_symbols.map((sym, sidx) => {
              const isClass = sym.symbol_type === 'class';
              return (
                <div 
                  key={sidx} 
                  className={`ast-symbol-item ${isClass ? 'ast-class' : 'ast-fn'}`}
                  onClick={() => jumpToLine(sym.start_line)}
                  title={`Jump to line ${sym.start_line}`}
                >
                  <div className="symbol-info">
                    <div className="symbol-type-badge">
                      {isClass ? <Box size={12} /> : <Code size={12} />}
                      <span>{sym.symbol_type}</span>
                    </div>
                    <span className="symbol-name">{sym.symbol}</span>
                  </div>
                  <span className="symbol-lines">
                    L{sym.start_line}-{sym.end_line}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="no-ast-data">
              {selectedFile?.endsWith('.py') 
                ? 'No top-level functions or classes detected in this file.' 
                : 'AST Symbol analysis is available for Python source files.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

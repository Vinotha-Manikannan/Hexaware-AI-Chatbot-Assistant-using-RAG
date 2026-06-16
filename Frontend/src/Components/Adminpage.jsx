import React, { useState, useRef, useEffect } from 'react';
import './Styles/Adminpage.css';
import './Styles/Login.css';
import './Styles/Tickets_addon.css';
import { AiFillDelete } from "react-icons/ai";
import { MdPreview } from "react-icons/md";
import { FaFileAlt, FaTicketAlt } from "react-icons/fa";
import { IoMdRefresh } from "react-icons/io";

// ==========================================
// Login Component
// ==========================================

const Login = ({ onLogin, expiredSession }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('adminToken', data.token);
        onLogin(true);
      } else {
        setError(data.detail || 'Invalid credentials');
      }
    } catch (error) {
      setError('Login failed. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Admin Login</h2>
        <p className="login-subtitle">RAG Agent Management</p>

        {/* FIX: Show banner when session expired */}
        {expiredSession && (
          <p style={{
            background: '#fef3c7',
            color: '#92400e',
            border: '1px solid #fcd34d',
            borderRadius: 8,
            padding: '8px 12px',
            fontSize: 13,
            marginBottom: 12,
            textAlign: 'center'
          }}>
            Your session expired. Please log in again.
          </p>
        )}

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            required
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ==========================================
// Ticket Status Badge
// ==========================================

const StatusBadge = ({ status }) => {
  const colors = {
    'Open':        { bg: '#fee2e2', color: '#dc2626', border: '#fca5a5' },
    'In Progress': { bg: '#fef3c7', color: '#d97706', border: '#fcd34d' },
    'Resolved':    { bg: '#d1fae5', color: '#059669', border: '#6ee7b7' },
  };
  const style = colors[status] || colors['Open'];

  return (
    <span style={{
      padding: '3px 10px',
      borderRadius: '999px',
      fontSize: '12px',
      fontWeight: 600,
      background: style.bg,
      color: style.color,
      border: `1px solid ${style.border}`,
      whiteSpace: 'nowrap',
    }}>
      {status}
    </span>
  );
};

// ==========================================
// Ticket Priority Badge
// ==========================================

const PriorityBadge = ({ priority }) => {
  const colors = {
    'Low':      { bg: '#f0fdf4', color: '#16a34a', border: '#86efac' },
    'Medium':   { bg: '#fefce8', color: '#ca8a04', border: '#fde047' },
    'High':     { bg: '#fff7ed', color: '#ea580c', border: '#fdba74' },
    'Critical': { bg: '#fef2f2', color: '#dc2626', border: '#fca5a5' },
  };
  const style = colors[priority] || colors['Low'];

  return (
    <span style={{
      padding: '3px 10px',
      borderRadius: '999px',
      fontSize: '12px',
      fontWeight: 600,
      background: style.bg,
      color: style.color,
      border: `1px solid ${style.border}`,
      whiteSpace: 'nowrap',
    }}>
      {priority || 'Low'}
    </span>
  );
};

// ==========================================
// Tickets Tab
// ==========================================

const TicketsTab = ({ getAuthHeaders, onTokenExpired }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('All');
  const [expandedTicket, setExpandedTicket] = useState(null);

  // ==========================================
  // FIX: Central fetch wrapper
  // Catches 401 (expired JWT) and redirects
  // to login with "session expired" message
  // ==========================================
  const authFetch = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: { ...getAuthHeaders(), ...(options.headers || {}) }
    });
    if (response.status === 401) {
      onTokenExpired();
      return null;
    }
    return response;
  };

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const response = await authFetch('http://localhost:8000/api/tickets');
      if (response?.ok) {
        const data = await response.json();
        setTickets(data.tickets || []);
      }
    } catch (error) {
      console.error('Failed to fetch tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (ticketId, newStatus) => {
    try {
      const response = await authFetch(`http://localhost:8000/api/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (response?.ok) {
        setTickets(prev =>
          prev.map(t => t.ticket_id === ticketId ? { ...t, status: newStatus } : t)
        );
      }
    } catch (error) {
      console.error('Failed to update ticket:', error);
    }
  };

  const updatePriority = async (ticketId, newPriority, currentStatus) => {
    try {
      const response = await authFetch(`http://localhost:8000/api/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: currentStatus, priority: newPriority })
      });
      if (response?.ok) {
        setTickets(prev =>
          prev.map(t => t.ticket_id === ticketId ? { ...t, priority: newPriority } : t)
        );
      }
    } catch (error) {
      console.error('Failed to update priority:', error);
    }
  };

  const deleteTicket = async (ticketId) => {
    if (!window.confirm(`Delete ticket ${ticketId}?`)) return;
    try {
      const response = await authFetch(`http://localhost:8000/api/tickets/${ticketId}`, {
        method: 'DELETE'
      });
      if (response?.ok) {
        setTickets(prev => prev.filter(t => t.ticket_id !== ticketId));
        if (expandedTicket === ticketId) setExpandedTicket(null);
      }
    } catch (error) {
      console.error('Failed to delete ticket:', error);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const filtered = filter === 'All' ? tickets : tickets.filter(t => t.status === filter);

  const counts = {
    All: tickets.length,
    Open: tickets.filter(t => t.status === 'Open').length,
    'In Progress': tickets.filter(t => t.status === 'In Progress').length,
    Resolved: tickets.filter(t => t.status === 'Resolved').length,
  };

  return (
    <div className="tickets-container">

      {/* Header */}
      <div className="tickets-header">
        <div className="tickets-title-row">
          <h2>IT Support Tickets</h2>
          <button className="refresh-btn" onClick={fetchTickets} title="Refresh">
            <IoMdRefresh size={24} />
          </button>
        </div>

        {/* Filter tabs */}
        <div className="ticket-filters">
          {['All', 'Open', 'In Progress', 'Resolved'].map(f => (
            <button
              key={f}
              className={`filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
              <span className="filter-count">{counts[f]}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="tickets-loading">
          <div className="spinner"></div>
          <p>Loading tickets...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="no-tickets">
          <FaTicketAlt size={48} style={{ opacity: 0.3, marginBottom: 12 }} />
          <p>No {filter !== 'All' ? filter.toLowerCase() : ''} tickets found</p>
        </div>
      ) : (
        <div className="tickets-table-wrapper">
          <table className="tickets-table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th style={{ minWidth: 180 }}>Issue</th>
                <th>Name</th>
                <th>Emp ID</th>
                <th>Department</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th style={{ whiteSpace: 'nowrap' }}>Created At</th>
                <th style={{ minWidth: 220 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(ticket => (
                <React.Fragment key={ticket.ticket_id}>

                  {/* Main row — click to expand */}
                  <tr
                    className="ticket-row"
                    onClick={() =>
                      setExpandedTicket(
                        expandedTicket === ticket.ticket_id ? null : ticket.ticket_id
                      )
                    }
                    style={{ cursor: 'pointer' }}
                  >
                    <td><code className="ticket-id">{ticket.ticket_id}</code></td>
                    <td>
                      <div className="ticket-issue-text" title={ticket.issue}>
                        {ticket.issue}
                      </div>
                    </td>
                    <td>{ticket.employee_name || '—'}</td>
                    <td><code style={{ fontSize: 12 }}>{ticket.employee_id || '—'}</code></td>
                    <td>{ticket.department || '—'}</td>
                    <td>
                      <span className="ticket-category">{ticket.category}</span>
                    </td>
                    <td>
                      <PriorityBadge priority={ticket.priority} />
                    </td>
                    <td>
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="ticket-date">{ticket.created_at}</td>

                    {/* Actions — stop row click from firing */}
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="ticket-actions">

                        {/* Priority dropdown */}
                        <div className="action-group">
                          <label className="action-label">Priority</label>
                          <select
                            className="status-select"
                            value={ticket.priority || 'Low'}
                            onChange={(e) => updatePriority(ticket.ticket_id, e.target.value, ticket.status)}
                          >
                            <option>Low</option>
                            <option>Medium</option>
                            <option>High</option>
                            <option>Critical</option>
                          </select>
                        </div>

                        {/* Status dropdown */}
                        <div className="action-group">
                          <label className="action-label">Status</label>
                          <select
                            className="status-select"
                            value={ticket.status}
                            onChange={(e) => updateStatus(ticket.ticket_id, e.target.value)}
                          >
                            <option>Open</option>
                            <option>In Progress</option>
                            <option>Resolved</option>
                          </select>
                        </div>

                        {/* Delete */}
                        <button
                          className="btn-icon delete"
                          title="Delete ticket"
                          onClick={() => deleteTicket(ticket.ticket_id)}
                          style={{ alignSelf: 'flex-end', marginBottom: 2 }}
                        >
                          <AiFillDelete />
                        </button>

                      </div>
                    </td>
                  </tr>

                  {/* Expanded full issue row */}
                  {expandedTicket === ticket.ticket_id && (
                    <tr className="ticket-expanded-row">
                      <td colSpan={10}>
                        <div className="ticket-expanded-content">
                          <strong>Full Issue</strong>
                          <p>{ticket.issue}</p>
                        </div>
                      </td>
                    </tr>
                  )}

                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// ==========================================
// Main Admin Panel
// ==========================================

const AdminPanel = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [expiredSession, setExpiredSession] = useState(false); // FIX: track expiry
  const [activeTab, setActiveTab] = useState('files');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [domains, setDomains] = useState([]);
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [viewModal, setViewModal] = useState({ show: false, content: '', filename: '' });
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
  });

  // ==========================================
  // FIX: Called when any request gets 401
  // Shows "session expired" banner on login page
  // ==========================================
  const handleTokenExpired = () => {
    localStorage.removeItem('adminToken');
    setIsAuthenticated(false);
    setExpiredSession(true);
    setSelectedDomain('');
    setFiles([]);
    setDomains([]);
  };

  // ==========================================
  // FIX: Central fetch wrapper for files tab
  // ==========================================
  const authFetch = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: { ...getAuthHeaders(), ...(options.headers || {}) }
    });
    if (response.status === 401) {
      handleTokenExpired();
      return null;
    }
    return response;
  };

  const fetchDomains = async () => {
    try {
      const response = await authFetch('http://localhost:8000/api/domains');
      if (response?.ok) {
        const data = await response.json();
        setDomains(data.domains || []);
      }
    } catch (error) {
      console.error('Failed to fetch domains:', error);
    }
  };

  const fetchDomainFiles = async (domain) => {
    try {
      const response = await authFetch(`http://localhost:8000/api/files/${domain}`);
      if (response?.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      }
    } catch (error) {
      console.error('Failed to fetch files:', error);
    }
  };

  const handleFileSelect = (e) => {
    if (!selectedDomain) { alert('Please select a domain first!'); return; }
    addFiles(Array.from(e.target.files));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (!selectedDomain) { alert('Please select a domain first!'); return; }
    addFiles(Array.from(e.dataTransfer.files));
  };

  const addFiles = async (newFiles) => {
    setUploading(true);
    for (const file of newFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('domain', selectedDomain);
      try {
        const response = await authFetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData
        });
        if (response && !response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }
      } catch (error) {
        alert(`Failed to upload ${file.name}: ${error.message}`);
      }
    }
    setUploading(false);
    await fetchDomainFiles(selectedDomain);
  };

  const deleteFile = async (filename) => {
    if (!window.confirm(`Delete "${filename}"?`)) return;
    try {
      const response = await authFetch(
        `http://localhost:8000/api/files/${selectedDomain}/${filename}`,
        { method: 'DELETE' }
      );
      if (response?.ok) {
        setFiles(files.filter(f => f.name !== filename));
      } else if (response) {
        const error = await response.json();
        throw new Error(error.detail || 'Delete failed');
      }
    } catch (error) {
      alert('Failed to delete file: ' + error.message);
    }
  };

  const viewFile = async (filename) => {
    try {
      const response = await authFetch(
        `http://localhost:8000/api/files/${selectedDomain}/${filename}/content`
      );
      if (response?.ok) {
        const data = await response.json();
        setViewModal({ show: true, content: data.content, filename });
      } else if (response) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to load file');
      }
    } catch (error) {
      alert('Failed to load file: ' + error.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    setIsAuthenticated(false);
    setExpiredSession(false);
    setSelectedDomain('');
    setFiles([]);
    setDomains([]);
  };

  // ==========================================
  // Clear token on page refresh / tab close
  // ==========================================

  useEffect(() => {
    const clearAuth = () => {
      localStorage.removeItem('adminToken');
    };
    window.addEventListener('beforeunload', clearAuth);
    return () => {
      window.removeEventListener('beforeunload', clearAuth);
    };
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('adminToken');
    if (token) {
      setIsAuthenticated(true);
      fetchDomains();
    }
  }, []);

  useEffect(() => {
    if (selectedDomain && isAuthenticated) {
      fetchDomainFiles(selectedDomain);
    }
  }, [selectedDomain]);

  if (!isAuthenticated) {
    return <Login onLogin={setIsAuthenticated} expiredSession={expiredSession} />;
  }

  return (
    <div className="admin-container">

      {/* Header */}
      <div className="admin-header">
        <div>
          <h1>Source Management (Admin)</h1>
          <p className="admin-subtitle">Manage domain-specific knowledge bases</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1">
            </path>
          </svg>
          Logout
        </button>
      </div>

      {/* Admin Tabs */}
      <div className="admin-tabs">
        <button
          className={`admin-tab-btn ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          <FaFileAlt style={{ marginRight: 8 }} />
          Knowledge Base
        </button>
        <button
          className={`admin-tab-btn ${activeTab === 'tickets' ? 'active' : ''}`}
          onClick={() => setActiveTab('tickets')}
        >
          <FaTicketAlt style={{ marginRight: 8 }} />
          IT Tickets
        </button>
      </div>

      {/* ---- FILES TAB ---- */}
      {activeTab === 'files' && (
        <>
          <div className="domain-selector">
            <div className="domain-select-wrapper">
              <label>Select Domain:</label>
              <select
                onClick={fetchDomains}
                value={selectedDomain}
                onChange={(e) => {
                  const domain = e.target.value;
                  setSelectedDomain(domain);
                  if (domain) fetchDomainFiles(domain);
                }}
                className="domain-select"
              >
                <option value="">Choose</option>
                {domains.map(d => (
                  <option key={d.name} value={d.name}>
                    {d.name} ({d.fileCount} files)
                  </option>
                ))}
              </select>
            </div>
            {!selectedDomain && (
              <p className="domain-hint">Please select a domain to manage files</p>
            )}
          </div>

          {selectedDomain && (
            <div className="admin-body">
              <div className="upload-section">
                <div className="upload-card">
                  <div
                    className={`upload-zone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => !uploading && fileInputRef.current?.click()}
                  >
                    {uploading ? (
                      <div className="upload-progress">
                        <div className="spinner"></div>
                        <h3>Uploading & Processing...</h3>
                      </div>
                    ) : (
                      <>
                        <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12">
                          </path>
                        </svg>
                        <h3>Upload to {selectedDomain} Domain</h3>
                        <p>Supports PDF, TXT, DOCX, CSV files</p>
                        <input
                          type="file"
                          ref={fileInputRef}
                          className="file-input"
                          multiple
                          accept=".pdf,.txt,.doc,.docx,.csv"
                          onChange={handleFileSelect}
                          disabled={uploading}
                        />
                        <button
                          className="upload-btn"
                          onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                          disabled={uploading}
                        >
                          Select Files
                        </button>
                      </>
                    )}
                  </div>

                  <div className="file-list">
                    <div className="file-list-header">
                      <h3>{selectedDomain} Files ({files.length})</h3>
                      <button
                        className="refresh-btn"
                        onClick={() => fetchDomainFiles(selectedDomain)}
                        title="Refresh file list"
                      >
                        <IoMdRefresh size={30} />
                      </button>
                    </div>

                    <div className="file-items">
                      {files.length === 0 ? (
                        <div className="no-files"><p>No files uploaded yet</p></div>
                      ) : (
                        files.map((file) => (
                          <div key={file.id} className="file-item">
                            <div className="file-info">
                              <div className="file-icon"><FaFileAlt /></div>
                              <div className="file-details">
                                <div className="file-name">{file.name}</div>
                                <div className="file-meta">{file.size} • {file.uploadTime}</div>
                              </div>
                            </div>
                            <div className="file-actions">
                              <button className="btn-icon view" title="View file" onClick={() => viewFile(file.name)}>
                                <MdPreview />
                              </button>
                              <button className="btn-icon delete" title="Delete file" onClick={() => deleteFile(file.name)}>
                                <AiFillDelete />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* ---- TICKETS TAB ---- */}
      {activeTab === 'tickets' && (
        <TicketsTab getAuthHeaders={getAuthHeaders} onTokenExpired={handleTokenExpired} />
      )}

      {/* File Preview Modal */}
      {viewModal.show && (
        <div className="modal-overlay" onClick={() => setViewModal({ show: false, content: '', filename: '' })}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📄 {viewModal.filename}</h3>
              <button className="modal-close" onClick={() => setViewModal({ show: false, content: '', filename: '' })}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <pre>{viewModal.content}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
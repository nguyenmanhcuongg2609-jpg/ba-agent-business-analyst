import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, FileText, Upload, X, Loader2, Info, ChevronRight, Trash2, Plus, MessageSquare, Filter } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';
const API_KEY = 'rag-secret-key-2024';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'X-API-Key': API_KEY }
});

function App() {
  const [messages, setMessages] = useState([{
    role: 'ai',
    content: 'Xin chào! Tôi là trợ lý AI RAG. Hãy hỏi bất cứ điều gì về tài liệu đã tải lên!'
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [papers, setPapers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [useHyDE, setUseHyDE] = useState(false);
  const [filterFiles, setFilterFiles] = useState([]);
  const [showFilter, setShowFilter] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => { fetchPapers(); fetchSessions(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchPapers = async () => {
    try { const r = await api.get('/api/papers'); setPapers(r.data.papers || []); } catch {}
  };

  const fetchSessions = async () => {
    try { const r = await api.get('/api/sessions'); setSessions(r.data.sessions || []); } catch {}
  };

  const newSession = async () => {
    try {
      const r = await api.post('/api/sessions', { title: 'Phiên mới ' + new Date().toLocaleTimeString('vi-VN') });
      const sid = r.data.session_id;
      setCurrentSessionId(sid);
      setMessages([{ role: 'ai', content: 'Phiên mới đã bắt đầu. Hãy đặt câu hỏi!' }]);
      fetchSessions();
    } catch {}
  };

  const loadSession = async (sessionId) => {
    try {
      const r = await api.get(`/api/sessions/${sessionId}`);
      setCurrentSessionId(sessionId);
      const msgs = r.data.messages.map(m => ({
        role: m.role === 'assistant' ? 'ai' : 'user',
        content: m.content,
        sources: m.sources || []
      }));
      setMessages(msgs.length ? msgs : [{ role: 'ai', content: 'Phiên này chưa có tin nhắn.' }]);
    } catch {}
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/sessions/${sessionId}`);
      if (currentSessionId === sessionId) { setCurrentSessionId(null); setMessages([{ role: 'ai', content: 'Xin chào! Hãy bắt đầu phiên mới.' }]); }
      fetchSessions();
    } catch {}
  };

  const deletePaper = async (filename) => {
    if (!window.confirm(`Xoá "${filename}"?`)) return;
    try {
      await api.delete(`/api/papers/${filename}`);
      setFilterFiles(prev => prev.filter(f => f !== filename));
      fetchPapers();
    } catch (err) { alert(err.response?.data?.detail || 'Lỗi xoá file'); }
  };

  const toggleFilter = (filename) => {
    setFilterFiles(prev => prev.includes(filename) ? prev.filter(f => f !== filename) : [...prev, filename]);
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    const historyForApi = messages.map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content }));

    try {
      setMessages(prev => [...prev, { role: 'ai', content: '', isStreaming: true }]);
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
        body: JSON.stringify({
          query: userMessage,
          history: historyForApi,
          use_hyde: useHyDE,
          session_id: currentSessionId,
          filter_files: filterFiles.length > 0 ? filterFiles : null
        })
      });

      if (!response.ok) throw new Error('Stream failed');
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let aiText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value, { stream: true }).split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const dataStr = line.replace('data: ', '').trim();
          if (!dataStr || dataStr === '[DONE]') continue;
          try {
            const data = JSON.parse(dataStr);
            if (data.type === 'chunk') {
              aiText += data.content;
              setMessages(prev => { const n = [...prev]; n[n.length - 1] = { ...n[n.length - 1], content: aiText }; return n; });
            } else if (data.type === 'metadata') {
              setMessages(prev => { const n = [...prev]; n[n.length - 1] = { ...n[n.length - 1], sources: data.sources, followUps: data.follow_up_questions, isStreaming: false }; return n; });
              if (currentSessionId) fetchSessions();
            } else if (data.type === 'error') {
              setMessages(prev => { const n = [...prev]; n[n.length - 1] = { ...n[n.length - 1], content: '❌ ' + data.content, isStreaming: false }; return n; });
            }
          } catch {}
        }
      }
    } catch (error) {
      // Fallback to non-stream
      try {
        const r = await api.post('/api/chat', {
          query: userMessage, history: historyForApi, use_hyde: useHyDE,
          session_id: currentSessionId, filter_files: filterFiles.length > 0 ? filterFiles : null
        });
        setMessages(prev => { const n = [...prev]; n[n.length - 1] = { role: 'ai', content: r.data.answer, sources: r.data.sources, followUps: r.data.follow_up_questions, isStreaming: false }; return n; });
      } catch {
        setMessages(prev => { const n = [...prev]; n[n.length - 1] = { role: 'ai', content: '❌ Lỗi kết nối server.', isStreaming: false }; return n; });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };

  const handleFollowUpClick = (q) => {
    setInput(q);
    setTimeout(() => document.getElementById('send-btn')?.click(), 100);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="gradient-text" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bot size={24} /> RAG Assistant
          </h1>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={newSession}>
              <Plus size={14} /> Phiên mới
            </button>
            <button className="btn btn-secondary" onClick={() => setShowUploadModal(true)}>
              <Upload size={14} />
            </button>
          </div>
        </div>

        <div className="sidebar-content">
          {/* Sessions */}
          <h3 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Lịch sử ({sessions.length})
          </h3>
          <div style={{ marginBottom: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
            {sessions.length === 0 ? (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '0.5rem' }}>Chưa có phiên nào</p>
            ) : sessions.map(s => (
              <div key={s.id} className={`paper-item ${currentSessionId === s.id ? 'active' : ''}`}
                onClick={() => loadSession(s.id)}
                style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontSize: '0.8rem' }}>
                  <MessageSquare size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />{s.title}
                </span>
                <button onClick={(e) => deleteSession(s.id, e)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0 2px' }}>
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>

          {/* Papers */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Tài liệu ({papers.length})
            </h3>
            <button onClick={() => setShowFilter(!showFilter)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: filterFiles.length > 0 ? 'var(--accent-color)' : 'var(--text-secondary)' }}>
              <Filter size={14} />
            </button>
          </div>
          {showFilter && papers.length > 0 && (
            <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              ✅ Tick để lọc retrieval theo file
            </p>
          )}
          {papers.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '1.5rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <FileText size={28} style={{ opacity: 0.4, margin: '0 auto 0.4rem' }} />
              <p>Chưa có tài liệu</p>
            </div>
          ) : papers.map((p, i) => (
            <div key={i} className="paper-item" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {showFilter && (
                <input type="checkbox" checked={filterFiles.includes(p.filename)}
                  onChange={() => toggleFilter(p.filename)}
                  style={{ accentColor: 'var(--accent-color)', flexShrink: 0 }} />
              )}
              <FileText size={13} style={{ flexShrink: 0 }} />
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.8rem' }} title={p.filename}>
                {p.filename}
              </span>
              <button onClick={() => deletePaper(p.filename)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0 2px', flexShrink: 0 }}>
                <Trash2 size={12} />
              </button>
            </div>
          ))}

          {filterFiles.length > 0 && (
            <div style={{ marginTop: '0.5rem', padding: '0.4rem 0.6rem', background: 'rgba(var(--accent-rgb),0.15)', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--accent-color)' }}>
              🔍 Đang lọc: {filterFiles.length} file
              <button onClick={() => setFilterFiles([])} style={{ marginLeft: '6px', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '0.75rem' }}>✕ Xoá filter</button>
            </div>
          )}
        </div>
      </aside>

      {/* Main Chat */}
      <main className="chat-container">
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              <div className={`message-avatar ${msg.role}`}>
                {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className={`message ${msg.role}`}>
                <div className="message-content prose">
                  {msg.isStreaming && !msg.content ? (
                    <div className="typing-indicator">
                      <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                    </div>
                  ) : <ReactMarkdown>{msg.content}</ReactMarkdown>}
                </div>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources-container">
                    <div className="sources-title"><Info size={14} /> Nguồn tham khảo:</div>
                    <div className="source-badges">
                      {msg.sources.map((src, i) => (
                        <div key={i} className="source-badge" title={`${src.title}\n${src.authors} (${src.year})\nSection: ${src.section}\nScore: ${(src.confidence_score * 100).toFixed(0)}%\n\n${src.content?.substring(0, 200)}...`}>
                          <span>{src.filename || `Nguồn ${i + 1}`}</span>
                          {src.section && src.section !== 'Body' && <span style={{ opacity: 0.7, fontSize: '0.7rem', marginLeft: '4px' }}>[{src.section}]</span>}
                          <span style={{ opacity: 0.6, fontSize: '0.7rem', marginLeft: '4px' }}>{(src.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {msg.followUps && msg.followUps.length > 0 && (
                  <div className="follow-ups">
                    {msg.followUps.map((q, i) => (
                      <button key={i} className="follow-up-pill" onClick={() => handleFollowUpClick(q)}>
                        {q} <ChevronRight size={14} style={{ display: 'inline', verticalAlign: 'middle' }} />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', maxWidth: '800px', margin: '0 auto 0.5rem', alignItems: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {currentSessionId ? `📁 Session đang lưu` : '💭 Không lưu (tạo phiên mới để lưu)'}
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <input type="checkbox" checked={useHyDE} onChange={e => setUseHyDE(e.target.checked)} style={{ accentColor: 'var(--accent-color)' }} />
              Bật HyDE
            </label>
          </div>
          <div className="input-container glass" style={{ borderRadius: '16px' }}>
            <textarea className="chat-input" style={{ background: 'transparent', border: 'none' }}
              value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Hỏi bất cứ điều gì về tài liệu..." disabled={isLoading} rows={1} />
            <button id="send-btn" className="send-button" onClick={handleSend} disabled={!input.trim() || isLoading}>
              {isLoading ? <Loader2 size={18} className="spinner" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </main>

      {showUploadModal && (
        <UploadModal onClose={() => setShowUploadModal(false)} onSuccess={() => { setShowUploadModal(false); fetchPapers(); }} />
      )}
    </div>
  );
}

function UploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) { setError('Vui lòng chọn file PDF'); return; }
    setUploading(true); setError(''); setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const r = await api.post('/api/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(r.data);
      setTimeout(onSuccess, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi upload');
    } finally { setUploading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}><X size={20} /></button>
        <h2 style={{ marginBottom: '1rem' }}>Tải lên tài liệu mới</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Metadata (tên tác giả, năm, tiêu đề) sẽ được tự động trích xuất từ PDF.
        </p>
        <label className="upload-zone" style={{ display: 'block' }}>
          <input type="file" accept=".pdf" style={{ display: 'none' }} onChange={e => { if (e.target.files?.[0]) { setFile(e.target.files[0]); setError(''); } }} />
          <Upload size={40} className="upload-icon" style={{ margin: '0 auto 1rem' }} />
          {file ? <p style={{ fontWeight: 500, color: 'var(--success)' }}>{file.name}</p> : <p>Click hoặc kéo thả file PDF vào đây</p>}
        </label>
        {error && <p style={{ color: 'var(--error)', fontSize: '0.9rem', margin: '0.5rem 0' }}>{error}</p>}
        {result && (
          <div style={{ background: 'rgba(0,200,100,0.1)', borderRadius: '8px', padding: '0.8rem', margin: '0.5rem 0', fontSize: '0.85rem' }}>
            ✅ {result.message}<br />
            📄 Title: {result.metadata?.title}<br />
            👤 Authors: {result.metadata?.authors}<br />
            📅 Year: {result.metadata?.year}
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
          <button className="btn btn-secondary" onClick={onClose} disabled={uploading}>Hủy</button>
          <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? <><Loader2 size={16} className="spinner" /> Đang xử lý...</> : 'Tải lên & Lưu'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;

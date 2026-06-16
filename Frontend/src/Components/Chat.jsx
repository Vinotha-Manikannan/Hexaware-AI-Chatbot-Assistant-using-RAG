import React, { useState, useRef, useEffect } from 'react';
import './Styles/Chat.css';
import ReactMarkdown from 'react-markdown';

const STORAGE_KEY = 'hexaware_chat_history';

const ChatPage = () => {

  const [sessionId] = useState(() => {
    // Always generate a NEW session ID on page load/refresh
    // This ensures a fresh chat starts every time — no stale
    // pending ticket flows carried over from previous sessions
    const newId = 'session-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    sessionStorage.setItem('chat_session_id', newId);
    return newId;
  });

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // ==========================================
  // Clear chat on page refresh (not on navigation)
  // ==========================================

  useEffect(() => {
    const navEntry = performance.getEntriesByType('navigation')[0];
    if (navEntry?.type === 'reload') {
      localStorage.removeItem(STORAGE_KEY);
      setMessages([]);
    }
  }, []);

  // ==========================================
  // Save messages to localStorage on every change
  // ==========================================

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // storage quota exceeded — fail silently
    }
  }, [messages]);

  // ==========================================
  // Auto scroll
  // ==========================================

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // ==========================================
  // Input handler
  // ==========================================

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  // ==========================================
  // Send message
  // ==========================================

  const sendMessage = async () => {
    // Capture text before clearing — avoids stale closure bug
    const text = inputValue.trim();
    if (!text) return;

    const userMessage = {
      id: Date.now(),
      text,
      type: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          // FIX: Do NOT send chat_history from frontend.
          // Backend manages conversation history internally
          // via chat_sessions. Sending history here caused
          // domain detection to be polluted by previous answers
          // (e.g. salary answer containing "IT Help Desk" made
          // the next question route to IT instead of Finance).
          chat_history: []
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        type: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error('Chat failed:', error);

      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        type: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, errorMessage]);

    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ==========================================
  // Render
  // ==========================================

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AI Assistant</h1>
        <p>Ask me anything about your knowledge base</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <svg className="empty-state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z">
              </path>
            </svg>
            <h3>Hello, how was your day?</h3>
            <p></p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? 'U' : 'AI'}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <div className="message-text">
                    {message.type === 'bot' ? (
                      <ReactMarkdown>{message.text}</ReactMarkdown>
                    ) : (
                      message.text
                    )}
                  </div>
                  <div className="message-time">{message.time}</div>
                </div>
              </div>
            </div>
          ))
        )}

        {isTyping && (
          <div className="message bot">
            <div className="message-avatar">AI</div>
            <div className="message-content">
              <div className="message-bubble">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="Ask a question..."
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            rows="1"
          />
          <button className="send-btn" onClick={sendMessage} disabled={!inputValue.trim()}>
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8">
              </path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
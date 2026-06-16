import React, { useState } from 'react';
import AdminPanel from './Components/Adminpage';
import ChatPage from './Components/Chat';
import './App.css';
import { IoIosLock } from "react-icons/io";

function App() {
  const [currentPage, setCurrentPage] = useState('admin');

  return (
    <div className="app-container">

      {/* Navigation Sidebar */}
      <div className="nav-sidebar">
        <div className="logo">
          <div className="logo-icon"><img src="/Logo.png" alt="" /></div>
          <span>Agent</span>
        </div>

        <div className="nav-tabs">
          <button
            className={`nav-tab ${currentPage === 'admin' ? 'active' : ''}`}
            onClick={() => setCurrentPage('admin')}
          >
            <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
              </path>
            </svg>
            Link(Source)<IoIosLock size={20} />
          </button>

          <button
            className={`nav-tab ${currentPage === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentPage('chat')}
          >
            <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z">
              </path>
            </svg>
            Assistant
          </button>
        </div>
      </div>

      {/* Main Content — both components stay mounted, only visibility changes */}
      <div className="main-content">
        <div style={{ display: currentPage === 'admin' ? 'block' : 'none' }}>
          <AdminPanel />
        </div>
        <div style={{ display: currentPage === 'chat' ? 'block' : 'none' }}>
          <ChatPage />
        </div>
      </div>

    </div>
  );
}

export default App;
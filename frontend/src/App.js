import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import SearchForm from './components/SearchForm';
import ResultsDisplay from './components/ResultsDisplay';

function App() {
  const [mode, setMode] = useState('chat'); // 'chat' or 'search'
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🌦️ Weather-Wise Flight Booking</h1>
          <p>Make smarter flight decisions with weather intelligence</p>
        </div>
      </header>

      <div className="mode-toggle">
        <button 
          className={mode === 'chat' ? 'active' : ''} 
          onClick={() => setMode('chat')}
        >
          💬 Chat Mode
        </button>
        <button 
          className={mode === 'search' ? 'active' : ''} 
          onClick={() => setMode('search')}
        >
          🔍 Search Mode
        </button>
      </div>

      <main className="App-main">
        {mode === 'chat' ? (
          <ChatInterface />
        ) : (
          <>
            <SearchForm 
              setResults={setResults} 
              setLoading={setLoading} 
            />
            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                <p>Analyzing weather and fare data...</p>
              </div>
            )}
            {results && <ResultsDisplay results={results} />}
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by Amazon Nova</p>
        <p className="footer-note">Built with ❤️ for smarter travel decisions</p>
      </footer>
    </div>
  );
}

export default App;

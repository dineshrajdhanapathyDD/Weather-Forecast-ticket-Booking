import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ChatInterface.css';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I\'m your Weather-Wise Flight Booking assistant. Tell me where you want to fly and when, and I\'ll help you make the best booking decision based on weather and fare trends. 🌦️✈️'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // Replace with your actual API endpoint
      const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'YOUR_API_ENDPOINT_HERE';
      
      const response = await axios.post(`${API_ENDPOINT}/chat`, {
        message: userMessage
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again or check if the API endpoint is configured correctly.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {typeof msg.content === 'string' ? (
                <pre>{msg.content}</pre>
              ) : (
                <pre>{JSON.stringify(msg.content, null, 2)}</pre>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me about your flight... (e.g., 'I want to fly to Los Angeles from New York in mid-August')"
          rows="3"
          disabled={loading}
        />
        <button 
          className="send-button" 
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? '⏳' : '✈️'} Send
        </button>
      </div>

      <div className="chat-examples">
        <p>💡 Try asking:</p>
        <button onClick={() => setInput("I want to fly to Los Angeles from New York between August 15-22")}>
          "I want to fly to Los Angeles from New York between August 15-22"
        </button>
        <button onClick={() => setInput("Should I book a flight to Miami from Chicago in early September?")}>
          "Should I book a flight to Miami from Chicago in early September?"
        </button>
        <button onClick={() => setInput("I want to fly from Chennai to Delhi on April 10th")}>
          "I want to fly from Chennai to Delhi on April 10th"
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RefreshCw } from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [sessionToken, setSessionToken] = useState(null);
  const [apiToken, setApiToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom of messages area
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setError(null);
    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Append user message immediately
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage }
    ]);

    // Append temporary assistant skeleton
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '' }
    ]);

    const gatewayUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${gatewayUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer ' + apiToken,
          ...(sessionToken ? { 'X-Session-Token': sessionToken } : {}),
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';
      let currentEvent = '';
      let currentAgents = [];
      let pending = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        pending += decoder.decode(value, { stream: true });
        const lines = pending.split('\n');
        pending = lines.pop();

        for (const line of lines) {
          // Remove carriage return characters at the end of the line if any
          const cleanLine = line.endsWith('\r') ? line.slice(0, -1) : line;
          
          if (cleanLine.startsWith('event:')) {
            currentEvent = cleanLine.slice(6).trim();
          } else if (cleanLine.startsWith('data:')) {
            // Remove exactly one space after "data:" if present
            const dataVal = cleanLine.startsWith('data: ') ? cleanLine.slice(6) : cleanLine.slice(5);
            
            if (currentEvent === 'session') {
              const session = JSON.parse(dataVal);
              setSessionId(session.id);
              setSessionToken(session.token);
            } else if (currentEvent === 'agents') {
              try {
                currentAgents = JSON.parse(dataVal);
              } catch (e) {
                currentAgents = [];
              }
            } else if (currentEvent === 'message') {
              let textVal = '';
              try {
                const payload = JSON.parse(dataVal);
                textVal = payload.text;
              } catch (e) {
                // Fallback to raw dataVal if not valid JSON
                textVal = dataVal;
              }
              assistantText += textVal;
              
              // Update last message contents dynamically
              setMessages((prev) => {
                const updated = [...prev];
                if (updated.length > 0) {
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: assistantText,
                    agents: currentAgents
                  };
                }
                return updated;
              });
            } else if (currentEvent === 'error') {
              throw new Error(dataVal.trim());
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to communicate with Gateway API.');
      // Remove empty draft bubble
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (sessionId) {
      const url = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
      try {
        const response = await fetch(url + '/api/sessions/' + sessionId, { method: 'DELETE', headers: { Authorization: 'Bearer ' + apiToken, 'X-Session-Token': sessionToken } });
        if (!response.ok) throw new Error('Could not delete history. Please retry.');
      } catch (err) { setError(err.message); return; }
    }
    setSessionId(null);
    setSessionToken(null);
    setMessages([]);
    setError(null);
    setInput('');
  };

  return (
    <div className="chat-container">
      {/* Header section with branding and status */}
      <div className="chat-header">
        <div>
          <h1>Google ADK A2A Demo</h1>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {sessionId && (
            <button 
              disabled={isLoading}
              onClick={handleReset} 
              className="send-btn" 
              style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
              title="Reset session history"
            >
              <RefreshCw size={14} /> Reset
            </button>
          )}
          <div className="status-badge">
            <span className="status-dot"></span>
            A2A Network Online
          </div>
        </div>
      </div>

      <label style={{ padding: '12px' }}>Access token
        <input type="password" autoComplete="off" value={apiToken} onChange={(e) => setApiToken(e.target.value)} disabled={isLoading || !!sessionId} placeholder="Token supplied by your administrator" />
      </label>
      <p style={{ padding: '0 12px', fontSize: '0.8rem' }}>Messages may be sent to Google Gemini. Do not enter personal or confidential data. History expires after one hour or can be deleted with Reset. AI answers may be inaccurate.</p>
      {/* Messages area with dynamic bubble allocation */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', marginTop: '20%' }}>
            <Bot size={48} style={{ margin: '0 auto 12px', display: 'block', strokeWidth: 1.5, color: '#818cf8' }} />
            <p>Welcome! Type a query to see the multi-agent system coordinate and answer.</p>
            <p style={{ fontSize: '0.8rem' }}>Demo triggers: <b>"summarize"</b> calls Summary Agent, other requests trigger Knowledge Agent.</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`message-bubble ${msg.role}`}
            style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}
          >
            <div style={{ marginTop: '2px' }}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} style={{ color: '#c084fc' }} />}
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
              {msg.role === 'assistant' && msg.agents && msg.agents.length > 0 && (
                <div className="agent-participants">
                  <span className="participant-label">Processed by A2A:</span>
                  {msg.agents.map((agentName, i) => (
                    <span key={i} className="agent-badge">{agentName}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && messages[messages.length - 1]?.content === '' && (
          <div className="typing-indicator">
            <span className="typing-dot"></span>
            <span className="typing-dot"></span>
            <span className="typing-dot"></span>
            <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', marginLeft: '6px' }}>
              Coordinating A2A Agents...
            </span>
          </div>
        )}

        {error && (
          <div className="message-bubble assistant" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
            <p style={{ margin: 0 }}><b>Error:</b> {error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer message inputs */}
      <form onSubmit={handleSend} className="input-area">
        <input
          maxLength={8000}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the project architecture..."
          className="chat-input"
          disabled={isLoading}
        />
        <button type="submit" className="send-btn" disabled={isLoading || !input.trim() || !apiToken}>
          <Send size={16} /> Send
        </button>
      </form>
    </div>
  );
}

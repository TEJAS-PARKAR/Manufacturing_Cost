import { useRef, useEffect } from 'react';

export default function ChatHistory({ history, currentUserRole }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  if (!history || history.length === 0) {
    return <div className="chat-empty">No messages yet. Start the conversation below.</div>;
  }

  return (
    <div className="chat-container">
      {history.map((item, idx) => {
        const role = item.role || 'system';
        const message = item.message || '';
        const timestamp = item.timestamp || '';

        let isMe = false;
        let isSystem = false;
        let roleLabel = '';

        if (role === 'system') {
          isSystem = true;
          roleLabel = 'System';
        } else if (currentUserRole === 'supplier') {
          isMe = (role === 'supplier');
          roleLabel = isMe ? 'You (Supplier)' : 'Tata Motors AI';
        } else if (currentUserRole === 'tata') {
          isMe = (role === 'assistant' || role === 'tata');
          roleLabel = isMe ? 'You (Tata Motors)' : 'Supplier';
        } else {
          // Fallback if currentUserRole is missing
          isSystem = true;
        }

        if (isSystem) {
          return (
            <div key={idx} className="chat-message-row system">
              <div className="chat-bubble chat-system">
                <div className="chat-msg">{message}</div>
                {timestamp && <div className="chat-ts">{timestamp}</div>}
              </div>
            </div>
          );
        }

        return (
          <div key={idx} className={`chat-message-row ${isMe ? 'me' : 'other'}`}>
            <div className={`chat-bubble ${isMe ? 'chat-me' : 'chat-other'}`}>
              <div className="chat-role">{roleLabel}</div>
              <div className="chat-msg">{message}</div>
              {timestamp && <div className="chat-ts">{timestamp}</div>}
            </div>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}

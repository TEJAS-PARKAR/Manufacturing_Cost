import { useRef, useEffect } from 'react';

export default function ChatHistory({ history }) {
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

        let cssClass, roleLabel;
        if (role === 'supplier') {
          cssClass = 'chat-supplier';
          roleLabel = 'Supplier';
        } else if (role === 'assistant') {
          cssClass = 'chat-assistant';
          roleLabel = 'AI Buyer Agent';
        } else if (role === 'tata') {
          cssClass = 'chat-assistant';
          roleLabel = 'Tata Motors';
        } else {
          cssClass = 'chat-system';
          roleLabel = 'System';
        }

        return (
          <div key={idx} className={cssClass}>
            <div className="chat-role">{roleLabel}</div>
            <div className="chat-msg">{message}</div>
            {timestamp && <div className="chat-ts">{timestamp}</div>}
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}

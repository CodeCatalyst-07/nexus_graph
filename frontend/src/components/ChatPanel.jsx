import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ArrowRight, Zap, Info } from 'lucide-react';

export default function ChatPanel({
  messages,
  onSendMessage,
  isProcessing,
  showBaseline,
  sessionBreakActive
}) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sessionBreakActive]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;
    onSendMessage(inputText);
    setInputText('');
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800">
      {/* Panel Sub-header */}
      <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          <span className="text-xs font-semibold text-slate-300">Live Customer Session Stream</span>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">
          Persona: Alice Chen
        </span>
      </div>

      {/* Baseline Comparison Card (When Toggled) */}
      {showBaseline && (
        <div className="bg-amber-950/30 border-b border-amber-500/30 px-4 py-2 text-xs flex items-start gap-2.5">
          <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300 block">Baseline Amnesiac Bot Contrast:</span>
            <span className="text-slate-400 text-[11px]">
              A standard chatbot without Neo4j Agent Memory replies to <i>"It's still not working"</i> with:
              <span className="text-amber-200/90 font-mono block mt-1">
                "I'm sorry to hear that. Could you please provide your account email, product name, and describe your issue again?"
              </span>
            </span>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {messages.length === 0 && !sessionBreakActive && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-3">
              <Bot className="w-6 h-6 text-indigo-400" />
            </div>
            <p className="text-sm font-medium text-slate-400 mb-1">No Active Chat History</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Use the 1-Click controls on the right or type a message below to report an issue for Alice Chen.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className="space-y-1">
            <div className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.sender === 'agent' && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-indigo-400" />
                </div>
              )}

              <div className={`max-w-[82%] rounded-xl px-4 py-2.5 text-xs shadow-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}>
                {msg.text}

                {/* Metadata Badge for Agent Responses */}
                {msg.action && (
                  <div className="mt-2 pt-1.5 border-t border-slate-800 flex items-center gap-1.5 text-[10px] text-indigo-400 font-mono">
                    <Zap className="w-3 h-3 text-indigo-400 shrink-0" />
                    <span className="truncate">{msg.action}</span>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-slate-300" />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Visual Session Break Divider */}
        {sessionBreakActive && (
          <div className="py-3 flex items-center justify-center">
            <div className="bg-amber-950/40 border border-amber-500/40 text-amber-300 px-4 py-1.5 rounded-full text-xs font-mono flex items-center gap-2 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
              SESSION BREAK: IN-MEMORY CHAT WIPED (NEO4J RETAINS PERSISTENCE)
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-indigo-400 animate-spin" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-slate-400 flex items-center gap-2">
              <span className="animate-pulse">Traversing Neo4j Graph Memory...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Field */}
      <form onSubmit={handleSubmit} className="p-3 bg-slate-900/90 border-t border-slate-800 flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type message as Alice Chen (e.g. 'It's still not working.')..."
          disabled={isProcessing}
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50 placeholder:text-slate-500"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isProcessing}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50 shadow-md shadow-indigo-600/20"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}

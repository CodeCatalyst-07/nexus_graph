import React from 'react';
import { Database, RotateCcw, User, Eye, EyeOff } from 'lucide-react';

export default function Header({ onReset, isProcessing, showBaseline, setShowBaseline }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-lg text-white font-bold flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Database className="w-5 h-5 text-indigo-200" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-white tracking-wide">NexusGraph Support</h1>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono">
              Agent Memory
            </span>
          </div>
          <p className="text-xs text-slate-400">Context-Aware AI Support Memory with Neo4j Graph Reasoning</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Baseline Comparison Toggle */}
        <button
          onClick={() => setShowBaseline(!showBaseline)}
          className={`text-xs px-3 py-1.5 rounded-md border flex items-center gap-1.5 transition-all ${
            showBaseline 
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' 
              : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
          }`}
          title="Compare with standard chatbot without memory"
        >
          {showBaseline ? <Eye className="w-3.5 h-3.5 text-amber-400" /> : <EyeOff className="w-3.5 h-3.5" />}
          {showBaseline ? 'Hide Amnesiac Baseline' : 'Show Amnesiac Baseline'}
        </button>

        {/* Demo Persona Badge */}
        <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg text-xs">
          <User className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-slate-300 font-medium">Alice Chen</span>
          <span className="text-slate-500 font-mono">(alice@techcorp.io)</span>
        </div>

        {/* Neo4j Connection Indicator */}
        <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-xs text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-medium">Neo4j AuraDB</span>
        </div>

        {/* Reset Demo Button */}
        <button
          onClick={onReset}
          disabled={isProcessing}
          className="flex items-center gap-1.5 bg-slate-800 hover:bg-rose-900/40 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-700/50 px-3 py-1.5 rounded-lg text-xs transition-colors disabled:opacity-50"
          title="Reset tickets and graph state"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Demo
        </button>
      </div>
    </header>
  );
}

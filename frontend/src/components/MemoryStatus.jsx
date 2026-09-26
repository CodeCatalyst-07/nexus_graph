import React from 'react';
import { ShieldAlert, CheckCircle2, Clock, AlertTriangle, Layers } from 'lucide-react';

export default function MemoryStatus({ context, ticketStatus }) {
  if (!context && !ticketStatus) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-500" />
          <span>Active Graph Memory: <span className="text-slate-300 font-medium">Ready (Awaiting First Issue)</span></span>
        </div>
        <span className="text-slate-500 font-mono">Customer: alice@techcorp.io</span>
      </div>
    );
  }

  const status = ticketStatus || context?.ticket_status || 'OPEN';
  const outcomeStatus = context?.last_outcome_status || 'PENDING';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Active Graph Context
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Ticket Status Badge */}
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-medium flex items-center gap-1 border ${
            status === 'ESCALATED'
              ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
              : status === 'RESOLVED'
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          }`}>
            {status === 'ESCALATED' && <AlertTriangle className="w-3 h-3 text-orange-400" />}
            {status === 'RESOLVED' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
            {status === 'OPEN' && <Clock className="w-3 h-3 text-amber-400" />}
            Ticket #{context?.ticket_id || 'TK-101'}: {status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-xs">
        <div className="bg-slate-800/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block text-[10px] uppercase font-mono">Product</span>
          <span className="text-slate-200 font-medium truncate block" title={context?.product_name || 'GDS Workspace'}>
            {context?.product_name || 'GDS Workspace'}
          </span>
        </div>

        <div className="bg-slate-800/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block text-[10px] uppercase font-mono">Reported Error</span>
          <span className="text-purple-400 font-mono font-bold">
            Error {context?.error_code || '403'}
          </span>
        </div>

        <div className="bg-slate-800/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block text-[10px] uppercase font-mono">Last Prescribed Fix</span>
          <span className="text-slate-300 font-mono truncate block" title={context?.last_action_name || 'CLEAR_SSO_CACHE'}>
            {context?.last_action_name || 'CLEAR_SSO_CACHE'}
          </span>
        </div>

        <div className="bg-slate-800/60 p-2 rounded border border-slate-800">
          <span className="text-slate-400 block text-[10px] uppercase font-mono">Verification Outcome</span>
          <span className={`font-mono font-bold flex items-center gap-1 ${
            outcomeStatus === 'FAILED'
              ? 'text-rose-400'
              : outcomeStatus === 'SUCCESS'
              ? 'text-emerald-400'
              : 'text-amber-400'
          }`}>
            {outcomeStatus === 'FAILED' ? 'FAILED ❌' : outcomeStatus === 'SUCCESS' ? 'SUCCESS ✅' : 'PENDING ⏳'}
          </span>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { Play, Sparkles, Scissors, CornerDownLeft, RefreshCw } from 'lucide-react';

export default function DemoControls({
  onSeed,
  onSendSession1,
  onSimulateBreak,
  onSendSession2,
  onReset,
  isProcessing,
  currentStep
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
          <Play className="w-3.5 h-3.5 fill-indigo-400 text-indigo-400" />
          3-Minute Pitch Script Controls
        </span>
        <span className="text-[11px] text-slate-500 font-mono">1-Click Live Rehearsal</span>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {/* Step 1: Seed */}
        <button
          onClick={onSeed}
          disabled={isProcessing}
          className={`px-2.5 py-2 rounded-lg border text-left flex flex-col justify-between transition-all ${
            currentStep === 1
              ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-300'
          } disabled:opacity-50`}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="text-[10px] font-mono text-indigo-400 font-bold">STEP 1</span>
            <Sparkles className="w-3 h-3 text-indigo-300" />
          </div>
          <span className="text-xs font-semibold leading-tight">Seed Customer</span>
          <span className="text-[10px] text-slate-400 mt-0.5">Alice + GDS</span>
        </button>

        {/* Step 2: Session 1 */}
        <button
          onClick={onSendSession1}
          disabled={isProcessing}
          className={`px-2.5 py-2 rounded-lg border text-left flex flex-col justify-between transition-all ${
            currentStep === 2
              ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-300'
          } disabled:opacity-50`}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="text-[10px] font-mono text-indigo-400 font-bold">STEP 2</span>
            <CornerDownLeft className="w-3 h-3 text-indigo-300" />
          </div>
          <span className="text-xs font-semibold leading-tight">Send S1 Issue</span>
          <span className="text-[10px] text-slate-400 mt-0.5">Report Error 403</span>
        </button>

        {/* Step 3: Simulate Break */}
        <button
          onClick={onSimulateBreak}
          disabled={isProcessing}
          className={`px-2.5 py-2 rounded-lg border text-left flex flex-col justify-between transition-all ${
            currentStep === 3
              ? 'bg-amber-600/20 border-amber-500 text-white shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-300'
          } disabled:opacity-50`}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="text-[10px] font-mono text-amber-400 font-bold">STEP 3</span>
            <Scissors className="w-3 h-3 text-amber-300" />
          </div>
          <span className="text-xs font-semibold leading-tight">Simulate Break</span>
          <span className="text-[10px] text-amber-300/80 mt-0.5">Wipe UI History</span>
        </button>

        {/* Step 4: Session 2 */}
        <button
          onClick={onSendSession2}
          disabled={isProcessing}
          className={`px-2.5 py-2 rounded-lg border text-left flex flex-col justify-between transition-all ${
            currentStep === 4
              ? 'bg-emerald-600/20 border-emerald-500 text-white shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-300'
          } disabled:opacity-50`}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="text-[10px] font-mono text-emerald-400 font-bold">STEP 4</span>
            <Play className="w-3 h-3 text-emerald-300 fill-emerald-300" />
          </div>
          <span className="text-xs font-semibold leading-tight">Send S2 Return</span>
          <span className="text-[10px] text-slate-400 mt-0.5">"Still not working"</span>
        </button>

        {/* Step 5: Reset */}
        <button
          onClick={onReset}
          disabled={isProcessing}
          className="px-2.5 py-2 rounded-lg border border-slate-700 hover:border-slate-600 bg-slate-800/80 hover:bg-slate-800 text-slate-300 text-left flex flex-col justify-between transition-all disabled:opacity-50"
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="text-[10px] font-mono text-slate-400 font-bold">STEP 5</span>
            <RefreshCw className="w-3 h-3 text-slate-400" />
          </div>
          <span className="text-xs font-semibold leading-tight">Reset Canvas</span>
          <span className="text-[10px] text-slate-400 mt-0.5">Clear for re-run</span>
        </button>
      </div>
    </div>
  );
}

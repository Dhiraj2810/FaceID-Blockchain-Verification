import React from 'react';
import { ShieldCheck, Cpu, Activity, Database } from 'lucide-react';

export default function Header({ systemStatus }) {
  return (
    <header className="border-b border-slate-800/80 bg-[#0b0f19]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-teal-500 to-emerald-500 p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#080c14] rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-['Outfit']">
                FaceChain<span className="text-cyan-400 font-light">Verifier</span>
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-mono tracking-widest bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded-md uppercase">
                v1.0 Sepolia
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              AI-Powered Evidence Verification & On-Chain Fingerprinting
            </p>
          </div>
        </div>

        {/* System Badges */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono text-[11px]">InsightFace SCRFD + ArcFace</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono text-[11px]">Ethereum Sepolia</span>
          </div>

          {/* System Status Pill */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/50 border border-emerald-500/30 text-emerald-300 font-mono font-medium shadow-sm shadow-emerald-900/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="tracking-wider text-[11px]">SYSTEM {systemStatus || 'ONLINE'}</span>
          </div>
        </div>

      </div>
    </header>
  );
}

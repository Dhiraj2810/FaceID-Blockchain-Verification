import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ImageUploadPanel from './components/ImageUploadPanel';
import VerificationStatusCard from './components/VerificationStatusCard';
import FaceAnalysisCard from './components/FaceAnalysisCard';
import WebEvidenceCard from './components/WebEvidenceCard';
import BlockchainEvidenceCard from './components/BlockchainEvidenceCard';
import FinalVerificationCard from './components/FinalVerificationCard';
import TamperDemoPanel from './components/TamperDemoPanel';
import { AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [systemStatus, setSystemStatus] = useState('CHECKING');
  const [isLoading, setIsLoading] = useState(false);
  const [progressStage, setProgressStage] = useState('');
  const [pipelineResult, setPipelineResult] = useState(null);
  const [errorDetails, setErrorDetails] = useState(null);

  const apiBase = '/api';

  // Check backend API health on startup
  useEffect(() => {
    fetch(`${apiBase}/`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status) setSystemStatus(data.status);
      })
      .catch(() => {
        setSystemStatus('OFFLINE');
      });
  }, [apiBase]);

  // Execute pipeline via POST /verify
  const handleAnalyzeImage = async (file) => {
    setIsLoading(true);
    setErrorDetails(null);
    setPipelineResult(null);
    setProgressStage('Detecting Face (InsightFace SCRFD)...');

    const formData = new FormData();
    formData.append('image', file);

    // Simulated progress stage ticker for visual feedback while backend runs
    const stageTimer1 = setTimeout(() => setProgressStage('ArcFace 512-d Embedding Generation...'), 1500);
    const stageTimer2 = setTimeout(() => setProgressStage('Google Lens Reverse Image Search...'), 3500);
    const stageTimer3 = setTimeout(() => setProgressStage('Verifying Candidate Images & Cosine Similarity...'), 6500);
    const stageTimer4 = setTimeout(() => setProgressStage('Computing SHA-256 & Submitting Sepolia Tx...'), 9500);

    try {
      const response = await fetch(`${apiBase}/verify`, {
        method: 'POST',
        body: formData,
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      clearTimeout(stageTimer4);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'HTTP Request Failed' }));
        throw new Error(errorData.detail || 'Analysis request failed.');
      }

      const result = await response.json();

      if (result.status === 'error') {
        setErrorDetails(result.message || 'Pipeline error encountered.');
      }

      setPipelineResult(result);
    } catch (err) {
      setErrorDetails(err.message);
    } finally {
      setIsLoading(false);
      setProgressStage('');
    }
  };

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col font-['Outfit',sans-serif]">
      {/* Header */}
      <Header systemStatus={systemStatus} />

      {/* Dashboard Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Pipeline Error Banner */}
        {errorDetails && (
          <div className="p-4 rounded-2xl bg-rose-950/50 border border-rose-500/60 text-rose-200 flex items-start gap-3 shadow-xl animate-fade-in">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-xs">
              <h4 className="font-bold text-sm text-rose-300 mb-1">Pipeline Processing Message</h4>
              <p className="font-mono text-rose-200/90">{errorDetails}</p>
            </div>
            <button
              onClick={() => setErrorDetails(null)}
              className="text-xs font-mono text-rose-400 hover:text-white underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Pipeline Warning Banner (e.g. no face detected or no candidates found) */}
        {pipelineResult && pipelineResult.status === 'warning' && (
          <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-500/50 text-amber-200 flex items-start gap-3 shadow-xl">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-xs">
              <h4 className="font-bold text-sm text-amber-300 mb-1">Pipeline Warning</h4>
              <p className="font-mono text-amber-200/90">{pipelineResult.message}</p>
            </div>
          </div>
        )}

        {/* Final Verification Banner (Shows at top when verified evidence exists) */}
        {pipelineResult && pipelineResult.verification && (
          <FinalVerificationCard pipelineResult={pipelineResult} />
        )}

        {/* 2-Column Responsive Desktop-First Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left / Center Column (7 Cols) */}
          <div className="lg:col-span-7 space-y-8">
            {/* Image Upload Area */}
            <ImageUploadPanel
              onAnalyze={handleAnalyzeImage}
              isLoading={isLoading}
              progressStage={progressStage}
            />

            {/* Face Analysis Details */}
            <FaceAnalysisCard pipelineResult={pipelineResult} />

            {/* Web Evidence Results */}
            <WebEvidenceCard pipelineResult={pipelineResult} />

            {/* Tamper Demonstration Panel */}
            <TamperDemoPanel pipelineResult={pipelineResult} />
          </div>

          {/* Right Column (5 Cols) */}
          <div className="lg:col-span-5 space-y-8">
            {/* 7-Stage Verification Checklist */}
            <VerificationStatusCard
              pipelineResult={pipelineResult}
              isLoading={isLoading}
            />

            {/* Blockchain Record */}
            <BlockchainEvidenceCard pipelineResult={pipelineResult} />
          </div>

        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#080c14] py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap justify-between items-center gap-4">
          <div>
            FaceChain Verifier © 2026 • HH Goa Task 3 Prototype
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>InsightFace CPU</span>
            <span>•</span>
            <span>SerpApi Lens</span>
            <span>•</span>
            <span>Web3 Sepolia</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

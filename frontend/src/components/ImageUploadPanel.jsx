import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, Sparkles, X, CheckCircle2, AlertTriangle, Loader2, User } from 'lucide-react';

export default function ImageUploadPanel({ onAnalyze, isLoading, progressStage }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [imageMeta, setImageMeta] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('Please select a valid image file (JPG or PNG).');
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Read image dimensions
    const img = new Image();
    img.src = objectUrl;
    img.onload = () => {
      setImageMeta({
        width: img.width,
        height: img.height,
        sizeMB: (file.size / (1024 * 1024)).toFixed(2),
        name: file.name
      });
    };
  };

  const handleLoadSample = async (e) => {
    e.stopPropagation();
    try {
      const res = await fetch('/sample_face.jpg');
      if (!res.ok) throw new Error('Failed to load sample image');
      const blob = await res.blob();
      const file = new File([blob], 'sample_face.jpg', { type: 'image/jpeg' });
      handleFile(file);
    } catch (err) {
      alert('Could not load sample image: ' + err.message);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageMeta(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = () => {
    if (selectedFile && !isLoading) {
      onAnalyze(selectedFile);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden border border-slate-800/80 shadow-2xl">
      {/* Decorative cyber grid lines */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white font-['Outfit']">Target Face Evidence Input</h2>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded-md border border-slate-800">
          JPG / PNG
        </span>
      </div>

      {!previewUrl ? (
        /* Drag and Drop Zone */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
            isDragging
              ? 'border-cyan-400 bg-cyan-950/30 shadow-lg shadow-cyan-500/10 scale-[1.01]'
              : 'border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900/40 bg-slate-950/40'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            accept="image/jpeg,image/png,image/jpg"
            className="hidden"
          />
          
          <div className="w-16 h-16 rounded-2xl bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4 text-cyan-400 shadow-inner">
            <UploadCloud className="w-8 h-8 animate-pulse" />
          </div>

          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Drag & Drop Target Face Image Here
          </h3>
          <p className="text-xs text-slate-400 mb-5 max-w-sm mx-auto">
            Upload portrait or social photo containing a clear face for InsightFace detection & Sepolia verification.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              className="px-4 py-2 text-xs font-medium rounded-lg bg-cyan-950/80 text-cyan-300 border border-cyan-700/50 hover:bg-cyan-900 hover:border-cyan-500 transition-all shadow-sm"
            >
              Browse Local File
            </button>

            <button
              type="button"
              onClick={handleLoadSample}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-700/50 hover:bg-emerald-900 hover:border-emerald-500 transition-all shadow-sm flex items-center gap-1.5"
            >
              <User className="w-3.5 h-3.5 text-emerald-400" />
              <span>Use Sample Image</span>
            </button>
          </div>
        </div>
      ) : (
        /* Image Preview Panel */
        <div className="space-y-4">
          <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-black/60 aspect-video max-h-80 flex items-center justify-center group">
            <img
              src={previewUrl}
              alt="Preview"
              className="max-h-full max-w-full object-contain rounded-lg"
            />

            {/* Clear Image Overlay Button */}
            {!isLoading && (
              <button
                onClick={handleClear}
                className="absolute top-3 right-3 p-1.5 rounded-full bg-slate-950/80 text-slate-300 hover:text-white hover:bg-rose-950/90 hover:border-rose-500 border border-slate-700 transition-all shadow-md"
                title="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Cyber Scanning Overlay line when loading */}
            {isLoading && (
              <div className="absolute inset-0 bg-cyan-950/20 backdrop-blur-[1px] flex flex-col items-center justify-center">
                <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#06b6d4] animate-scanline"></div>
                <div className="absolute bottom-4 bg-slate-950/90 border border-cyan-500/40 px-4 py-2 rounded-lg text-xs font-mono text-cyan-300 flex items-center gap-2 shadow-xl">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                  <span>{progressStage || 'Executing Pipeline...'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Image Metadata Strip */}
          {imageMeta && (
            <div className="flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span className="truncate max-w-[200px]" title={imageMeta.name}>
                📄 {imageMeta.name}
              </span>
              <span>
                📐 {imageMeta.width} × {imageMeta.height} px
              </span>
              <span>
                💾 {imageMeta.sizeMB} MB
              </span>
            </div>
          )}

          {/* Action Button */}
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm tracking-wide flex items-center justify-center gap-2.5 transition-all shadow-lg ${
              isLoading
                ? 'bg-slate-900 text-slate-500 border border-slate-800 cursor-not-allowed'
                : 'bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-cyan-500/20 hover:shadow-cyan-500/30 hover:scale-[1.005] active:scale-[0.995] border border-cyan-400/30'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                <span>ANALYZING EVIDENCE...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 text-cyan-200" />
                <span>ANALYZE IMAGE & VERIFY ON BLOCKCHAIN</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

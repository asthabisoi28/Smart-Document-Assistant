import React, { useState, useRef } from 'react';
import { UploadCloud, FileUp, CheckCircle, AlertCircle, FileText } from 'lucide-react';

export default function DocumentUpload({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;

    // Validate extensions
    const validFiles = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop().toLowerCase();
      if (ext === 'pdf' || ext === 'txt') {
        validFiles.push(file);
      }
    }

    if (validFiles.length === 0) {
      setErrorMessage('Please upload valid PDF or TXT documents.');
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setIsUploading(true);

    try {
      const { uploadDocuments } = await import('../services/api');
      const uploaded = await uploadDocuments(validFiles);
      setSuccessMessage(`Successfully uploaded and indexed ${uploaded.length} document(s).`);
      if (onUploadComplete) {
        onUploadComplete(uploaded);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Error uploading files');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setTimeout(() => setSuccessMessage(null), 4000);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <FileUp className="w-4 h-4 text-brand-600" />
          Upload Documents
        </h2>
        <span className="text-[11px] text-slate-400 font-medium">Supports PDF & TXT</span>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-2.5 ${
          isDragging
            ? 'border-brand-500 bg-brand-50/50 scale-[0.99]'
            : 'border-slate-200 hover:border-brand-400 hover:bg-slate-50/60'
        } ${isUploading ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 group-hover:text-brand-600 transition-colors">
          {isUploading ? (
            <span className="inline-block w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
          ) : (
            <UploadCloud className="w-6 h-6 text-brand-600" />
          )}
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-700">
            {isUploading ? 'Parsing & Indexing into FAISS...' : 'Click to upload or drag and drop'}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Single or multiple PDF or TXT files
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useCallback } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { formatFileSize, isValidPDF, validateFileSize } from '@/lib/utils';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  disabled?: boolean;
  maxSizeMB?: number;
}

export default function FileUpload({ 
  onFileSelect, 
  isUploading = false, 
  disabled = false,
  maxSizeMB = 50 
}: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (!isValidPDF(file)) {
      return 'Only PDF files are supported';
    }
    
    if (!validateFileSize(file, maxSizeMB)) {
      return `File size must be less than ${maxSizeMB}MB`;
    }
    
    return null;
  }, [maxSizeMB]);

  const handleFileSelect = useCallback((file: File) => {
    const validationError = validateFile(file);
    
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    
    setError(null);
    setSelectedFile(file);
    onFileSelect(file);
  }, [validateFile, onFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isUploading) {
      setDragOver(true);
    }
  }, [disabled, isUploading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    if (disabled || isUploading) return;
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [disabled, isUploading, handleFileSelect]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  const isDisabled = disabled || isUploading;

  return (
    <div className="w-full">
      <div
        className={`
          upload-area relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300
          ${dragOver && !isDisabled ? 'drag-over border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-400 hover:bg-gray-50'}
          ${error ? 'border-red-300 bg-red-50' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isDisabled && document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          className="hidden"
          disabled={isDisabled}
        />
        
        {isUploading ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-gray-600">Uploading and processing...</p>
          </div>
        ) : selectedFile ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="flex items-center space-x-3 p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
              <FileText className="h-8 w-8 text-blue-500" />
              <div className="flex-1 text-left">
                <p className="font-medium text-gray-900 truncate max-w-xs">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                disabled={isDisabled}
              >
                <X className="h-4 w-4 text-gray-400" />
              </button>
            </div>
            <p className="text-sm text-gray-500">
              Click to select a different file or drag and drop
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <Upload className={`h-12 w-12 ${error ? 'text-red-400' : 'text-gray-400'}`} />
            <div>
              <p className={`text-lg font-medium ${error ? 'text-red-600' : 'text-gray-900'}`}>
                {error ? 'Upload Error' : 'Upload PDF File'}
              </p>
              <p className={`text-sm ${error ? 'text-red-500' : 'text-gray-500'}`}>
                {error || `Drag and drop your PDF file here, or click to browse (max ${maxSizeMB}MB)`}
              </p>
            </div>
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-3 flex items-center space-x-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  );
} 
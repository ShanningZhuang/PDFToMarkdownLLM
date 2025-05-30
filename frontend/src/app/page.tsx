'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { FileText, Settings, RefreshCw, Zap, Clock } from 'lucide-react';
import FileUpload from '@/components/FileUpload';
import MarkdownPreview from '@/components/MarkdownPreview';
import StatusIndicator, { StatusType } from '@/components/StatusIndicator';
import { apiService, UploadResponse } from '@/lib/api';
import { formatDuration, formatFileSize } from '@/lib/utils';

interface ProcessingStats {
  startTime: number;
  firstTokenTime?: number;
  endTime?: number;
  tokenCount: number;
  fileSize?: number;
  fileName?: string;
}

export default function HomePage() {
  const [markdownContent, setMarkdownContent] = useState('');
  const [rawMarkdownContent, setRawMarkdownContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<StatusType>('idle');
  const [statusMessage, setStatusMessage] = useState('Ready to process PDF files');
  const [statusDetails, setStatusDetails] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [cleanWithLLM, setCleanWithLLM] = useState(true);
  const [processingStats, setProcessingStats] = useState<ProcessingStats | null>(null);
  const [backendHealth, setBackendHealth] = useState<'unknown' | 'healthy' | 'unhealthy'>('unknown');

  // Check backend health on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      await apiService.checkHealth();
      setBackendHealth('healthy');
    } catch (error) {
      setBackendHealth('unhealthy');
      setStatus('error');
      setStatusMessage('Backend service is not available');
      setStatusDetails('Please make sure the backend is running on http://localhost:8001');
    }
  };

  const resetState = useCallback(() => {
    setMarkdownContent('');
    setRawMarkdownContent('');
    setIsStreaming(false);
    setIsProcessing(false);
    setStatus('idle');
    setStatusMessage('Ready to process PDF files');
    setStatusDetails('');
    setProcessingStats(null);
  }, []);

  const handleFileSelect = useCallback(async (file: File) => {
    resetState();
    
    const stats: ProcessingStats = {
      startTime: Date.now(),
      tokenCount: 0,
      fileSize: file.size,
      fileName: file.name,
    };
    setProcessingStats(stats);

    if (useStreaming && cleanWithLLM) {
      await handleStreamingUpload(file, stats);
    } else {
      await handleRegularUpload(file, stats);
    }
  }, [useStreaming, cleanWithLLM]);

  const handleStreamingUpload = async (file: File, stats: ProcessingStats) => {
    setIsStreaming(true);
    setIsProcessing(true);
    setStatus('streaming');
    setStatusMessage('Uploading and processing with streaming...');
    setStatusDetails(`Processing ${file.name} (${formatFileSize(file.size)})`);

    try {
      const reader = await apiService.uploadPDFStream(file);
      const decoder = new TextDecoder();
      let content = '';
      let isFirstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // Handle metadata chunk (first chunk)
        if (isFirstChunk && chunk.startsWith('data:')) {
          try {
            const metadataStr = chunk.replace('data: ', '').trim();
            const metadata = JSON.parse(metadataStr);
            setStatusDetails(`File: ${metadata.filename} | Raw content: ${metadata.raw_content_length} chars`);
            isFirstChunk = false;
            continue;
          } catch (e) {
            // If not valid JSON, treat as regular content
          }
        }

        content += chunk;
        setMarkdownContent(content);
        
        // Update stats
        const updatedStats = { 
          ...stats, 
          tokenCount: stats.tokenCount + 1,
          firstTokenTime: stats.firstTokenTime || Date.now()
        };
        setProcessingStats(updatedStats);

        if (updatedStats.tokenCount % 10 === 0) {
          const elapsed = Date.now() - stats.startTime;
          setStatusDetails(`Tokens received: ${updatedStats.tokenCount} | Time: ${formatDuration(elapsed)}`);
        }
      }

      const finalStats = {
        ...stats,
        endTime: Date.now(),
        tokenCount: content.length,
      };
      setProcessingStats(finalStats);

      setIsStreaming(false);
      setIsProcessing(false);
      setStatus('success');
      setStatusMessage('Streaming completed successfully!');
      const totalTime = finalStats.endTime - finalStats.startTime;
      setStatusDetails(`Processed ${finalStats.tokenCount} characters in ${formatDuration(totalTime)}`);

    } catch (error) {
      setIsStreaming(false);
      setIsProcessing(false);
      setStatus('error');
      setStatusMessage('Streaming failed');
      setStatusDetails(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  };

  const handleRegularUpload = async (file: File, stats: ProcessingStats) => {
    setIsProcessing(true);
    setStatus('processing');
    setStatusMessage('Uploading and processing...');
    setStatusDetails(`Processing ${file.name} (${formatFileSize(file.size)})`);

    try {
      let response: UploadResponse;
      
      if (cleanWithLLM) {
        response = await apiService.uploadPDF(file, true);
      } else {
        response = await apiService.convertPDFToText(file);
      }

      const finalStats = {
        ...stats,
        endTime: Date.now(),
        tokenCount: response.cleaned_markdown.length,
      };
      setProcessingStats(finalStats);

      setRawMarkdownContent(response.raw_markdown);
      setMarkdownContent(response.cleaned_markdown);
      setIsProcessing(false);
      setStatus('success');
      setStatusMessage('Processing completed successfully!');
      
      const totalTime = finalStats.endTime - finalStats.startTime;
      const cleaningStatus = response.cleaned_with_llm ? 'with LLM cleaning' : 'without LLM cleaning';
      setStatusDetails(`Processed ${response.content_length} characters in ${formatDuration(totalTime)} ${cleaningStatus}`);

    } catch (error) {
      setIsProcessing(false);
      setStatus('error');
      setStatusMessage('Processing failed');
      setStatusDetails(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  };

  const handleDownload = useCallback(() => {
    if (!markdownContent) return;
    
    const filename = processingStats?.fileName 
      ? `${processingStats.fileName.replace('.pdf', '')}-converted.md`
      : 'converted-document.md';
    
    const blob = new Blob([markdownContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [markdownContent, processingStats]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">PDF to Markdown Converter</h1>
                <p className="text-sm text-gray-600">AI-powered document conversion with real-time streaming</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Backend Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  backendHealth === 'healthy' ? 'bg-green-500' : 
                  backendHealth === 'unhealthy' ? 'bg-red-500' : 
                  'bg-yellow-500'
                }`} />
                <span className="text-xs text-gray-600">
                  Backend {backendHealth === 'healthy' ? 'Online' : backendHealth === 'unhealthy' ? 'Offline' : 'Checking...'}
                </span>
              </div>
              
              <button
                onClick={checkBackendHealth}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Refresh backend status"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Upload and Settings */}
          <div className="space-y-6">
            {/* Settings Panel */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Settings className="h-5 w-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Processing Options</h2>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Enable LLM Cleaning</label>
                    <p className="text-xs text-gray-500">Use AI to clean and improve markdown formatting</p>
                  </div>
                  <button
                    onClick={() => setCleanWithLLM(!cleanWithLLM)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      cleanWithLLM ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                    disabled={isProcessing}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        cleanWithLLM ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Enable Streaming</label>
                    <p className="text-xs text-gray-500">See results as they are generated (requires LLM cleaning)</p>
                  </div>
                  <button
                    onClick={() => setUseStreaming(!useStreaming)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      useStreaming && cleanWithLLM ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                    disabled={isProcessing || !cleanWithLLM}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        useStreaming && cleanWithLLM ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <FileUpload
              onFileSelect={handleFileSelect}
              isUploading={isProcessing}
              disabled={backendHealth !== 'healthy'}
            />

            {/* Status */}
            <StatusIndicator
              status={status}
              message={statusMessage}
              details={statusDetails}
            />

            {/* Processing Stats */}
            {processingStats && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Statistics</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">File:</span>
                    <p className="font-medium truncate">{processingStats.fileName}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Size:</span>
                    <p className="font-medium">{processingStats.fileSize ? formatFileSize(processingStats.fileSize) : 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Characters:</span>
                    <p className="font-medium">{processingStats.tokenCount.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <p className="font-medium">
                      {processingStats.endTime 
                        ? formatDuration(processingStats.endTime - processingStats.startTime)
                        : formatDuration(Date.now() - processingStats.startTime)
                      }
                    </p>
                  </div>
                  {processingStats.firstTokenTime && (
                    <>
                      <div>
                        <span className="text-gray-600">First Token:</span>
                        <p className="font-medium">{formatDuration(processingStats.firstTokenTime - processingStats.startTime)}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Mode:</span>
                        <p className="font-medium flex items-center">
                          {isStreaming ? (
                            <>
                              <Zap className="h-3 w-3 mr-1 text-green-500" />
                              Streaming
                            </>
                          ) : (
                            <>
                              <Clock className="h-3 w-3 mr-1 text-blue-500" />
                              Batch
                            </>
                          )}
                        </p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Preview */}
          <div>
            <MarkdownPreview
              content={markdownContent}
              isStreaming={isStreaming}
              title="Converted Markdown"
              onDownload={handleDownload}
            />
          </div>
        </div>
      </main>
    </div>
  );
} 
import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { 
  Upload as UploadIcon, 
  FileText, 
  FileCode, 
  FileType, 
  File, 
  X, 
  CheckCircle2,
  Loader2,
  Sparkles
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const Upload: React.FC = () => {
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'html':
        return <FileCode className="w-8 h-8 text-blue-500" />;
      case 'markdown':
        return <FileText className="w-8 h-8" style={{ color: '#005dac' }} />;
      case 'pdf':
        return <FileText className="w-8 h-8 text-red-500" />;
      case 'docx':
        return <File className="w-8 h-8 text-blue-600" />;
      default:
        return <FileType className="w-8 h-8 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const fileExt = droppedFile.name.split('.').pop()?.toLowerCase();
      if (['html', 'md', 'pdf', 'docx'].includes(fileExt || '')) {
        setFile(droppedFile);
        if (!contentType) {
          setContentType(fileExt === 'md' ? 'markdown' : fileExt || '');
        }
        setError(null);
      } else {
        setError('Please upload HTML, Markdown, PDF, or DOCX files only');
      }
    }
  }, [contentType]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!file || !title || !contentType) {
      setError('Please fill all fields');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('content_type', contentType);
      formData.append('file', file);

      await api.uploadSubmission(formData);
      setSuccess(true);

      // Navigate to submissions after a brief delay
      setTimeout(() => {
        navigate('/submissions');
      }, 1500);
    } catch (error: any) {
      console.error('Upload failed:', error);
      setError(error.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-blue-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 shadow-lg" style={{ backgroundColor: '#005dac' }}>
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Upload Content</h1>
          <p className="text-lg text-gray-600">
            Upload your marketing content for AI-powered compliance analysis
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Upload Form */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-xl border-0">
              <CardHeader>
                <CardTitle>Content Details</CardTitle>
                <CardDescription>Provide information about your content</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Title Input */}
                  <div>
                    <label htmlFor="title" className="block text-sm font-semibold text-gray-700 mb-2">
                      Content Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="title"
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g., Q4 Life Insurance Campaign"
                      required
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-transparent transition-all"
                      style={{ 
                        '--tw-ring-color': '#005dac',
                      } as React.CSSProperties & { '--tw-ring-color': string }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#005dac';
                        e.target.style.boxShadow = '0 0 0 2px #005dac';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '';
                        e.target.style.boxShadow = '';
                      }}
                    />
                  </div>

                  {/* Content Type Select */}
                  <div>
                    <label htmlFor="content-type" className="block text-sm font-semibold text-gray-700 mb-2">
                      Content Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="content-type"
                      value={contentType}
                      onChange={(e) => setContentType(e.target.value)}
                      required
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-transparent transition-all bg-white"
                      style={{ 
                        '--tw-ring-color': '#005dac',
                      } as React.CSSProperties & { '--tw-ring-color': string }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#005dac';
                        e.target.style.boxShadow = '0 0 0 2px #005dac';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '';
                        e.target.style.boxShadow = '';
                      }}
                    >
                      <option value="">Select content type</option>
                      <option value="html">HTML</option>
                      <option value="markdown">Markdown</option>
                      <option value="pdf">PDF</option>
                      <option value="docx">DOCX</option>
                    </select>
                  </div>

                  {/* File Upload Area */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Upload File <span className="text-red-500">*</span>
                    </label>
                    <div
                      onDragEnter={handleDragEnter}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
                        isDragging
                          ? 'scale-105'
                          : file
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-300 bg-gray-50'
                      }`}
                      style={{
                        borderColor: isDragging ? '#005dac' : file ? undefined : undefined,
                        backgroundColor: isDragging ? '#e6f2ff' : file ? undefined : undefined,
                      }}
                      onMouseEnter={(e) => {
                        if (!file && !isDragging) {
                          e.currentTarget.style.borderColor = '#005dac';
                          e.currentTarget.style.backgroundColor = '#e6f2ff';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!file && !isDragging) {
                          e.currentTarget.style.borderColor = '';
                          e.currentTarget.style.backgroundColor = '';
                        }
                      }}
                    >
                      <input
                        ref={fileInputRef}
                        id="file"
                        type="file"
                        onChange={handleFileSelect}
                        accept=".html,.md,.pdf,.docx"
                        required
                        className="hidden"
                      />

                      {!file ? (
                        <div className="text-center">
                          <div className="flex justify-center mb-4">
                            <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ backgroundColor: '#005dac' }}>
                              <UploadIcon className="w-8 h-8 text-white" />
                            </div>
                          </div>
                          <p className="text-lg font-semibold text-gray-700 mb-2">
                            Drag & drop your file here
                          </p>
                          <p className="text-sm text-gray-500 mb-4">or</p>
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="px-6 py-2 text-white rounded-lg transition-all shadow-lg hover:shadow-xl"
                            style={{ backgroundColor: '#005dac' }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004a8a'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#005dac'}
                          >
                            Browse Files
                          </button>
                          <p className="text-xs text-gray-400 mt-4">
                            Supported: HTML, Markdown, PDF, DOCX (Max 50MB)
                          </p>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            {getFileIcon(contentType)}
                            <div>
                              <p className="font-semibold text-gray-900">{file.name}</p>
                              <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={removeFile}
                            className="p-2 hover:bg-red-100 rounded-full transition-colors"
                          >
                            <X className="w-5 h-5 text-red-500" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Error Message */}
                  {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                      <X className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  )}

                  {/* Success Message */}
                  {success && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                      <p className="text-sm text-green-700">Upload successful! Redirecting...</p>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={uploading || !file || !title || !contentType}
                    className="w-full flex items-center justify-center gap-3 text-white px-6 py-4 rounded-lg disabled:from-gray-400 disabled:via-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl font-semibold text-lg"
                    style={{ backgroundColor: uploading || !file || !title || !contentType ? '#9ca3af' : '#005dac' }}
                    onMouseEnter={(e) => {
                      if (!uploading && file && title && contentType) {
                        e.currentTarget.style.backgroundColor = '#004a8a';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!uploading && file && title && contentType) {
                        e.currentTarget.style.backgroundColor = '#005dac';
                      }
                    }}
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <UploadIcon className="w-5 h-5" />
                        Upload and Check Compliance
                      </>
                    )}
                  </button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Info Sidebar */}
          <div className="space-y-6">
            <Card className="shadow-xl border-0 text-white" style={{ backgroundColor: '#005dac' }}>
              <CardHeader>
                <CardTitle className="text-white">What We Check</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-white mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">IRDAI Regulations</p>
                    <p className="text-sm opacity-90">50% weight</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-white mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Brand Guidelines</p>
                    <p className="text-sm opacity-90">30% weight</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-white mt-2 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">SEO Best Practices</p>
                    <p className="text-sm opacity-90">20% weight</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-gray-600">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <p>Ensure your content is complete before uploading</p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <p>Analysis typically takes 10-30 seconds</p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <p>You'll receive detailed violation reports</p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <p>AI-powered suggestions for fixes included</p>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-lg border-2" style={{ borderColor: '#005dac' }}>
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: '#e6f2ff' }}>
                  <Sparkles className="w-6 h-6" style={{ color: '#005dac' }} />
                </div>
                <p className="font-semibold text-gray-900 mb-1">AI-Powered Analysis</p>
                <p className="text-xs text-gray-500">
                  Powered by Ollama qwen2.5:7b model for intelligent compliance checking
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

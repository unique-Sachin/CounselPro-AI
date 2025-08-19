"use client";

import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import {
  uploadCatalogFiles,
  indexAllCatalogFiles,
  unindexCatalogFile,
  deleteCatalogFile,
  listCatalogFiles,
  CatalogFile
} from "@/lib/services/catalog";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, File, Trash2, Calendar, HardDrive, Loader2 } from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

// Types
type FileStatus = "uploaded" | "indexed" | "failed";
type UploadedFile = CatalogFile;

const ACCEPTED_FILE_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
  'text/markdown': '.md',
  'application/msword': '.doc', // Legacy Word format
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getFileIcon = (type: string) => {
  if (type === 'application/pdf') return '📄';
  if (type.includes('word') || type.includes('document')) return '📝';
  if (type === 'text/plain') return '📋';
  if (type === 'text/markdown') return '📖';
  return '📄';
};

const getFileTypeLabel = (type: string) => {
  if (type === 'application/pdf') return 'PDF';
  if (type.includes('word') || type.includes('document')) return 'DOCX';
  if (type === 'text/plain') return 'TXT';
  if (type === 'text/markdown') return 'MD';
  return type.split('/')[1]?.toUpperCase() || 'FILE';
};

const getStatusBadgeVariant = (status: FileStatus, isIndexing?: boolean): "default" | "secondary" | "destructive" | "outline" => {
  if (isIndexing) return 'outline';
  if (status === 'indexed') return 'default';
  if (status === 'failed') return 'destructive';
  return 'secondary';
};

const getStatusLabel = (status: FileStatus, isIndexing?: boolean) => {
  if (isIndexing) return 'Indexing...';
  if (status === 'indexed') return 'Indexed';
  if (status === 'failed') return 'Failed';
  return 'Uploaded';
};

export default function CatalogsPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [indexingProgress, setIndexingProgress] = useState(0);
  const [indexingFiles, setIndexingFiles] = useState<Set<string>>(new Set());
  const [indexingFileStatus, setIndexingFileStatus] = useState<Record<string, 'indexing' | 'completed' | 'failed'>>({});
  // Fetch files on mount
  useEffect(() => {
    listCatalogFiles()
      .then(files => setUploadedFiles(files))
      .catch((err) => {
        if (err?.response?.status !== 404) {
          toast.error("Failed to load catalog files");
        }
        // If 404, do nothing (no files is valid)
      });
  }, []);

  
 

  // Index All handler with progress tracking
  const handleIndexAll = useCallback(async () => {
    const filesToIndex = uploadedFiles.filter(f => f.status === "uploaded");
    if (filesToIndex.length === 0) return;

    setIndexing(true);
    setIndexingProgress(0);
    setIndexingFileStatus({});
    
    // Initialize indexing status for all files
    const initialStatus: Record<string, 'indexing' | 'completed' | 'failed'> = {};
    filesToIndex.forEach(file => {
      initialStatus[file.uid] = 'indexing';
    });
    setIndexingFileStatus(initialStatus);
    setIndexingFiles(new Set(filesToIndex.map(f => f.uid)));

    let progressInterval: NodeJS.Timeout | null = null;

    try {
      // Simulate progressive indexing (since we don't have streaming API)
      let completed = 0;
      const total = filesToIndex.length;

      // Start the actual indexing
      const indexPromise = indexAllCatalogFiles();
      
      // Simulate progress updates
      progressInterval = setInterval(() => {
        completed += 1;
        const progress = Math.min((completed / total) * 80, 80); // Cap at 80% until real completion
        setIndexingProgress(progress);
        
        if (completed < total) {
          // Update individual file status
          const currentFile = filesToIndex[completed - 1];
          if (currentFile) {
            setIndexingFileStatus(prev => ({
              ...prev,
              [currentFile.uid]: 'completed'
            }));
          }
        }
      }, Math.max(500, 2000 / total)); // Adjust timing based on number of files

      // Wait for actual API response
      const indexedFiles = await indexPromise;
      
      // Clear interval and finalize
      if (progressInterval) clearInterval(progressInterval);
      setIndexingProgress(100);
      
      // Update all files as completed
      const finalStatus: Record<string, 'indexing' | 'completed' | 'failed'> = {};
      indexedFiles.forEach(file => {
        finalStatus[file.uid] = 'completed';
      });
      setIndexingFileStatus(finalStatus);

      // Merge the indexed files with the existing files list
      setUploadedFiles(prev => 
        prev.map(file => {
          const indexedFile = indexedFiles.find(indexed => indexed.uid === file.uid);
          return indexedFile || file;
        })
      );

      // Clean up after a short delay
      setTimeout(() => {
        setIndexing(false);
        setIndexingProgress(0);
        setIndexingFiles(new Set());
        setIndexingFileStatus({});
      }, 1000);

      toast.success("All uploaded files have been indexed");

    } catch (error) {
      if (progressInterval) clearInterval(progressInterval);
      setIndexing(false);
      setIndexingProgress(0);
      setIndexingFiles(new Set());
      setIndexingFileStatus({});
      toast.error((error as Error)?.message || "Failed to index files");
    }
  }, [uploadedFiles]);

  const handleFileUpload = useCallback((files: File[]) => {
    const validFiles = files.filter(file => 
      Object.keys(ACCEPTED_FILE_TYPES).includes(file.type) || 
      file.name.endsWith('.md')
    );
    if (validFiles.length === 0) return;
    toast.promise(
      uploadCatalogFiles(validFiles),
      {
        loading: "Uploading files...",
        success: (newFiles) => {
          setUploadedFiles(prev => [...prev, ...newFiles]);
          return "Files uploaded successfully";
        },
        error: (err) => err?.message || "Failed to upload files"
      }
    );
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileUpload(files);
    }
    // Reset input
    e.target.value = '';
  }, [handleFileUpload]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files);
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const removeFile = useCallback((id: string) => {
    toast.promise(
      deleteCatalogFile(id),
      {
        loading: "Deleting file...",
        success: () => {
          setUploadedFiles(prev => prev.filter(file => file.uid !== id));
          return "File deleted";
        },
        error: (err) => err?.message || "Failed to delete file"
      }
    );
  }, []);

  const toggleFileStatus = useCallback((id: string) => {
    toast.promise(
      unindexCatalogFile(id),
      {
        loading: "Unindexing file...",
        success: (updatedFile) => {
          setUploadedFiles(prev => prev.map(file => file.uid === id ? updatedFile : file));
          return "File marked as uploaded";
        },
        error: (err) => err?.message || "Failed to unindex file"
      }
    );
  }, []);

  return (
    <PageTransition>
      <div className="container max-w-6xl mx-auto py-6">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Catalog Management</h1>
            <p className="text-muted-foreground mt-2">
              Upload and manage your document catalogs. Supported formats: PDF, DOCX, TXT, MD
            </p>
          </div>
          <Button
            variant="default"
            size="sm"
            disabled={!uploadedFiles || uploadedFiles.filter(f => f.status === "uploaded").length === 0 || indexing}
            onClick={handleIndexAll}
            className="mt-4 sm:mt-0 flex items-center gap-2"
          >
            {indexing && <Loader2 className="h-4 w-4 animate-spin" />}
            Index All
          </Button>
        </div>
        
        {/* Progress Bar Section */}
        {indexing && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6"
          >
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium">Indexing Progress</h3>
                    <span className="text-sm text-muted-foreground">
                      {Math.round(indexingProgress)}%
                    </span>
                  </div>
                  <Progress value={indexingProgress} className="w-full" />
                  <p className="text-sm text-muted-foreground">
                    Processing {uploadedFiles.filter(f => f.status === "uploaded").length} files...
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
        <div className="space-y-6">
          {/* File Upload Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Documents
                </CardTitle>
                <CardDescription>
                  Drag and drop files or click to browse. Files start as &ldquo;uploaded&rdquo; and can only be deleted in that state.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragOver
                      ? 'border-primary bg-primary/5'
                      : 'border-muted-foreground/25 hover:border-muted-foreground/50'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">
                    Drop your files here
                  </p>
                  <p className="text-muted-foreground mb-4">
                    Or click to browse and select files
                  </p>
                  <div className="flex items-center justify-center">
                    <Input
                      type="file"
                      multiple
                      accept=".pdf,.docx,.doc,.txt,.md"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="file-upload"
                    />
                    <Button asChild>
                      <label htmlFor="file-upload" className="cursor-pointer">
                        Choose Files
                      </label>
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Supported formats: PDF, DOCX, TXT, MD
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Uploaded Files List */}
          {Array.isArray(uploadedFiles) && uploadedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Uploaded Files ({uploadedFiles.length})
                  </CardTitle>
                  <CardDescription>
                    Manage your uploaded documents • {uploadedFiles.filter(f => f.status === 'indexed').length} indexed, {uploadedFiles.filter(f => f.status === 'uploaded').length} uploaded, {uploadedFiles.filter(f => f.status === 'failed').length} failed
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <AnimatePresence>
                      {uploadedFiles.map((file, index) => (
                        <motion.div
                          key={file.uid + file.status}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          transition={{ duration: 0.2, delay: index * 0.05 }}
                          layout
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/30 transition-colors"
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            {/* File Icon */}
                            <div className="text-2xl shrink-0">
                              {getFileIcon(file.type)}
                            </div>
                            
                            {/* File Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-medium truncate" title={file.filename}>
                                  {file.filename}
                                </p>
                                <Badge variant="outline" className="shrink-0">
                                  {getFileTypeLabel(file.type)}
                                </Badge>
                                <Badge 
                                  variant={getStatusBadgeVariant(file.status, indexingFiles.has(file.uid))} 
                                  className="shrink-0 flex items-center gap-1"
                                >
                                  {indexingFiles.has(file.uid) && indexingFileStatus[file.uid] === 'indexing' && (
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  )}
                                  {getStatusLabel(file.status, indexingFiles.has(file.uid))}
                                </Badge>
                              </div>
                              
                              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <HardDrive className="h-3 w-3" />
                                  <span>{formatFileSize(file.size)}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  <span>{new Date(file.uploaded_at).toLocaleDateString()}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Actions */}
                          <div className="flex items-center gap-2 shrink-0">
                            {/* Unindex Button for indexed files */}
                            {file.status === 'indexed' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => toggleFileStatus(file.uid)}
                                className="text-xs"
                              >
                                Unindex
                              </Button>
                            )}
                            {/* Delete Button - Only enabled for uploaded and failed files */}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(file.uid)}
                              disabled={file.status === 'indexed'}
                              className={`shrink-0 ${
                                file.status === 'indexed' 
                                  ? 'opacity-50 cursor-not-allowed' 
                                  : 'text-destructive hover:text-destructive hover:bg-destructive/10'
                              }`}
                              title={file.status === 'indexed' ? 'Cannot delete indexed files' : 'Delete file'}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
          
          {/* Empty State */}
          {uploadedFiles.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <File className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                    <p className="text-lg text-muted-foreground mb-2">
                      No files uploaded yet
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Upload your first document to get started
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </PageTransition>
  );
}

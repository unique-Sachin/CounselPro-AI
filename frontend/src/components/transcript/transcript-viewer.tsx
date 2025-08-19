"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Clock, FileText, Loader2, BarChart3 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { getRawTranscript, analyzeSession } from "@/lib/services/sessions";
import { useAnalysis } from "@/contexts/analysis-context";

// Types
interface TranscriptUtterance {
  speaker: number;
  text: string;
  start_time: string; // Format: "00:00:04.08"
  end_time: string;   // Format: "00:00:04.80"
  confidence: number;
  role: string;       // "counselor" or "student"
}

interface TranscriptMetadata {
  chunk_name: string;
  processing_time_seconds: number;
  timestamp: string;
  role_mapping: {
    counselor: number;
    student: number;
  };
  total_speakers: number;
}

interface TranscriptData {
  metadata: TranscriptMetadata;
  utterances: TranscriptUtterance[];
}



interface TranscriptViewerProps {
  sessionUid: string;
  data?: TranscriptData;
}

const formatTime = (timeString?: string) => {
  if (!timeString) return null;
  
  // Already in HH:MM:SS.MS format (expected format)
  if (timeString.includes(':')) {
    return timeString;
  }
  
  // Convert seconds to HH:MM:SS.MS format
  const seconds = parseFloat(timeString);
  if (!isNaN(seconds)) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  }
  
  return null;
};

const getBadgeVariant = (role: string) => {
  if (role === 'counselor') return 'default';
  if (role === 'student') return 'secondary';
  return 'outline';
};

export default function TranscriptViewer({ sessionUid, data }: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showOnlyCounselor, setShowOnlyCounselor] = useState(false);
  const { isAnalyzing: globalIsAnalyzing, setIsAnalyzing, setSessionUid, setAnalysisSource } = useAnalysis();

  // Fetch transcript data from API
  const {
    data: transcriptResponse,
    isLoading,
    error,
    isFetching,
    refetch: refetchTranscript,
  } = useQuery({
    queryKey: ["raw-transcript", sessionUid],
    queryFn: () => getRawTranscript(sessionUid),
    enabled: !!sessionUid,
    retry: 1, // Only retry once for transcript fetching
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });

  // Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: () => analyzeSession(sessionUid),
    onMutate: () => {
      // Set global analysis state when starting
      setSessionUid(sessionUid);
      setAnalysisSource('transcript-tab');
      setIsAnalyzing(true);
    },
    onSuccess: () => {
      toast.success("Analysis Completed", {
        description: "Session analysis has been completed successfully. Fetching transcript...",
      });
      // Refetch transcript data after successful analysis
      setTimeout(() => {
        refetchTranscript();
      }, 3000); // Wait 3 seconds for analysis to process and generate transcript
      // Release global lock
      setIsAnalyzing(false);
      setSessionUid(null);
      setAnalysisSource(null);
    },
    onError: (error) => {
      console.error("Analysis failed:", error);
      toast.error("Analysis Failed", {
        description: "Failed to analyze the session. Please try again.",
      });
      // Release global lock on error
      setIsAnalyzing(false);
      setSessionUid(null);
      setAnalysisSource(null);
    },
  });

  const isAnalyzing = analysisMutation.isPending || globalIsAnalyzing;

  // Extract transcript data from API response or use passed data (for backward compatibility)  
  const currentData = transcriptResponse?.raw_transcript || data;
  const utterances = currentData?.utterances || [];

  // Filter utterances based on search and counselor toggle
  const filteredUtterances = utterances.filter((utterance: TranscriptUtterance) => {
    const matchesSearch = searchQuery
      ? utterance.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        utterance.role.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    
    const matchesCounselorFilter = showOnlyCounselor
      ? utterance.role === 'counselor'
      : true;

    return matchesSearch && matchesCounselorFilter;
  });

  // Show loading state while fetching transcript
  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        {/* Controls Skeleton */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Loading Transcript
            </CardTitle>
            <CardDescription>
              Fetching session transcript...
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Search bar skeleton */}
            <Skeleton className="h-10 w-full" />
            
            {/* Toggle skeleton */}
            <div className="flex items-center space-x-2">
              <Skeleton className="h-5 w-10" />
              <Skeleton className="h-4 w-32" />
            </div>
            
            {/* Stats skeleton */}
            <Skeleton className="h-4 w-48" />
          </CardContent>
        </Card>

        {/* Transcript Content Skeleton */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Skeleton className="h-6 w-32" />
            </CardTitle>
            <CardDescription>
              <Skeleton className="h-4 w-96" />
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6 max-h-[600px] overflow-y-auto">
              {[...Array(8)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="space-y-3"
                >
                  {/* Speaker badge and timestamp skeleton */}
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-6 w-20" /> {/* Badge */}
                    <Skeleton className="h-4 w-16" /> {/* Time */}
                    <Skeleton className="h-4 w-24" /> {/* Confidence */}
                  </div>
                  
                  {/* Message text skeleton */}
                  <div className="pl-4 border-l-2 border-l-muted space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    {i % 3 === 0 && <Skeleton className="h-4 w-1/2" />} {/* Vary lengths */}
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Show analyzing overlay when analysis is running
  if (isAnalyzing) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Analyzing Session
            </CardTitle>
            <CardDescription>
              Please wait while we analyze the session and generate transcript...
            </CardDescription>
          </CardHeader>
          <CardContent>
            <motion.div 
              className="text-center py-16"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <motion.div 
                className="mx-auto w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-6"
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <BarChart3 className="w-12 h-12 text-primary" />
              </motion.div>
              <motion.div 
                className="space-y-3"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                <h3 className="text-xl font-semibold">Analysis in Progress</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  We&apos;re analyzing the session content to generate insights and transcript. 
                  This may take a few minutes.
                </p>
                <motion.div 
                  className="flex items-center justify-center gap-2 mt-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                >
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Processing...</span>
                </motion.div>
              </motion.div>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Show error state if fetch failed (optional, can be removed to show placeholder instead)
  if (error) {
    console.warn("Transcript fetch failed:", error);
  }

  // If no data available (either failed to fetch or no transcript exists), show placeholder
  if (!currentData) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Transcript
            </CardTitle>
            <CardDescription>
              Session transcript will appear here after analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <motion.div 
              className="text-center py-12"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <motion.div 
                className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-4"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                <FileText className="w-12 h-12 text-muted-foreground" />
              </motion.div>
              <motion.div 
                className="space-y-4"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                <h3 className="text-lg font-semibold">Transcript not available yet</h3>
                <p className="text-muted-foreground max-w-sm mx-auto">
                  Please analyse the session to view transcript.
                </p>
                
                {/* Analyse Button */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 }}
                >
                  <Button 
                    onClick={() => analysisMutation.mutate()}
                    disabled={isAnalyzing}
                    className="flex items-center gap-2"
                    size="lg"
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="h-4 w-4" />
                        Analyse
                      </>
                    )}
                  </Button>
                  {isAnalyzing && (
                    <motion.p 
                      className="text-sm text-muted-foreground mt-2"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      Please wait while we analyze the session...
                    </motion.p>
                  )}
                </motion.div>
              </motion.div>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div 
      className={`space-y-6 ${isLoading || isAnalyzing ? 'pointer-events-none' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Controls */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <Card className={`${isLoading || isAnalyzing ? 'relative overflow-hidden' : ''}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Transcript Controls
            {(isFetching && !isLoading) || isAnalyzing ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="counselor-only"
              checked={showOnlyCounselor}
              onCheckedChange={setShowOnlyCounselor}
            />
            <Label htmlFor="counselor-only">Show only counselor</Label>
          </div>

          {/* Stats */}
          <div className="text-sm text-muted-foreground">
            {filteredUtterances.length} of {utterances.length} utterances
            {searchQuery && ` matching "${searchQuery}"`}
          </div>
        </CardContent>
      </Card>
      </motion.div>

      {/* Transcript Content */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
      >
        <Card className={`${isLoading || isAnalyzing ? 'relative overflow-hidden' : ''}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Conversation
            {(isFetching && !isLoading) || isAnalyzing ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : null}
          </CardTitle>
          {(currentData as TranscriptData)?.metadata && (
            <CardDescription>
              Processed: {new Date((currentData as TranscriptData).metadata.timestamp).toLocaleString()} • 
              {(currentData as TranscriptData).metadata.total_speakers} speakers • 
              {Math.round((currentData as TranscriptData).metadata.processing_time_seconds)}s processing time
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {filteredUtterances.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchQuery ? `No utterances found matching "${searchQuery}"` : "No utterances to display"}
            </div>
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              <AnimatePresence>
                {filteredUtterances.map((utterance: TranscriptUtterance, index: number) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2, delay: index * 0.02 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant={getBadgeVariant(utterance.role)}>
                        {utterance.role.charAt(0).toUpperCase() + utterance.role.slice(1)}
                      </Badge>
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{formatTime(utterance.start_time)}</span>
                        {utterance.confidence && (
                          <span className="ml-2">
                            {Math.round(utterance.confidence * 100)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-sm leading-relaxed pl-4 border-l-2 border-l-muted">
                      {utterance.text}
                    </p>
                    {index < filteredUtterances.length - 1 && <Separator className="my-4" />}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>
      </motion.div>
    </motion.div>
  );
}

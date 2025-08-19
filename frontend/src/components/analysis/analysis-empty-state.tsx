"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, Loader2, Play } from "lucide-react";
import { analyzeSession } from "@/lib/services/sessions";
import { useAnalysis } from "@/contexts/analysis-context";
import { useNavigationLock } from "@/hooks/use-navigation-lock";
import { toast } from "sonner";

interface AnalysisEmptyStateProps {
  sessionUid: string;
  source?: 'session-details' | 'transcript-tab';
}

export default function AnalysisEmptyState({ 
  sessionUid, 
  source = 'session-details' 
}: AnalysisEmptyStateProps) {
  const queryClient = useQueryClient();
  const { setIsAnalyzing, setSessionUid, setAnalysisSource } = useAnalysis();
  
  // Enable navigation lock when analyzing
  useNavigationLock();

  // Mutation for triggering analysis
  const analysisMutation = useMutation({
    mutationFn: () => analyzeSession(sessionUid),
    onMutate: () => {
      // Set analyzing state to block navigation
      setIsAnalyzing(true);
      setSessionUid(sessionUid);
      setAnalysisSource(source);
      toast.info("Starting analysis...", {
        description: "Please wait while we analyze the session data."
      });
    },
    onSuccess: () => {
      toast.success("Analysis started successfully!", {
        description: "Analysis is now processing. Results will appear shortly."
      });
      
      // Invalidate and refetch both session analysis and raw transcript data
      queryClient.invalidateQueries({
        queryKey: ['session-analysis', sessionUid]
      });
      queryClient.invalidateQueries({
        queryKey: ['raw-transcript', sessionUid]
      });
    },
    onError: (error) => {
      console.error('Analysis trigger failed:', error);
      toast.error("Failed to start analysis", {
        description: error instanceof Error ? error.message : "An unexpected error occurred."
      });
      
      // Reset analyzing state on error
      setIsAnalyzing(false);
      setSessionUid(null);
      setAnalysisSource(null);
    },
    onSettled: () => {
      // Reset analyzing state after mutation completes
      setTimeout(() => {
        setIsAnalyzing(false);
        setSessionUid(null);
        setAnalysisSource(null);
      }, 2000); // Keep locked for 2 seconds to allow refetch
    }
  });

  const isAnalyzing = analysisMutation.isPending;

  const handleAnalyzeClick = () => {
    analysisMutation.mutate();
  };

  return (
    <div>
      <Card>
        <CardContent className="pt-12 pb-12">
          <div className="text-center max-w-md mx-auto">
            {/* Icon */}
            <div className="w-16 h-16 mx-auto mb-6 bg-muted rounded-full flex items-center justify-center">
              {isAnalyzing ? (
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              ) : (
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              )}
            </div>

            {/* Title */}
            <h2 className="text-2xl font-bold mb-3">
              {isAnalyzing ? "Analysis in Progress" : "Analysis Pending"}
            </h2>

            {/* Subtitle */}
            <p className="text-muted-foreground mb-8 leading-relaxed">
              {isAnalyzing 
                ? "We're analyzing the session data to generate transcript and quality metrics. This may take a few minutes."
                : "Run analysis to generate transcript and quality metrics for this session."
              }
            </p>

            {/* Analyze Button */}
            <Button
              onClick={handleAnalyzeClick}
              disabled={isAnalyzing}
              size="lg"
              className="min-w-[140px]"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Analyse
                </>
              )}
            </Button>

            {/* Progress indicator */}
            {isAnalyzing && (
              <div className="mt-6">
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full animate-pulse" style={{ width: '45%' }} />
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Processing session data...
                </p>
              </div>
            )}

            {/* Warning message during analysis */}
            {isAnalyzing && (
              <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-sm text-orange-800">
                  <strong>Please don&apos;t navigate away</strong> while analysis is running.
                  You&apos;ll be redirected automatically when complete.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

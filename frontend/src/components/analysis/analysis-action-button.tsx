"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { analyzeSession, AnalysisTaskResponse } from "@/lib/services/sessions";

interface AnalysisActionButtonProps {
  sessionUid: string;
  status?: "PENDING" | "STARTED" | "COMPLETED" | "FAILED";
  isLoading?: boolean;
  className?: string;
}

export function AnalysisActionButton({ 
  sessionUid, 
  status, 
  isLoading = false,
  className = "" 
}: AnalysisActionButtonProps) {
  const queryClient = useQueryClient();

  const analysisMutation = useMutation<AnalysisTaskResponse, Error, void>({
    mutationFn: () => analyzeSession(sessionUid),
    onSuccess: (data) => {
      toast.success("Analysis Started", {
        description: `Session analysis has been queued successfully. Task ID: ${data.task_id}`,
      });
      
      // Invalidate all analysis-related queries to refresh data
      queryClient.invalidateQueries({
        queryKey: ["session", sessionUid],
        refetchType: 'all'
      });
      queryClient.invalidateQueries({
        queryKey: ["session-analysis", sessionUid],
        refetchType: 'all'
      });
      queryClient.invalidateQueries({
        queryKey: ["raw-transcript", sessionUid],
        refetchType: 'all'
      });
      queryClient.invalidateQueries({
        queryKey: ["bulk-analysis"],
        refetchType: 'all'
      });
      
      // Keep global analyzing state active if response status is STARTED
      // Only release the lock if the task failed to start
      if (data.status !== "STARTED") {
        // Analysis completed or failed to start
      }
      // If status is STARTED, the analysis continues in background via Celery
    },
    onError: (error) => {
      console.error("Analysis failed to start:", error);
      toast.error("Analysis Failed to Start", {
        description: "Failed to queue the session analysis. Please try again.",
      });
    },
  });

  const isAnalyzing = analysisMutation.isPending || isLoading;

  // Get button text based on status
  const getButtonText = () => {
    if (!status || status === "PENDING") return "Analyse";
    
    switch (status) {
      case "COMPLETED":
      case "FAILED":
        return "Re-analyse";
      case "STARTED":
        return "Analyse";
      default:
        return "Analyse";
    }
  };

  // Get status badge
  const getStatusBadge = () => {
    if (!status) return null;
    
    switch (status) {
      case "COMPLETED":
        return <Badge variant="default">Completed</Badge>;
      case "STARTED":
        return <Badge variant="secondary">Processing</Badge>;
      case "PENDING":
        return <Badge variant="outline">Pending</Badge>;
      case "FAILED":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center gap-2 text-sm font-medium">
        <BarChart3 className="h-4 w-4" />
        Session Analysis
      </div>
      
      {/* Analysis Status */}
      {status && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Status:</span>
          {getStatusBadge()}
        </div>
      )}
      
      <div className="flex items-center gap-3">
        <Button 
          onClick={() => analysisMutation.mutate()}
          disabled={isAnalyzing || status === "STARTED"}
          className="flex items-center gap-2"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Starting analysis...
            </>
          ) : (
            <>
              <BarChart3 className="h-4 w-4" />
              {getButtonText()}
            </>
          )}
        </Button>
        {isAnalyzing && (
          <span className="text-sm text-muted-foreground">
            Starting analysis...
          </span>
        )}
        {status === "STARTED" && !isAnalyzing && (
          <span className="text-sm text-muted-foreground">
            Analysis is currently in progress...
          </span>
        )}
      </div>
    </div>
  );
}

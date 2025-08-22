"use client";

import { useParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useSessionAnalysisWithPolling } from "@/lib/services/analysis";
import AnalysisDashboard from "@/components/analysis/analysis-dashboard";
import AnalysisEmptyState from "@/components/analysis/analysis-empty-state";
import { AnalysisActionButton } from "@/components/analysis/analysis-action-button";

export default function AnalysisTab() {
  const params = useParams();
  const sessionUid = params.uid as string;

  const {
    data: analysisData,
    isLoading,
    error,
    isError,
  } = useSessionAnalysisWithPolling(sessionUid, {
    pollingInterval: 2000, // Poll every 5 seconds when status is PENDING/STARTED
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Header Skeleton */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-6 w-64" />
                <Skeleton className="h-4 w-96" />
              </div>
              <Skeleton className="h-6 w-20" />
            </div>
          </CardHeader>
        </Card>

        {/* Metrics Grid Skeleton */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16 mb-1" />
                <Skeleton className="h-3 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Content Grid Skeleton */}
        <div className="grid gap-6 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Loading indicator */}
        <div className="text-center py-8">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Loading session analysis...</p>
        </div>
      </div>
    );
  }

  // Error state (404, empty, or other errors)
  if (isError || error || !analysisData) {
    return <AnalysisEmptyState sessionUid={sessionUid} source="session-details" />;
  }

  // Check if analysis status is not COMPLETED - show analysis action button
  if (analysisData.status && analysisData.status !== "COMPLETED") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5" />
            Session Analysis
          </CardTitle>
          <CardDescription>
            Analysis results will be available after processing is completed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AnalysisActionButton 
            sessionUid={sessionUid} 
            status={analysisData.status}
            className="pt-4 border-t"
          />
        </CardContent>
      </Card>
    );
  }

  // Success state - show the analysis dashboard
  return <AnalysisDashboard analysisData={analysisData} uid={sessionUid} />;
}

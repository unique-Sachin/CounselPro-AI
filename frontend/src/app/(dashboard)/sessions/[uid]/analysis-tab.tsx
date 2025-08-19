"use client";

import { useParams } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { AlertTriangle, BarChart3, Loader2 } from "lucide-react";
import { useSessionAnalysis } from "@/lib/services/analysis";
import AnalysisDashboard from "@/components/analysis/analysis-dashboard";

export default function AnalysisTab() {
  const params = useParams();
  const sessionUid = params.uid as string;

  const {
    data: analysisData,
    isLoading,
    error,
    isError,
  } = useSessionAnalysis(sessionUid, {
    staleTime: 30_000,
    retry: 1,
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

  // Error state
  if (isError || error) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {error instanceof Error 
              ? `Failed to load session analysis: ${error.message}`
              : "Failed to load session analysis. The analysis may not be available yet or there was an error processing the request."
            }
          </AlertDescription>
        </Alert>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground mb-2">Analysis Not Available</p>
              <p className="text-sm text-muted-foreground">
                This session has not been analyzed yet, or the analysis failed to complete.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No data state
  if (!analysisData) {
    return (
      <div className="space-y-6">
        <Alert>
          <BarChart3 className="h-4 w-4" />
          <AlertDescription>
            No analysis data is available for this session. The session may need to be analyzed first.
          </AlertDescription>
        </Alert>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground mb-2">No Analysis Data</p>
              <p className="text-sm text-muted-foreground">
                Please run an analysis on this session first to see the results here.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Success state - show the analysis dashboard
  return <AnalysisDashboard analysisData={analysisData} />;
}

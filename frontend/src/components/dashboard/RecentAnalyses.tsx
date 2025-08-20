"use client";

import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  FileText, 
  ExternalLink,
  Calendar,
  User,
  BarChart3
} from "lucide-react";
import { listSessions } from "@/lib/services/sessions";
import { getBulkSessionAnalyses } from "@/lib/services/analysis";
import { calcCompliance, countRedFlags } from "@/lib/analysis-utils";
import { BulkAnalysisItem } from "@/lib/types.analysis";

// Animation variants
const cardVariants = {
  hidden: { 
    opacity: 0, 
    y: 20 
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4
    }
  }
};

// Analysis data calculator (uses real data when available, mock when not)
const getAnalysisData = (analysis?: BulkAnalysisItem) => {
  if (analysis) {
    // Use real compliance and red flag calculations
    const compliance = calcCompliance(analysis);
    const redFlagCount = countRedFlags(analysis);
    
    // Derive quality score from compliance and other factors
    let qualityScore = compliance;
    
    // Adjust quality based on red flags
    if (redFlagCount > 0) {
      qualityScore = Math.max(qualityScore - (redFlagCount * 5), 0);
    }
    
    // Determine status based on backend status and analysis results
    let status: "Completed" | "Processing" | "Review Required" | "Pending";
    
    if (analysis.status) {
      // Use backend status as primary source
      switch (analysis.status) {
        case "COMPLETED":
          // Check if completed analysis needs review based on quality
          if (redFlagCount > 3 || compliance < 70) {
            status = "Review Required";
          } else {
            status = "Completed";
          }
          break;
        case "STARTED":
          status = "Processing";
          break;
        case "PENDING":
          status = "Pending";
          break;
        case "FAILED":
          status = "Review Required";
          break;
        default:
          status = "Completed";
      }
    } else {
      // Fallback logic when status is not provided
      if (redFlagCount > 3 || compliance < 70) {
        status = "Review Required";
      } else {
        status = "Completed";
      }
    }
    
    return {
      compliance,
      qualityScore: Math.min(qualityScore, 100),
      status,
      redFlagCount
    };
  } else {
    // When no analysis available, show "Pending" to indicate analysis is needed
    return {
      compliance: 0, // No compliance data available
      qualityScore: 0, // No quality score available
      status: "Pending" as const, // Indicate analysis is needed
      redFlagCount: 0 // No red flags data available
    };
  }
};

interface RecentAnalysesProps {
  limit?: number;
  sessionIds?: string[];
}

function SkeletonRow() {
  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <Skeleton className="h-4 w-20" />
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-muted-foreground" />
          <Skeleton className="h-4 w-24" />
        </div>
      </TableCell>
      <TableCell>
        <Skeleton className="h-5 w-12" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-5 w-12" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-5 w-16" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-8 w-16" />
      </TableCell>
    </TableRow>
  );
}

export function RecentAnalyses({ 
  limit = 5,
  sessionIds 
}: RecentAnalysesProps) {
  
  // Fetch sessions data
  const { 
    data: sessionsData, 
    isLoading: sessionsLoading, 
    error: sessionsError 
  } = useQuery({
    queryKey: ['recent-sessions', limit],
    queryFn: () => listSessions({ skip: 0, limit }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Use provided sessionIds or fallback to fetched sessions
  const sessions = sessionIds 
    ? sessionsData?.items?.filter(session => sessionIds.includes(session.uid)) || []
    : sessionsData?.items || [];

  // Get session UIDs for bulk analysis
  const sessionUids = sessions.map(session => session.uid);

  // Fetch bulk analysis data
  const { 
    data: analysesData, 
    isLoading: analysesLoading
  } = useQuery({
    queryKey: ['bulk-analyses', sessionUids],
    queryFn: () => getBulkSessionAnalyses(sessionUids),
    enabled: sessionUids.length > 0, // Only fetch if we have session UIDs
    refetchInterval: 60000, // Refetch every minute
  });

  // Create a map of session UID to analysis for quick lookup
  const analysisMap = new Map<string, BulkAnalysisItem>();
  analysesData?.analyses?.forEach(analysis => {
    analysisMap.set(analysis.session_uid, analysis);
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Completed":
        return <Badge variant="default">Completed</Badge>;
      case "Processing":
        return <Badge variant="secondary">Processing</Badge>;
      case "Pending":
        return <Badge variant="outline">Pending</Badge>;
      case "Review Required":
        return <Badge variant="outline">Review Required</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getComplianceBadge = (score: number) => {
    if (score === 0) return <Badge variant="outline">Pending</Badge>;
    if (score >= 95) return <Badge variant="default">{score}%</Badge>;
    if (score >= 85) return <Badge variant="secondary">{score}%</Badge>;
    return <Badge variant="destructive">{score}%</Badge>;
  };

  const getQualityBadge = (score: number) => {
    if (score === 0) return <Badge variant="outline">Pending</Badge>;
    if (score >= 90) return <Badge variant="default">{score}%</Badge>;
    if (score >= 80) return <Badge variant="secondary">{score}%</Badge>;
    return <Badge variant="outline">{score}%</Badge>;
  };

  return (
    <motion.div 
      variants={cardVariants}
      initial="hidden"
      animate="visible"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Recent Analyses
          </CardTitle>
          <CardDescription>
            Latest session analysis results and quality assessments
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sessionsError ? (
            <div className="flex items-center justify-center py-8 text-center">
              <div className="space-y-2">
                <BarChart3 className="h-12 w-12 text-muted-foreground/50 mx-auto" />
                <p className="text-sm text-muted-foreground">
                  Failed to load session data
                </p>
                <p className="text-xs text-muted-foreground">
                  {sessionsError.toString()}
                </p>
              </div>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Session Date
                      </div>
                    </TableHead>
                    <TableHead>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        Counselor
                      </div>
                    </TableHead>
                    <TableHead className="w-[100px]">Compliance</TableHead>
                    <TableHead className="w-[100px]">Quality Score</TableHead>
                    <TableHead className="w-[120px]">Status</TableHead>
                    <TableHead className="w-[80px]">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(sessionsLoading || analysesLoading) ? (
                    // Show skeleton rows while loading
                    Array.from({ length: limit }).map((_, index) => (
                      <SkeletonRow key={index} />
                    ))
                  ) : sessions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        <div className="space-y-2">
                          <BarChart3 className="h-8 w-8 text-muted-foreground/50 mx-auto" />
                          <p className="text-sm text-muted-foreground">
                            No recent analyses found
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    sessions.map((session) => {
                      // Get analysis data (real if available, mock if not)
                      const analysis = analysisMap.get(session.uid);
                      const analysisData = getAnalysisData(analysis);
                      
                      return (
                        <TableRow key={session.uid}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">
                                {formatDate(session.session_date)}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <User className="h-4 w-4 text-muted-foreground" />
                              <span className="font-medium">
                                {session.counselor.name}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {getComplianceBadge(analysisData.compliance)}
                          </TableCell>
                          <TableCell>
                            {getQualityBadge(analysisData.qualityScore)}
                          </TableCell>
                          <TableCell>
                            {getStatusBadge(analysisData.status)}
                          </TableCell>
                          <TableCell>
                            <Button asChild variant="ghost" size="sm">
                              <Link href={`/sessions/${session.uid}`}>
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Link>
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RecentAnalyses;

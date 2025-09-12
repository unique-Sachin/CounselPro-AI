"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  BarChart3,
  RefreshCw
} from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { SessionAnalysisResponse } from "@/lib/types.analysis";
import CourseAccuracyCard from "./course-accuracy-card";
import PaymentVerificationCard from "./PaymentVerificationCard";
import PressureAnalysisCard from "./PressureAnalysisCard";
import OneOnOneCard from "./OneOnOneCard";
import ParticipantsGrid from "./participants-grid";
import EnvironmentCard from "./environment-card";
import SessionTimeline from "./session-timeline";
import TechnicalInfo from "./technical-info";
import SessionMetadataCard from "./session-metadata";

interface AnalysisDashboardProps {
  analysisData: SessionAnalysisResponse;
  uid: string;
}

export default function AnalysisDashboard({ analysisData, uid }: AnalysisDashboardProps) {
  // Extract the specific data structure from the response
  const videoAnalysis = analysisData.video_analysis_data;
  const audioAnalysis = analysisData.audio_analysis_data;
  
  // Query client for invalidating queries
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Handle refresh functionality
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await queryClient.invalidateQueries({
        queryKey: ['session-analysis', uid]
      });
      // Wait a bit for the query to complete
      setTimeout(() => setIsRefreshing(false), 1000);
    } catch (error) {
      console.error('Error refreshing analysis:', error);
      setIsRefreshing(false);
    }
  };

  // Format the updated_at timestamp
  const formatLastUpdated = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';
    try {
      return format(new Date(timestamp), 'MMM dd, yyyy \'at\' h:mm a');
    } catch {
      return 'Invalid date';
    }
  };
  
  // Animation variants for cards
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Analysis Header */}
      <motion.div variants={cardVariants}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Session Analysis Results
                </CardTitle>
                <CardDescription>
                  Comprehensive analysis of video engagement and course accuracy
                </CardDescription>
                {analysisData.updated_at && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Last updated: {formatLastUpdated(analysisData.updated_at)}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </Button>
                <Badge variant="default">
                  COMPLETED
                </Badge>
              </div>
            </div>
          </CardHeader>
        </Card>
      </motion.div>

      {/* Analysis Cards Grid */}
      <motion.div 
        variants={containerVariants}
        className="grid gap-6 lg:grid-cols-2"
      >
        {/* Course Accuracy Card */}
        <motion.div variants={cardVariants} className="min-w-0">
          <CourseAccuracyCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* Payment Verification Card */}
        <motion.div variants={cardVariants} className="min-w-0">
          <PaymentVerificationCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* Pressure Analysis Card */}
        <motion.div variants={cardVariants} className="min-w-0">
          <PressureAnalysisCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* One-on-One Verification Card */}
        <motion.div variants={cardVariants} className="min-w-0">
          <OneOnOneCard videoAnalysisData={videoAnalysis} />
        </motion.div>
      </motion.div>

      {/* Session Metadata */}
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="mt-6"
      >
        <SessionMetadataCard audioAnalysisData={audioAnalysis} />
      </motion.div>

      {/* Participants Grid */}
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="mt-8"
      >
        <ParticipantsGrid videoAnalysisData={videoAnalysis} />
      </motion.div>

      {/* Environment Card */}
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="mt-6"
      >
        <EnvironmentCard videoAnalysisData={videoAnalysis} />
      </motion.div>

      {/* Session Timeline */}
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="mt-6"
      >
        <SessionTimeline videoAnalysisData={videoAnalysis} />
      </motion.div>

      {/* Technical Information */}
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        className="mt-6"
      >
        <TechnicalInfo videoAnalysisData={videoAnalysis} />
      </motion.div>
    </motion.div>
  );
}

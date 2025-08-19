"use client";

import { motion } from "framer-motion";
import { 
  BarChart3,
  Camera
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { SessionAnalysisResponse } from "@/lib/types.analysis";
import CourseAccuracyCard from "./course-accuracy-card";
import PaymentVerificationCard from "./PaymentVerificationCard";
import PressureAnalysisCard from "./PressureAnalysisCard";
import OneOnOneCard from "./OneOnOneCard";
import ParticipantsGrid from "./participants-grid";

interface AnalysisDashboardProps {
  analysisData: SessionAnalysisResponse;
}

export default function AnalysisDashboard({ analysisData }: AnalysisDashboardProps) {
  // Extract the specific data structure from the response
  const videoAnalysis = analysisData.video_analysis_data;
  const audioAnalysis = analysisData.audio_analysis_data;
  
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
              </div>
              <Badge variant="default">
                COMPLETED
              </Badge>
            </div>
          </CardHeader>
        </Card>
      </motion.div>

      {/* Analysis Cards Grid */}
      <motion.div 
        variants={containerVariants}
        className="grid gap-6 md:grid-cols-2"
      >
        {/* Course Accuracy Card */}
        <motion.div variants={cardVariants}>
          <CourseAccuracyCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* Payment Verification Card */}
        <motion.div variants={cardVariants}>
          <PaymentVerificationCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* Pressure Analysis Card */}
        <motion.div variants={cardVariants}>
          <PressureAnalysisCard audioAnalysisData={audioAnalysis} />
        </motion.div>

        {/* One-on-One Verification Card */}
        <motion.div variants={cardVariants}>
          <OneOnOneCard videoAnalysisData={videoAnalysis} />
        </motion.div>
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

      {/* Additional Analysis Details */}
      {(videoAnalysis?.environment_analysis || videoAnalysis?.technical_info) && (
        <motion.div variants={cardVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5" />
                Environment & Technical Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {/* Environment Analysis */}
                {videoAnalysis.environment_analysis && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Environment Assessment</h4>
                    
                    {videoAnalysis.environment_analysis.attire_assessment && (
                      <div className="space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-medium">Attire Rating</span>
                          <span className="text-xs">{videoAnalysis.environment_analysis.attire_assessment.overall_rating}%</span>
                        </div>
                        <Progress value={videoAnalysis.environment_analysis.attire_assessment.overall_rating} className="h-1.5" />
                        <p className="text-xs text-muted-foreground">
                          {videoAnalysis.environment_analysis.attire_assessment.description}
                        </p>
                      </div>
                    )}

                    {videoAnalysis.environment_analysis.background_assessment && (
                      <div className="space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-medium">Background Rating</span>
                          <span className="text-xs">{videoAnalysis.environment_analysis.background_assessment.overall_rating}%</span>
                        </div>
                        <Progress value={videoAnalysis.environment_analysis.background_assessment.overall_rating} className="h-1.5" />
                        <p className="text-xs text-muted-foreground">
                          {videoAnalysis.environment_analysis.background_assessment.description}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Technical Info */}
                {videoAnalysis.technical_info && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Technical Details</h4>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span>Analysis Method:</span>
                        <span className="font-mono">{videoAnalysis.technical_info.analysis_method}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Frames Analyzed:</span>
                        <span className="font-mono">{videoAnalysis.technical_info.total_frames_analyzed}</span>
                      </div>
                      {videoAnalysis.technical_info.analysis_timestamp && (
                        <div className="flex justify-between">
                          <span>Processed:</span>
                          <span className="font-mono">
                            {new Date(videoAnalysis.technical_info.analysis_timestamp).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

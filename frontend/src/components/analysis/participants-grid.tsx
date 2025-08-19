"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { User, Camera, Clock, AlertTriangle, CheckCircle } from "lucide-react";
import { VideoAnalysisData } from "@/lib/types.analysis";

interface ParticipantsGridProps {
  videoAnalysisData?: VideoAnalysisData;
}

export default function ParticipantsGrid({ videoAnalysisData }: ParticipantsGridProps) {
  // Early return if no video analysis data or participants
  if (!videoAnalysisData?.participants || Object.keys(videoAnalysisData.participants).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Participant Analysis
          </CardTitle>
          <CardDescription>
            Individual participant engagement and behavior analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">No participant data available</p>
            <p className="text-xs text-muted-foreground">
              Participant analysis will appear here once video analysis is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const participants = videoAnalysisData.participants;
  const participantEntries = Object.entries(participants);

  // Animation variants for staggered entry
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3,
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Section Header */}
      <div className="flex items-center gap-2">
        <User className="h-5 w-5" />
        <h3 className="text-lg font-semibold">Participant Analysis</h3>
        <Badge variant="outline" className="ml-auto">
          {participantEntries.length} Participants
        </Badge>
      </div>

      {/* Participants Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        {participantEntries.map(([participantKey, participant]) => (
          <motion.div key={participantKey} variants={cardVariants}>
            <Card className="h-full">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm font-medium">
                  <User className="h-4 w-4" />
                  {participantKey.replace('_', ' ').toUpperCase()}
                  {participant.participant_id && (
                    <Badge variant="outline" className="text-xs">
                      ID: {participant.participant_id}
                    </Badge>
                  )}
                </CardTitle>
                {participant.engagement_summary?.overall_status && (
                  <CardDescription className="text-xs">
                    Status: {participant.engagement_summary.overall_status}
                  </CardDescription>
                )}
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Camera Engagement */}
                {participant.engagement_summary && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <Camera className="h-3 w-3" />
                      Camera Engagement
                    </div>
                    
                    {/* Camera On Percentage */}
                    {participant.engagement_summary.camera_on_percentage !== undefined && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>Camera On</span>
                          <span className="font-medium">
                            {participant.engagement_summary.camera_on_percentage}%
                          </span>
                        </div>
                        <Progress 
                          value={participant.engagement_summary.camera_on_percentage} 
                          className="h-1.5"
                        />
                      </div>
                    )}

                    {/* Active Camera Percentage */}
                    {participant.engagement_summary.active_camera_percentage !== undefined && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>Active Camera</span>
                          <span className="font-medium">
                            {participant.engagement_summary.active_camera_percentage}%
                          </span>
                        </div>
                        <Progress 
                          value={participant.engagement_summary.active_camera_percentage} 
                          className="h-1.5"
                        />
                      </div>
                    )}

                    {/* Static Image Usage */}
                    {participant.engagement_summary.using_static_image && (
                      <div className="flex items-center gap-2 text-xs text-orange-600">
                        <AlertTriangle className="h-3 w-3" />
                        Using static image ({participant.engagement_summary.static_image_percentage}%)
                      </div>
                    )}
                  </div>
                )}

                {/* Session Periods */}
                {participant.session_periods && (
                  <div className="space-y-2 pt-2 border-t">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      Session Activity
                    </div>
                    
                    {/* Longest Continuous On */}
                    {participant.session_periods.longest_continuous_on && (
                      <div className="flex justify-between text-xs">
                        <span>Longest On:</span>
                        <span className="font-medium text-green-600">
                          {participant.session_periods.longest_continuous_on.duration_formatted}
                        </span>
                      </div>
                    )}

                    {/* Longest Continuous Off */}
                    {participant.session_periods.longest_continuous_off && (
                      <div className="flex justify-between text-xs">
                        <span>Longest Off:</span>
                        <span className="font-medium text-red-600">
                          {participant.session_periods.longest_continuous_off.duration_formatted}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Notable Issues */}
                <div className="space-y-2 pt-2 border-t">
                  <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <AlertTriangle className="h-3 w-3" />
                    Notable Issues
                  </div>
                  
                  {participant.behavior_insights?.notable_issues && 
                   participant.behavior_insights.notable_issues.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {participant.behavior_insights.notable_issues.slice(0, 3).map((issue, index) => (
                        <Badge 
                          key={index} 
                          variant="destructive" 
                          className="text-xs px-2 py-0.5"
                        >
                          {issue}
                        </Badge>
                      ))}
                      {participant.behavior_insights.notable_issues.length > 3 && (
                        <Badge variant="outline" className="text-xs px-2 py-0.5">
                          +{participant.behavior_insights.notable_issues.length - 3} more
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-xs text-green-600">
                      <CheckCircle className="h-3 w-3" />
                      <span>None</span>
                    </div>
                  )}
                </div>

                {/* Consistency Score */}
                {participant.behavior_insights?.consistency_score !== undefined && (
                  <div className="space-y-1 pt-2 border-t">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Consistency Score</span>
                      <span className="font-medium">
                        {Math.round(participant.behavior_insights.consistency_score * 100)}%
                      </span>
                    </div>
                    <Progress 
                      value={participant.behavior_insights.consistency_score * 100} 
                      className="h-1.5"
                    />
                  </div>
                )}

                {/* Engagement Pattern */}
                {participant.behavior_insights?.engagement_pattern && (
                  <div className="pt-2 border-t">
                    <div className="text-xs text-muted-foreground mb-1">Pattern:</div>
                    <Badge variant="outline" className="text-xs">
                      {participant.behavior_insights.engagement_pattern}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

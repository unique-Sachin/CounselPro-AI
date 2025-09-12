"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CourseInfo } from "@/lib/types.analysis";

interface AudioAnalysisData {
  accuracy_score?: number;
  courses_mentioned?: CourseInfo[];
  overall_summary?: string;
}

interface CourseAccuracyCardProps {
  audioAnalysisData?: AudioAnalysisData;
}

export default function CourseAccuracyCard({ audioAnalysisData }: CourseAccuracyCardProps) {
  // If no audio analysis data, show pending state
  if (!audioAnalysisData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5" />
            Course Accuracy
          </CardTitle>
          <CardDescription>
            Analysis of adherence to counseling protocols
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <BarChart3 className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Analysis Pending</p>
            <p className="text-xs text-muted-foreground">
              Course accuracy results will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Extract data with defaults
  const accuracyScore = audioAnalysisData.accuracy_score ?? 0;
  const coursesMentioned = audioAnalysisData.courses_mentioned ?? [];
  const overallSummary = audioAnalysisData.overall_summary ?? "";

  // Calculate percentage
  const accuracyPercentage = Math.round(accuracyScore * 100);

  return (
    <Card className="h-fit">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="h-5 w-5" />
          Course Accuracy
        </CardTitle>
        <CardDescription>
          Analysis of adherence to counseling protocols
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          {/* Big Accuracy Percentage */}
          <div className="text-center">
            <div className="text-4xl font-bold text-primary mb-2">
              {accuracyPercentage}%
            </div>
            <Badge 
              variant={accuracyPercentage >= 80 ? "default" : accuracyPercentage >= 60 ? "secondary" : "destructive"}
              className="mb-3"
            >
              {accuracyPercentage >= 80 ? "Excellent" : accuracyPercentage >= 60 ? "Good" : "Needs Improvement"}
            </Badge>
            <Progress value={accuracyPercentage} className="h-2 mb-4" />
          </div>

          {/* Courses Mentioned */}
          <div className="space-y-2">
            <span className="text-sm font-medium">Courses Mentioned</span>
            {coursesMentioned.length > 0 ? (
              <div className="space-y-2">
                {coursesMentioned.map((course: CourseInfo, index: number) => (
                  <div key={index} className="p-2 rounded-md bg-muted/50 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary" className="text-xs max-w-full break-words">
                        <span className="truncate max-w-[200px]" title={course.name}>
                          {course.name}
                        </span>
                      </Badge>
                      {course.match_status && (
                        <Badge 
                          variant={course.match_status === "MATCH" ? "default" : "destructive"} 
                          className="text-xs"
                        >
                          {course.match_status}
                        </Badge>
                      )}
                    </div>
                    {course.confidence_score && (
                      <div className="text-xs text-muted-foreground">
                        {Math.round(course.confidence_score * 100)}% confidence
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  No courses mentioned
                </Badge>
              </div>
            )}
          </div>

          {/* Overall Summary */}
          {overallSummary && (
            <div className="space-y-2 pt-2 border-t">
              <span className="text-sm font-medium">Analysis Summary</span>
              <div className="text-sm text-muted-foreground leading-relaxed max-h-32 overflow-y-auto">
                <p className="break-words">
                  {overallSummary}
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

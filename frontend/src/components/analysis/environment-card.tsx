"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Eye, Shirt, Home, CheckCircle, XCircle, Clock } from "lucide-react";
import { VideoAnalysisData } from "@/lib/types.analysis";

interface EnvironmentCardProps {
  videoAnalysisData?: VideoAnalysisData;
}

export default function EnvironmentCard({ videoAnalysisData }: EnvironmentCardProps) {
  // Handle missing video analysis data or environment analysis
  if (!videoAnalysisData?.environment_analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Eye className="h-5 w-5 text-muted-foreground" />
            Environment Analysis
          </CardTitle>
          <CardDescription>
            Professional appearance and background assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Environment analysis pending</p>
            <p className="text-xs text-muted-foreground">
              Professional environment assessment will appear here once analysis is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { attire_assessment, background_assessment } = videoAnalysisData.environment_analysis;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Eye className="h-5 w-5" />
          Environment Analysis
        </CardTitle>
        <CardDescription>
          Professional appearance and background assessment
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Attire Assessment */}
        {attire_assessment && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Shirt className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium">Attire Assessment</h4>
              <Badge 
                variant={attire_assessment.meets_professional_standards ? "default" : "destructive"}
                className={attire_assessment.meets_professional_standards 
                  ? "bg-green-100 text-green-800 border-green-200" 
                  : ""
                }
              >
                {attire_assessment.meets_professional_standards ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Professional
                  </>
                ) : (
                  <>
                    <XCircle className="h-3 w-3 mr-1" />
                    Non-Professional
                  </>
                )}
              </Badge>
            </div>

            {/* Attire Rating */}
            {attire_assessment.overall_rating !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Overall Rating</span>
                  <span className="font-medium">
                    {attire_assessment.overall_rating}/100
                  </span>
                </div>
                <Progress 
                  value={attire_assessment.overall_rating} 
                  className="h-2"
                />
              </div>
            )}

            {/* Attire Description */}
            {attire_assessment.description && (
              <div className="space-y-2">
                <span className="text-sm font-medium text-muted-foreground">Assessment</span>
                <p className="text-sm bg-muted p-3 rounded-md">
                  {attire_assessment.description}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Background Assessment */}
        {background_assessment && (
          <div className="space-y-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <Home className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium">Background Assessment</h4>
              <Badge 
                variant={background_assessment.meets_professional_standards ? "default" : "destructive"}
                className={background_assessment.meets_professional_standards 
                  ? "bg-green-100 text-green-800 border-green-200" 
                  : ""
                }
              >
                {background_assessment.meets_professional_standards ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Professional
                  </>
                ) : (
                  <>
                    <XCircle className="h-3 w-3 mr-1" />
                    Non-Professional
                  </>
                )}
              </Badge>
            </div>

            {/* Background Rating */}
            {background_assessment.overall_rating !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Overall Rating</span>
                  <span className="font-medium">
                    {background_assessment.overall_rating}/100
                  </span>
                </div>
                <Progress 
                  value={background_assessment.overall_rating} 
                  className="h-2"
                />
              </div>
            )}

            {/* Background Description */}
            {background_assessment.description && (
              <div className="space-y-2">
                <span className="text-sm font-medium text-muted-foreground">Assessment</span>
                <p className="text-sm bg-muted p-3 rounded-md">
                  {background_assessment.description}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Summary Section */}
        {(attire_assessment?.meets_professional_standards !== undefined || 
          background_assessment?.meets_professional_standards !== undefined) && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">Overall Environment</span>
              <Badge 
                variant={
                  (attire_assessment?.meets_professional_standards ?? true) && 
                  (background_assessment?.meets_professional_standards ?? true) 
                    ? "default" 
                    : "secondary"
                }
                className={
                  (attire_assessment?.meets_professional_standards ?? true) && 
                  (background_assessment?.meets_professional_standards ?? true)
                    ? "bg-green-100 text-green-800 border-green-200"
                    : "bg-orange-100 text-orange-800 border-orange-200"
                }
              >
                {(attire_assessment?.meets_professional_standards ?? true) && 
                 (background_assessment?.meets_professional_standards ?? true) ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Fully Professional
                  </>
                ) : (
                  <>
                    <XCircle className="h-3 w-3 mr-1" />
                    Needs Improvement
                  </>
                )}
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

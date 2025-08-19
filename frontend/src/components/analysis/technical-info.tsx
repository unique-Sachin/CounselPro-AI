"use client";

import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Settings, Calendar, BarChart3, Clock } from "lucide-react";
import { VideoAnalysisData } from "@/lib/types.analysis";

interface TechnicalInfoProps {
  videoAnalysisData?: VideoAnalysisData;
}

export default function TechnicalInfo({ videoAnalysisData }: TechnicalInfoProps) {
  // Handle missing video analysis data or technical info
  if (!videoAnalysisData?.technical_info) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Settings className="h-5 w-5 text-muted-foreground" />
            Technical Information
          </CardTitle>
          <CardDescription>
            Analysis processing details and technical metadata
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Technical info pending</p>
            <p className="text-xs text-muted-foreground">
              Technical analysis details will appear here once processing is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { analysis_method, total_frames_analyzed, analysis_timestamp } = videoAnalysisData.technical_info;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Settings className="h-5 w-5" />
          Technical Information
        </CardTitle>
        <CardDescription>
          Analysis processing details and technical metadata
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="technical-details">
            <AccordionTrigger className="text-left">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span>Analysis Processing Details</span>
                <Badge variant="outline" className="ml-2">
                  Technical Data
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4 pt-4">
                {/* Analysis Method */}
                {analysis_method && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Analysis Method</span>
                    </div>
                    <div className="bg-muted p-3 rounded-md">
                      <p className="text-sm font-mono">
                        {analysis_method}
                      </p>
                    </div>
                  </div>
                )}

                {/* Total Frames Analyzed */}
                {total_frames_analyzed !== undefined && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Frames Processed</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                      <span className="text-sm text-muted-foreground">Total frames analyzed:</span>
                      <Badge variant="secondary" className="font-mono">
                        {total_frames_analyzed.toLocaleString()}
                      </Badge>
                    </div>
                  </div>
                )}

                {/* Analysis Timestamp */}
                {analysis_timestamp && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Processing Timestamp</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                        <span className="text-sm text-muted-foreground">Processed at:</span>
                        <span className="text-sm font-mono">
                          {new Date(analysis_timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded-md">
                        <span className="text-xs text-blue-700">Relative time:</span>
                        <span className="text-xs font-medium text-blue-800">
                          {getRelativeTime(analysis_timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Processing Summary */}
                <div className="pt-4 border-t">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Settings className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">
                        Processing Summary
                      </span>
                    </div>
                    <div className="space-y-1 text-xs text-green-700">
                      {analysis_method && (
                        <p>• Method: {analysis_method}</p>
                      )}
                      {total_frames_analyzed && (
                        <p>• Analyzed {total_frames_analyzed.toLocaleString()} video frames</p>
                      )}
                      {analysis_timestamp && (
                        <p>• Completed {getRelativeTime(analysis_timestamp)}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}

// Helper function to get relative time
function getRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  } catch {
    return 'unknown time';
  }
}

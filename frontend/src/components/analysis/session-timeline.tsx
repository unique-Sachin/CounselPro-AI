"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, Activity, PauseCircle, PlayCircle } from "lucide-react";
import { VideoAnalysisData } from "@/lib/types.analysis";

interface SessionTimelineProps {
  videoAnalysisData?: VideoAnalysisData;
}

export default function SessionTimeline({ videoAnalysisData }: SessionTimelineProps) {
  // Handle missing video analysis data or session patterns
  if (!videoAnalysisData?.session_patterns) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Activity className="h-5 w-5 text-muted-foreground" />
            Session Timeline
          </CardTitle>
          <CardDescription>
            Engagement timeline and activity patterns during the session
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Timeline data pending</p>
            <p className="text-xs text-muted-foreground">
              Session timeline will appear here once analysis is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { engagement_timeline, collective_off_periods } = videoAnalysisData.session_patterns;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Activity className="h-5 w-5" />
          Session Timeline
        </CardTitle>
        <CardDescription>
          Engagement timeline and activity patterns during the session
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Engagement Timeline */}
        {engagement_timeline && engagement_timeline.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <PlayCircle className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium">Engagement Timeline</h4>
              <Badge variant="outline" className="ml-auto">
                {engagement_timeline.length} Periods
              </Badge>
            </div>
            
            <div className="space-y-2">
              {engagement_timeline.map((period, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm font-mono">
                        {period.period || 'Unknown period'}
                      </span>
                    </div>
                    {period.duration && (
                      <span className="text-xs text-muted-foreground">
                        ({period.duration})
                      </span>
                    )}
                  </div>
                  
                  <Badge 
                    variant={period.status === 'on' ? 'default' : 'secondary'}
                    className={
                      period.status === 'on' 
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : period.status === 'off'
                        ? 'bg-red-100 text-red-800 border-red-200' 
                        : ''
                    }
                  >
                    {period.status === 'on' && <PlayCircle className="h-3 w-3 mr-1" />}
                    {period.status === 'off' && <PauseCircle className="h-3 w-3 mr-1" />}
                    {period.status?.toUpperCase() || 'Unknown'}
                  </Badge>
                </div>
              ))}
            </div>

            {/* Simple Timeline Bar */}
            <div className="mt-4">
              <div className="text-xs text-muted-foreground mb-2">Visual Timeline</div>
              <div className="flex rounded-lg overflow-hidden border h-6">
                {engagement_timeline.map((period, index) => {
                  // Simple equal width segments for visual representation
                  const width = `${100 / engagement_timeline.length}%`;
                  return (
                    <div
                      key={index}
                      className={`flex items-center justify-center text-xs font-medium transition-colors ${
                        period.status === 'on'
                          ? 'bg-green-200 text-green-800'
                          : period.status === 'off'
                          ? 'bg-red-200 text-red-800'
                          : 'bg-gray-200 text-gray-800'
                      }`}
                      style={{ width }}
                      title={`${period.period} - ${period.status} ${period.duration ? `(${period.duration})` : ''}`}
                    >
                      {period.status === 'on' ? '●' : '○'}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Collective Off Periods */}
        {collective_off_periods && collective_off_periods.length > 0 && (
          <div className="space-y-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <PauseCircle className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium">Collective Off Periods</h4>
              <Badge variant="outline" className="ml-auto">
                {collective_off_periods.length} Periods
              </Badge>
            </div>
            
            <div className="space-y-2">
              {collective_off_periods.map((period, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg border bg-red-50 border-red-200"
                >
                  <div className="flex items-center gap-3">
                    <PauseCircle className="h-4 w-4 text-red-600" />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono">
                        {period.start} – {period.end}
                      </span>
                      {period.duration_formatted && (
                        <span className="text-xs text-muted-foreground">
                          ({period.duration_formatted})
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <Badge variant="destructive" className="text-xs">
                    All Off
                  </Badge>
                </div>
              ))}
            </div>
            
            {collective_off_periods.length > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mt-3">
                <div className="flex items-center gap-2 text-orange-700">
                  <PauseCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    {collective_off_periods.length} period{collective_off_periods.length > 1 ? 's' : ''} 
                    where all participants were off camera
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* No Data Message */}
        {(!engagement_timeline || engagement_timeline.length === 0) && 
         (!collective_off_periods || collective_off_periods.length === 0) && (
          <div className="text-center py-6">
            <div className="w-12 h-12 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
              <Activity className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">
              No timeline data available for this session
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

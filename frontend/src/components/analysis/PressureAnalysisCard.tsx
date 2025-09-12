"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ShieldCheck, Clock, AlertCircle } from "lucide-react";
import { AudioAnalysisData } from "@/lib/types.analysis";
import { filterPressureFlags, getPressureSeverity } from "@/lib/analysis-utils";

interface PressureAnalysisCardProps {
  audioAnalysisData?: AudioAnalysisData;
}

export default function PressureAnalysisCard({ audioAnalysisData }: PressureAnalysisCardProps) {
  // Handle missing audio analysis data
  if (!audioAnalysisData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="h-5 w-5 text-muted-foreground" />
            Pressure Analysis
          </CardTitle>
          <CardDescription>
            Detection of high-pressure sales tactics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Analysis Pending</p>
            <p className="text-xs text-muted-foreground">
              Pressure analysis will appear here once audio analysis is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle undefined red_flags
  if (!audioAnalysisData.red_flags) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="h-5 w-5 text-muted-foreground" />
            Pressure Analysis
          </CardTitle>
          <CardDescription>
            Detection of high-pressure sales tactics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Analysis Pending</p>
            <p className="text-xs text-muted-foreground">
              Pressure analysis results will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const pressureFlags = filterPressureFlags(audioAnalysisData.red_flags);
  const severity = getPressureSeverity(pressureFlags);

  // No pressure tactics detected
  if (pressureFlags.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <ShieldCheck className="h-5 w-5 text-green-600" />
            Pressure Analysis
          </CardTitle>
          <CardDescription>
            Detection of high-pressure sales tactics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-green-50 rounded-full flex items-center justify-center">
              <ShieldCheck className="h-8 w-8 text-green-600" />
            </div>
            <p className="text-green-700 font-medium mb-2">No pressure tactics detected</p>
            <p className="text-xs text-muted-foreground">
              The conversation appears to be conducted without high-pressure sales techniques
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Pressure tactics detected
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "Low": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "Medium": return "bg-orange-100 text-orange-800 border-orange-200";
      case "High": return "bg-red-100 text-red-800 border-red-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "Low": return <AlertCircle className="h-4 w-4" />;
      case "Medium": return <AlertTriangle className="h-4 w-4" />;
      case "High": return <AlertTriangle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  // Show top 3 examples
  const topExamples = pressureFlags.slice(0, 3);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <AlertTriangle className="h-5 w-5 text-orange-600" />
          Pressure Analysis
        </CardTitle>
        <CardDescription>
          Detection of high-pressure sales tactics
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Severity Indicator */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Severity Level</span>
          <Badge 
            variant="outline" 
            className={getSeverityColor(severity)}
          >
            {getSeverityIcon(severity)}
            <span className="ml-1">{severity}</span>
          </Badge>
        </div>

        {/* Pressure Count */}
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-sm font-medium text-muted-foreground">Issues Detected</span>
          <span className="text-2xl font-bold text-orange-600">
            {pressureFlags.length}
          </span>
        </div>

        {/* Top Examples */}
        {topExamples.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <span className="text-sm font-medium text-muted-foreground">
              Top Examples:
            </span>
            <div className="space-y-2">
              {topExamples.map((flag, index) => (
                <div key={index} className="text-sm p-2 bg-orange-50 rounded border-l-2 border-orange-200">
                  {typeof flag === 'string' 
                    ? flag 
                    : (flag.description || flag.message || flag.type || 'Pressure tactic detected')
                  }
                </div>
              ))}
              {pressureFlags.length > 3 && (
                <p className="text-xs text-muted-foreground">
                  +{pressureFlags.length - 3} more pressure tactics detected
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { UserCheck, Users, Info, Clock } from "lucide-react";
import { VideoAnalysisData } from "@/lib/types.analysis";

interface OneOnOneCardProps {
  videoAnalysisData?: VideoAnalysisData;
}

export default function OneOnOneCard({ videoAnalysisData }: OneOnOneCardProps) {
  // Handle missing video analysis data
  if (!videoAnalysisData || !videoAnalysisData.session_overview) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="h-5 w-5 text-muted-foreground" />
            One-on-One Verification
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Value derived from video participant tracking.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardTitle>
          <CardDescription>
            Verification of proper counselor-client interaction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Verification Pending</p>
            <p className="text-xs text-muted-foreground">
              One-on-one verification will appear here once video analysis is complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalParticipants = videoAnalysisData.session_overview.total_participants;

  // Handle missing total_participants
  if (totalParticipants === undefined || totalParticipants === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="h-5 w-5 text-muted-foreground" />
            One-on-One Verification
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Value derived from video participant tracking.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardTitle>
          <CardDescription>
            Verification of proper counselor-client interaction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Verification Pending</p>
            <p className="text-xs text-muted-foreground">
              Participant tracking data is not available yet
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Determine verification status
  const isOneOnOne = totalParticipants === 2;
  const statusText = isOneOnOne 
    ? "Verified one-on-one" 
    : `Not one-on-one (${totalParticipants} participants)`;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {isOneOnOne ? (
            <UserCheck className="h-5 w-5 text-green-600" />
          ) : (
            <Users className="h-5 w-5 text-red-600" />
          )}
          One-on-One Verification
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Value derived from video participant tracking.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
        <CardDescription>
          Verification of proper counselor-client interaction
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Badge */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Verification Status</span>
          <Badge 
            variant={isOneOnOne ? "default" : "destructive"}
            className={isOneOnOne ? "bg-green-100 text-green-800 border-green-200" : ""}
          >
            {isOneOnOne ? (
              <UserCheck className="h-3 w-3 mr-1" />
            ) : (
              <Users className="h-3 w-3 mr-1" />
            )}
            {isOneOnOne ? "Verified" : "Not Verified"}
          </Badge>
        </div>

        {/* Participant Count */}
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-sm font-medium text-muted-foreground">Total Participants</span>
          <span className={`text-2xl font-bold ${isOneOnOne ? 'text-green-600' : 'text-red-600'}`}>
            {totalParticipants}
          </span>
        </div>

        {/* Status Message */}
        <div className="pt-2 border-t">
          <div className={`text-center py-4 rounded-lg ${
            isOneOnOne 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
              isOneOnOne ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {isOneOnOne ? (
                <UserCheck className="h-6 w-6 text-green-600" />
              ) : (
                <Users className="h-6 w-6 text-red-600" />
              )}
            </div>
            <p className={`font-medium ${isOneOnOne ? 'text-green-700' : 'text-red-700'}`}>
              {statusText}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {isOneOnOne 
                ? "Session follows proper one-on-one counseling protocol"
                : "Session includes additional participants beyond counselor and client"
              }
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

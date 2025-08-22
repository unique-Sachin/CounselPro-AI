"use client";

import { Info, MessageSquare, Users, Settings } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface SessionMetadata {
  session_id?: string | null;
  total_utterances?: number;
  counselor_utterances?: number;
  student_utterances?: number;
  verification_scope?: string;
  content_filtering?: string;
  original_length_words?: number;
  filtered_length_words?: number;
  diarization_note?: string;
}

interface AudioAnalysisData {
  session_metadata?: SessionMetadata;
}

interface SessionMetadataProps {
  audioAnalysisData?: AudioAnalysisData;
}

export default function SessionMetadataCard({ audioAnalysisData }: SessionMetadataProps) {
  // Handle missing audio analysis data
  if (!audioAnalysisData?.session_metadata) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Info className="h-5 w-5" />
            Session Metadata
          </CardTitle>
          <CardDescription>
            Processing and analysis information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Info className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Metadata Pending</p>
            <p className="text-xs text-muted-foreground">
              Session processing information will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const metadata = audioAnalysisData.session_metadata;

  // Helper function to format numbers with commas
  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toLocaleString();
  };

  // Helper function to calculate percentage
  const calculatePercentage = (part?: number, total?: number) => {
    if (!part || !total || total === 0) return 0;
    return Math.round((part / total) * 100);
  };

  // Calculate utterance percentages
  const counselorPercentage = calculatePercentage(metadata.counselor_utterances, metadata.total_utterances);
  const studentPercentage = calculatePercentage(metadata.student_utterances, metadata.total_utterances);

  // Calculate word filtering efficiency
  const filteringEfficiency = calculatePercentage(metadata.filtered_length_words, metadata.original_length_words);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Info className="h-5 w-5" />
          Session Metadata
        </CardTitle>
        <CardDescription>
          Processing and analysis information
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Session Overview */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
            <MessageSquare className="h-6 w-6 text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-blue-700">
              {formatNumber(metadata.total_utterances)}
            </div>
            <div className="text-xs text-blue-600">Total Utterances</div>
          </div>
          
          <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
            <Users className="h-6 w-6 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-700">
              {formatNumber(metadata.counselor_utterances)}
            </div>
            <div className="text-xs text-green-600">Counselor ({counselorPercentage}%)</div>
          </div>
          
          <div className="text-center p-3 bg-purple-50 rounded-lg border border-purple-200">
            <Users className="h-6 w-6 text-purple-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-purple-700">
              {formatNumber(metadata.student_utterances)}
            </div>
            <div className="text-xs text-purple-600">Student ({studentPercentage}%)</div>
          </div>
        </div>

        <Separator />

        {/* Content Processing */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground">Content Processing</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Word Analysis */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Original Words</span>
                <span className="font-medium">{formatNumber(metadata.original_length_words)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Filtered Words</span>
                <span className="font-medium">{formatNumber(metadata.filtered_length_words)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Filtering Efficiency</span>
                <Badge variant="secondary">{filteringEfficiency}% retained</Badge>
              </div>
            </div>

            {/* Processing Settings */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Verification Scope</span>
                <Badge variant="outline">{metadata.verification_scope || 'N/A'}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Content Filtering</span>
                <Badge variant="outline">{metadata.content_filtering || 'N/A'}</Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Session Information */}
        {(metadata.session_id || metadata.diarization_note) && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">Session Information</h4>
              
              {metadata.session_id && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Session ID</span>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    {metadata.session_id}
                  </code>
                </div>
              )}
              
              {metadata.diarization_note && (
                <div className="space-y-2">
                  <span className="text-sm font-medium text-muted-foreground">Processing Note</span>
                  <div className="text-sm bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-800">
                    <Settings className="h-4 w-4 inline mr-2" />
                    {metadata.diarization_note}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

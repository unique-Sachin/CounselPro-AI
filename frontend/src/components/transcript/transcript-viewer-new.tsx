"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Clock, FileText } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

// Types
interface TranscriptUtterance {
  speaker: number;
  text: string;
  start_time: string; // Format: "00:00:04.08"
  end_time: string;   // Format: "00:00:04.80"
  confidence: number;
  role: string;       // "counselor" or "student"
}

interface TranscriptMetadata {
  chunk_name: string;
  processing_time_seconds: number;
  timestamp: string;
  role_mapping: {
    counselor: number;
    student: number;
  };
  total_speakers: number;
}

interface TranscriptData {
  metadata: TranscriptMetadata;
  utterances: TranscriptUtterance[];
}

interface TranscriptViewerProps {
  data?: TranscriptData;
}

const formatTime = (timeString?: string) => {
  if (!timeString) return null;
  
  // Already in HH:MM:SS.MS format (expected format)
  if (timeString.includes(':')) {
    return timeString;
  }
  
  // Convert seconds to HH:MM:SS.MS format
  const seconds = parseFloat(timeString);
  if (!isNaN(seconds)) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  }
  
  return null;
};

const getBadgeVariant = (role: string) => {
  if (role === 'counselor') return 'default';
  if (role === 'student') return 'secondary';
  return 'outline';
};

export default function TranscriptViewer({ data }: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showOnlyCounselor, setShowOnlyCounselor] = useState(false);

  const utterances = data?.utterances || [];

  // Filter utterances based on search and counselor toggle
  const filteredUtterances = utterances.filter((utterance) => {
    const matchesSearch = searchQuery
      ? utterance.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        utterance.role.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    
    const matchesCounselorFilter = showOnlyCounselor
      ? utterance.role === 'counselor'
      : true;

    return matchesSearch && matchesCounselorFilter;
  });

  // If no data provided, show placeholder
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Transcript
          </CardTitle>
          <CardDescription>
            Session transcript will appear here after analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-4">
              <FileText className="w-12 h-12 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Transcript not available yet</h3>
              <p className="text-muted-foreground max-w-sm mx-auto">
                Please analyse the session to view transcript.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Transcript Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="counselor-only"
              checked={showOnlyCounselor}
              onCheckedChange={setShowOnlyCounselor}
            />
            <Label htmlFor="counselor-only">Show only counselor</Label>
          </div>

          {/* Stats */}
          <div className="text-sm text-muted-foreground">
            {filteredUtterances.length} of {utterances.length} utterances
            {searchQuery && ` matching "${searchQuery}"`}
          </div>
        </CardContent>
      </Card>

      {/* Transcript Content */}
      <Card>
        <CardHeader>
          <CardTitle>Conversation</CardTitle>
          {data.metadata && (
            <CardDescription>
              Processed: {new Date(data.metadata.timestamp).toLocaleString()} • 
              {data.metadata.total_speakers} speakers • 
              {Math.round(data.metadata.processing_time_seconds)}s processing time
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {filteredUtterances.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchQuery ? `No utterances found matching "${searchQuery}"` : "No utterances to display"}
            </div>
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              <AnimatePresence>
                {filteredUtterances.map((utterance, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2, delay: index * 0.02 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant={getBadgeVariant(utterance.role)}>
                        {utterance.role.charAt(0).toUpperCase() + utterance.role.slice(1)}
                      </Badge>
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{formatTime(utterance.start_time)}</span>
                        {utterance.confidence && (
                          <span className="ml-2">
                            {Math.round(utterance.confidence * 100)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-sm leading-relaxed pl-4 border-l-2 border-l-muted">
                      {utterance.text}
                    </p>
                    {index < filteredUtterances.length - 1 && <Separator className="my-4" />}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Upload, Clock } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

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
  
  return timeString;
};

const getSpeakerBadgeVariant = (role: string) => {
  const normalizedRole = role.toLowerCase();
  if (normalizedRole === 'counselor') {
    return "default";
  }
  if (normalizedRole === 'student') {
    return "secondary";
  }
  return "outline";
};

const DropzoneCard = ({ onFileUpload }: { onFileUpload: (data: TranscriptData) => void }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileUpload = useCallback((file: File) => {
    if (file.type === "application/json") {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const jsonData = JSON.parse(e.target?.result as string);
          
          // Handle the new expected format with metadata and utterances
          if (jsonData.metadata && jsonData.utterances && Array.isArray(jsonData.utterances)) {
            onFileUpload(jsonData);
          } 
          // Handle legacy format - array of utterances
          else if (Array.isArray(jsonData)) {
            const legacyData: TranscriptData = {
              metadata: {
                chunk_name: "legacy-upload",
                processing_time_seconds: 0,
                timestamp: new Date().toISOString(),
                role_mapping: { counselor: 0, student: 1 },
                total_speakers: 2
              },
              utterances: jsonData.map((item: {speaker?: string; text?: string; start_time?: string; end_time?: string}, index: number) => ({
                speaker: item.speaker === "Counselor" ? 0 : 1,
                text: item.text || "",
                start_time: item.start_time || `00:00:${String(index * 5).padStart(2, '0')}.00`,
                end_time: item.end_time || `00:00:${String((index + 1) * 5).padStart(2, '0')}.00`,
                confidence: 1.0,
                role: item.speaker === "Counselor" ? "counselor" : "student"
              }))
            };
            onFileUpload(legacyData);
          }
          // Handle legacy format with utterances array
          else if (jsonData.utterances && Array.isArray(jsonData.utterances)) {
            const legacyData: TranscriptData = {
              metadata: {
                chunk_name: "legacy-upload",
                processing_time_seconds: 0,
                timestamp: new Date().toISOString(),
                role_mapping: { counselor: 0, student: 1 },
                total_speakers: 2
              },
              utterances: jsonData.utterances.map((item: {speaker?: string; text?: string; start_time?: string; end_time?: string}, index: number) => ({
                speaker: item.speaker === "Counselor" ? 0 : 1,
                text: item.text || "",
                start_time: item.start_time || `00:00:${String(index * 5).padStart(2, '0')}.00`,
                end_time: item.end_time || `00:00:${String((index + 1) * 5).padStart(2, '0')}.00`,
                confidence: 1.0,
                role: item.speaker === "Counselor" ? "counselor" : "student"
              }))
            };
            onFileUpload(legacyData);
          }
          // Handle Deepgram format  
          else if (jsonData.results && Array.isArray(jsonData.results)) {
            const deepgramData: TranscriptData = {
              metadata: {
                chunk_name: "deepgram-upload",
                processing_time_seconds: 0,
                timestamp: new Date().toISOString(),
                role_mapping: { counselor: 0, student: 1 },
                total_speakers: 2
              },
              utterances: jsonData.results.map((result: {
                speaker?: string;
                text?: string;
                transcript?: string;
                start?: number | string;
                end?: number | string;
              }, index: number) => ({
                speaker: result.speaker === "Counselor" ? 0 : 1,
                text: result.text || result.transcript || "",
                start_time: result.start ? `00:00:${String(Math.floor(Number(result.start))).padStart(2, '0')}.${String(Math.floor((Number(result.start) % 1) * 100)).padStart(2, '0')}` : `00:00:${String(index * 5).padStart(2, '0')}.00`,
                end_time: result.end ? `00:00:${String(Math.floor(Number(result.end))).padStart(2, '0')}.${String(Math.floor((Number(result.end) % 1) * 100)).padStart(2, '0')}` : `00:00:${String((index + 1) * 5).padStart(2, '0')}.00`,
                confidence: 1.0,
                role: result.speaker === "Counselor" ? "counselor" : "student"
              }))
            };
            onFileUpload(deepgramData);
          }
          else {
            throw new Error("Unrecognized format");
          }
        } catch (error) {
          console.error("Failed to parse transcript JSON:", error);
          alert("Invalid JSON format. Please upload a valid transcript file.");
        }
      };
      reader.readAsText(file);
    } else {
      alert("Please select a JSON file.");
    }
  }, [onFileUpload]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const jsonFile = files.find(file => file.type === "application/json");
    
    if (jsonFile) {
      handleFileUpload(jsonFile);
    }
  }, [handleFileUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Upload Transcript
        </CardTitle>
        <CardDescription>
          Drop a JSON file or click to upload a transcript
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">
            Drop your transcript file here
          </p>
          <p className="text-muted-foreground mb-4">
            Supports JSON format with utterances array
          </p>
          <div className="flex items-center justify-center">
            <Input
              type="file"
              accept=".json"
              onChange={handleFileSelect}
              className="hidden"
              id="transcript-upload"
            />
            <Button asChild>
              <label htmlFor="transcript-upload" className="cursor-pointer">
                Choose File
              </label>
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Expected format: {`{metadata: {...}, utterances: [{speaker: 0, text: "Hello...", start_time: "00:00:04.08", end_time: "00:00:04.80", role: "counselor"}]}`}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default function TranscriptViewer({ data }: TranscriptViewerProps) {
  const [transcriptData, setTranscriptData] = useState<TranscriptData | undefined>(data);
  const [searchQuery, setSearchQuery] = useState("");
  const [showOnlyCounselor, setShowOnlyCounselor] = useState(false);

  const utterances = transcriptData?.utterances || [];

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

  // If no data provided and no uploaded data, show dropzone
  if (!transcriptData) {
    return <DropzoneCard onFileUpload={setTranscriptData} />;
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Transcript Viewer
          </CardTitle>
          <CardDescription>
            {utterances.length} utterances loaded
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Switch
                id="counselor-only"
                checked={showOnlyCounselor}
                onCheckedChange={setShowOnlyCounselor}
              />
              <Label htmlFor="counselor-only" className="text-sm">
                Show only Counselor
              </Label>
            </div>

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>
                Showing {filteredUtterances.length} of {utterances.length}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTranscriptData(undefined)}
                className="h-8"
              >
                <Upload className="h-3 w-3 mr-1" />
                Upload New
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transcript List */}
      <Card>
        <CardContent className="p-0">
          {filteredUtterances.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="mx-auto h-12 w-12 mb-4 text-muted-foreground/50" />
              <p>No utterances match your filters.</p>
            </div>
          ) : (
            <div className="max-h-[600px] overflow-y-auto">
              <AnimatePresence>
                {filteredUtterances.map((utterance, index) => (
                  <motion.div
                    key={`${utterance.speaker}-${index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2, delay: index * 0.02 }}
                    className="border-b last:border-b-0 p-4 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      {/* Speaker Badge */}
                      <Badge 
                        variant={getSpeakerBadgeVariant(utterance.role)}
                        className="shrink-0 min-w-fit capitalize"
                      >
                        {utterance.role}
                      </Badge>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm leading-relaxed break-words">
                          {utterance.text}
                        </p>

                        {/* Timestamps */}
                        {(utterance.start_time || utterance.end_time) && (
                          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {utterance.start_time && (
                              <span>{formatTime(utterance.start_time)}</span>
                            )}
                            {utterance.start_time && utterance.end_time && (
                              <span>-</span>
                            )}
                            {utterance.end_time && (
                              <span>{formatTime(utterance.end_time)}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
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

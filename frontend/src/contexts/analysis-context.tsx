"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface AnalysisContextType {
  isAnalyzing: boolean;
  setIsAnalyzing: (analyzing: boolean) => void;
  sessionUid: string | null;
  setSessionUid: (uid: string | null) => void;
  analysisSource: 'session-details' | 'transcript-tab' | 'analysis-tab' | 'analysis-action-button' | null;
  setAnalysisSource: (source: 'session-details' | 'transcript-tab' | 'analysis-tab' | 'analysis-action-button' | null) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return context;
}

interface AnalysisProviderProps {
  children: ReactNode;
}

export function AnalysisProvider({ children }: AnalysisProviderProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionUid, setSessionUid] = useState<string | null>(null);
  const [analysisSource, setAnalysisSource] = useState<'session-details' | 'transcript-tab' | 'analysis-tab' | 'analysis-action-button' | null>(null);

  return (
    <AnalysisContext.Provider 
      value={{ 
        isAnalyzing, 
        setIsAnalyzing, 
        sessionUid, 
        setSessionUid,
        analysisSource,
        setAnalysisSource
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

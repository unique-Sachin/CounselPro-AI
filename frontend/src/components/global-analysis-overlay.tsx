"use client";

import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, Loader2 } from "lucide-react";
import { useAnalysis } from "@/contexts/analysis-context";

export function GlobalAnalysisOverlay() {
  const { isAnalyzing, analysisSource } = useAnalysis();

  // Show overlay for both transcript-tab and session-details analysis
  const shouldShowOverlay = isAnalyzing && (analysisSource === 'transcript-tab' || analysisSource === 'session-details');

  return (
    <AnimatePresence>
      {shouldShowOverlay && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm"
          style={{ pointerEvents: "all" }}
        >
          <div className="flex items-center justify-center min-h-screen">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="bg-card border rounded-lg shadow-lg p-8 max-w-md mx-4"
            >
              <div className="text-center space-y-6">
                {/* Animated Icon */}
                <motion.div
                  className="mx-auto w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <BarChart3 className="w-10 h-10 text-primary" />
                </motion.div>

                {/* Content */}
                <div className="space-y-3">
                  <h2 className="text-xl font-semibold">Session Analysis in Progress</h2>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {analysisSource === 'session-details' 
                      ? "We're analyzing the session content to generate comprehensive insights and reports. Please wait while this process completes."
                      : "We're analyzing the session content to generate insights and transcript. Please wait while this process completes."
                    }
                  </p>
                </div>

                {/* Progress indicator */}
                <motion.div
                  className="flex items-center justify-center gap-2 text-sm text-muted-foreground"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                >
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing...</span>
                </motion.div>

                {/* Info note */}
                <motion.p
                  className="text-xs text-muted-foreground border-t pt-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.7 }}
                >
                  Navigation is temporarily disabled during analysis
                </motion.p>
              </div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

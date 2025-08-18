"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { getQueryClient } from "@/lib/queryClient";
import { AnalysisProvider } from "@/contexts/analysis-context";

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <AnalysisProvider>
        {children}
        <Toaster />
      </AnalysisProvider>
    </QueryClientProvider>
  );
}

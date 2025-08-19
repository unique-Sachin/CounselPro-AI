"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { getQueryClient } from "@/lib/queryClient";
import { AnalysisProvider } from "@/contexts/analysis-context";
import { ThemeProvider } from "@/components/theme-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <AnalysisProvider>
          {children}
          <Toaster />
        </AnalysisProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

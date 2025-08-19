"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAnalysis } from "@/contexts/analysis-context";

export function useNavigationLock() {
  const { isAnalyzing } = useAnalysis();
  const router = useRouter();

  useEffect(() => {
    if (!isAnalyzing) return;

    // Store original router methods
    const originalPush = router.push;
    const originalReplace = router.replace;
    const originalBack = router.back;
    const originalForward = router.forward;

    // Override router methods to prevent navigation
    router.push = () => {
      console.warn("Navigation blocked: Analysis in progress");
      return Promise.resolve(true);
    };
    
    router.replace = () => {
      console.warn("Navigation blocked: Analysis in progress");
      return Promise.resolve(true);
    };
    
    router.back = () => {
      console.warn("Navigation blocked: Analysis in progress");
    };
    
    router.forward = () => {
      console.warn("Navigation blocked: Analysis in progress");
    };

    // Block browser back/forward buttons
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "Analysis is in progress. Are you sure you want to leave?";
      return e.returnValue;
    };

    const handlePopState = (e: PopStateEvent) => {
      if (isAnalyzing) {
        e.preventDefault();
        window.history.pushState(null, "", window.location.href);
        console.warn("Navigation blocked: Analysis in progress");
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("popstate", handlePopState);

    // Cleanup on unmount or when analysis finishes
    return () => {
      router.push = originalPush;
      router.replace = originalReplace;
      router.back = originalBack;
      router.forward = originalForward;
      
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("popstate", handlePopState);
    };
  }, [isAnalyzing, router]);
}

"use client";

import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { 
  Users, 
  FileText, 
  Shield, 
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Info
} from "lucide-react";
import { listCounselors } from "@/lib/services/counselors";
import { listSessions } from "@/lib/services/sessions";

// Animation variants for staggered card entrance
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const cardVariants = {
  hidden: { 
    opacity: 0, 
    y: 20,
    scale: 0.95
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.4
    }
  }
};

// Mock KPI data for fields we don't have APIs for yet
const mockStaticKpis = {
  complianceRate: {
    value: "98.2%",
    delta: "+1.8%",
    deltaDirection: "up" as const
  },
  feedbackRate: {
    value: "94.7%", 
    delta: "-2.1%",
    deltaDirection: "down" as const
  }
};

interface KpiCardProps {
  title: string;
  value: string;
  delta: string;
  deltaDirection: "up" | "down";
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  isLoading?: boolean;
  hasTooltip?: boolean;
  tooltipText?: string;
}

function KpiCard({ 
  title, 
  value, 
  delta, 
  deltaDirection, 
  icon: Icon, 
  description, 
  isLoading = false,
  hasTooltip = false,
  tooltipText
}: KpiCardProps) {
  const isPositive = deltaDirection === "up";
  const DeltaIcon = isPositive ? TrendingUp : TrendingDown;
  
  const cardContent = (
    <motion.div variants={cardVariants}>
      <Card className="hover:shadow-md transition-shadow duration-200">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-1">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {title}
            </CardTitle>
            {hasTooltip && (
              <Info className="h-3 w-3 text-muted-foreground" />
            )}
          </div>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {isLoading ? (
              <>
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-4 w-24" />
              </>
            ) : (
              <>
                <div className="text-2xl font-bold tracking-tight">
                  {value}
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <DeltaIcon 
                    className={`h-3 w-3 ${
                      isPositive 
                        ? "text-green-600 dark:text-green-400" 
                        : "text-red-600 dark:text-red-400"
                    }`} 
                  />
                  <span 
                    className={`font-medium ${
                      isPositive 
                        ? "text-green-600 dark:text-green-400" 
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {delta}
                  </span>
                  <span className="text-muted-foreground">
                    {description}
                  </span>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  if (hasTooltip && tooltipText) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {cardContent}
          </TooltipTrigger>
          <TooltipContent>
            <p>{tooltipText}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return cardContent;
}

export function KpiRow() {
  // Fetch counselors data
  const { 
    data: counselorsData, 
    isLoading: counselorsLoading, 
    error: counselorsError 
  } = useQuery({
    queryKey: ['counselors-count'],
    queryFn: () => listCounselors(0, 1), // Just get total count, limit to 1 for efficiency
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch sessions data
  const { 
    data: sessionsData, 
    isLoading: sessionsLoading, 
    error: sessionsError 
  } = useQuery({
    queryKey: ['sessions-count'],
    queryFn: () => listSessions({ skip: 0, limit: 1 }), // Just get total count, limit to 1 for efficiency
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Prepare KPI data
  const kpiData = [
    {
      id: "total-sessions",
      title: "Total Sessions",
      value: sessionsError ? "Error" : sessionsData?.total?.toLocaleString() || "0",
      delta: "+12.5%", // Mock delta for now
      deltaDirection: "up" as const,
      icon: FileText,
      description: "vs last month",
      isLoading: sessionsLoading,
      hasTooltip: true,
      tooltipText: "Sampled from recent sessions data"
    },
    {
      id: "active-counselors",
      title: "Active Counselors",
      value: counselorsError ? "Error" : counselorsData?.total?.toString() || "0",
      delta: "+6.3%", // Mock delta for now
      deltaDirection: "up" as const,
      icon: Users,
      description: "vs last month",
      isLoading: counselorsLoading,
      hasTooltip: false
    },
    {
      id: "compliance-rate",
      title: "Compliance Rate",
      value: mockStaticKpis.complianceRate.value,
      delta: mockStaticKpis.complianceRate.delta,
      deltaDirection: mockStaticKpis.complianceRate.deltaDirection,
      icon: Shield,
      description: "vs last month",
      isLoading: false,
      hasTooltip: false
    },
    {
      id: "feedback-rate",
      title: "Same-Day Feedback Rate",
      value: mockStaticKpis.feedbackRate.value,
      delta: mockStaticKpis.feedbackRate.delta,
      deltaDirection: mockStaticKpis.feedbackRate.deltaDirection,
      icon: MessageSquare,
      description: "vs last month",
      isLoading: false,
      hasTooltip: false
    }
  ];

  return (
    <motion.div 
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {kpiData.map((kpi) => (
        <KpiCard
          key={kpi.id}
          title={kpi.title}
          value={kpi.value}
          delta={kpi.delta}
          deltaDirection={kpi.deltaDirection}
          icon={kpi.icon}
          description={kpi.description}
          isLoading={kpi.isLoading}
          hasTooltip={kpi.hasTooltip}
          tooltipText={kpi.tooltipText}
        />
      ))}
    </motion.div>
  );
}

export default KpiRow;

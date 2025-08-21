"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  BarChart3, 
  Clock,
  Trophy
} from "lucide-react";
import { KpiRow } from "@/components/dashboard/KpiRow";
import { QualityGlance } from "@/components/dashboard/QualityGlance";
import { RecentAnalyses } from "@/components/dashboard/RecentAnalyses";

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5
    }
  }
};

export default function DashboardPage() {
  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard — AI-Powered Counselor Excellence</h1>
        <p className="text-muted-foreground">
          Monitor performance, quality metrics, and operational insights across your counseling platform
        </p>
      </motion.div>

      {/* KPI Row - 4 Compact Cards */}
      <motion.div variants={itemVariants}>
        <KpiRow />
      </motion.div>

      {/* Quality at a Glance */}
      <motion.div variants={itemVariants}>
        <QualityGlance />
      </motion.div>

      {/* Recent Analyses Table */}
      <motion.div variants={itemVariants}>
        <RecentAnalyses />
      </motion.div>

      {/* Leaderboards & Benchmarks - 2-up Grid */}
      <motion.div 
        className="grid gap-6 lg:grid-cols-2"
        variants={itemVariants}
      >
        {/* Leaderboard */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Performance Leaderboard
            </CardTitle>
            <CardDescription>Top performing counselors this month</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { name: "Dr. Sarah Chen", score: 98.5, sessions: 45 },
              { name: "Dr. Emily Rodriguez", score: 97.2, sessions: 38 },
              { name: "Michael Torres", score: 96.8, sessions: 52 },
              { name: "Dr. Lisa Park", score: 95.1, sessions: 41 },
              { name: "James Wilson", score: 94.7, sessions: 29 }
            ].map((counselor, index) => (
              <div key={counselor.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-sm font-bold text-muted-foreground w-6">
                    #{index + 1}
                  </div>
                  <div>
                    <div className="font-medium">{counselor.name}</div>
                    <div className="text-xs text-muted-foreground">{counselor.sessions} sessions</div>
                  </div>
                </div>
                <Badge variant="default">{counselor.score}%</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Benchmarks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Performance Benchmarks
            </CardTitle>
            <CardDescription>Key metrics vs industry standards</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Response Accuracy</span>
                <span className="text-sm text-muted-foreground">94.2% vs 88% industry</span>
              </div>
              <Progress value={94.2} className="h-2" />
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Client Satisfaction</span>
                <span className="text-sm text-muted-foreground">96.8% vs 89% industry</span>
              </div>
              <Progress value={96.8} className="h-2" />
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Session Completion</span>
                <span className="text-sm text-muted-foreground">98.1% vs 92% industry</span>
              </div>
              <Progress value={98.1} className="h-2" />
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Average Session Time</span>
                <span className="text-sm text-muted-foreground">24m vs 31m industry</span>
              </div>
              <Progress value={77} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Processing Queue */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Processing Queue
            </CardTitle>
            <CardDescription>Jobs in progress and pending analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { id: "JOB-001", type: "Session Analysis", counselor: "Dr. Sarah Chen", progress: 75, eta: "2m" },
                { id: "JOB-002", type: "Quality Review", counselor: "Michael Torres", progress: 45, eta: "5m" },
                { id: "JOB-003", type: "Compliance Check", counselor: "Dr. Emily Rodriguez", progress: 90, eta: "1m" },
                { id: "JOB-004", type: "Performance Eval", counselor: "James Wilson", progress: 25, eta: "8m" }
              ].map((job) => (
                <div key={job.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="font-medium text-sm">{job.type}</div>
                      <div className="text-xs text-muted-foreground">{job.counselor} • ETA {job.eta}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{job.progress}%</div>
                      <Badge variant="outline" className="text-xs">{job.id}</Badge>
                    </div>
                  </div>
                  <Progress value={job.progress} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>     
    </motion.div>
  );
}

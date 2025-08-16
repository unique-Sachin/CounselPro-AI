"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Calendar, FileText, Link, Users, ExternalLink } from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import { getSession } from "@/lib/services/sessions";

export default function SessionDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const sessionUid = params.uid as string;

  // Fetch session details
  const {
    data: session,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["session", sessionUid],
    queryFn: () => getSession(sessionUid),
    enabled: !!sessionUid,
  });

  if (isLoading) {
    return (
      <PageTransition>
        <div className="container max-w-4xl mx-auto py-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          <div className="space-y-6">
            <div>
              <Skeleton className="h-8 w-64 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
            
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-64" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-6 w-48" />
              </CardContent>
            </Card>
          </div>
        </div>
      </PageTransition>
    );
  }

  if (error) {
    return (
      <PageTransition>
        <div className="container max-w-4xl mx-auto py-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold mb-2">Session Not Found</h2>
                <p className="text-muted-foreground mb-4">
                  The session you&apos;re looking for doesn&apos;t exist or has been removed.
                </p>
                <Button onClick={() => router.push("/sessions")}>
                  Back to Sessions
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="container max-w-4xl mx-auto py-6">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Session Details</h1>
            <p className="text-muted-foreground mt-2">
              Session ID: {sessionUid}
            </p>
          </div>
        </div>

        {/* Session Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Session Information
              </CardTitle>
              <CardDescription>
                Details and information about this counseling session
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Description */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <FileText className="h-4 w-4" />
                  Description
                </div>
                <p className="text-muted-foreground bg-muted p-3 rounded-md">
                  {session?.description}
                </p>
              </div>

              {/* Session Date */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Calendar className="h-4 w-4" />
                  Scheduled Date & Time
                </div>
                <Badge variant="outline" className="w-fit">
                  {session?.session_date ? new Date(session.session_date).toLocaleString() : 'Not specified'}
                </Badge>
              </div>

              {/* Recording Link */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Link className="h-4 w-4" />
                  Recording Link
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <a 
                      href={session?.recording_link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center gap-2"
                    >
                      Open Recording
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </Button>
                </div>
              </div>

              {/* Counselor Info (if available) */}
              {session?.counselor && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Users className="h-4 w-4" />
                    Assigned Counselor
                  </div>
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="font-medium">{session.counselor.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {session.counselor.specialty}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Actions */}
        <div className="flex gap-4 mt-6">
          <Button variant="outline" onClick={() => router.push("/sessions")}>
            All Sessions
          </Button>
          <Button variant="outline" onClick={() => router.push("/sessions/new")}>
            Create New Session
          </Button>
        </div>
      </div>
    </PageTransition>
  );
}

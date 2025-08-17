"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Calendar, Search, ChevronLeft, ChevronRight } from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { listSessions, listSessionsByCounselor, getCounselors } from "@/lib/services/sessions";
import Link from "next/link";

const ITEMS_PER_PAGE = 10;

export default function SessionsPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCounselor, setSelectedCounselor] = useState<string>("all");

  const skip = (currentPage - 1) * ITEMS_PER_PAGE;

  // Fetch counselors for the filter dropdown
  const {
    data: counselors,
  } = useQuery({
    queryKey: ["counselors"],
    queryFn: getCounselors,
    staleTime: 300000, // 5 minutes
  });

  // Fetch sessions with React Query - either all sessions or by counselor
  const {
    data: sessionsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["sessions", skip, ITEMS_PER_PAGE, selectedCounselor],
    queryFn: () => {
      if (selectedCounselor && selectedCounselor !== "all") {
        return listSessionsByCounselor(selectedCounselor, { skip, limit: ITEMS_PER_PAGE });
      }
      return listSessions({ skip, limit: ITEMS_PER_PAGE });
    },
    staleTime: 30000, // 30 seconds
  });

  // Client-side filtering
  const filteredSessions = sessionsData?.items?.filter((session) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      session.description.toLowerCase().includes(searchLower) ||
      session.counselor?.name?.toLowerCase().includes(searchLower)
    );
  }) || [];

  const totalPages = sessionsData ? Math.ceil(sessionsData.total / ITEMS_PER_PAGE) : 0;

  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const handleCounselorChange = (value: string) => {
    setSelectedCounselor(value);
    setCurrentPage(1); // Reset to first page when filter changes
  };

  return (
    <PageTransition>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Sessions</h1>
            <p className="text-muted-foreground">
              Manage counseling sessions and recordings
            </p>
          </div>
          
          <Button asChild>
            <Link href="/sessions/new">
              <Plus className="mr-2 h-4 w-4" />
              Create Session
            </Link>
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search sessions or counselors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
          
          <Select value={selectedCounselor} onValueChange={handleCounselorChange}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All counselors" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All counselors</SelectItem>
              {counselors?.map((counselor) => (
                <SelectItem key={counselor.uid} value={counselor.uid}>
                  {counselor.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Sessions List */}
        <Card>
          <CardHeader>
            <CardTitle>
              {selectedCounselor && selectedCounselor !== "all"
                ? `Sessions by ${counselors?.find(c => c.uid === selectedCounselor)?.name || 'Selected Counselor'}`
                : 'All Sessions'
              }
            </CardTitle>
            <CardDescription>
              {isLoading 
                ? "Loading sessions..." 
                : `${sessionsData?.total || 0} total sessions`
              }
              {searchQuery && !isLoading && (
                <>
                  {" • "}
                  {filteredSessions.length} matching &ldquo;{searchQuery}&rdquo;
                </>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-64" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                    <Skeleton className="h-8 w-20" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">Failed to load sessions</p>
                <Button variant="outline" onClick={() => window.location.reload()}>
                  Try Again
                </Button>
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="text-center py-8">
                <Calendar className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  {searchQuery ? "No sessions match your search" : "No sessions found"}
                </p>
                <Button asChild>
                  <Link href="/sessions/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Your First Session
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredSessions.map((session) => (
                  <motion.div
                    key={session.uid}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="space-y-1">
                      <p className="font-medium line-clamp-1">
                        {session.description}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>
                          {session.session_date ? new Date(session.session_date).toLocaleDateString() : 'Date not set'}
                        </span>
                        <span>•</span>
                        <span>
                          Counselor: {session.counselor?.name || 'Unknown'}
                        </span>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/sessions/${session.uid}`}>
                        View Details
                      </Link>
                    </Button>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {!isLoading && sessionsData && sessionsData.total > ITEMS_PER_PAGE && (
              <div className="flex items-center justify-between px-2 py-4">
                <div className="text-sm text-muted-foreground">
                  Showing {skip + 1} to {Math.min(skip + ITEMS_PER_PAGE, sessionsData.total)} of {sessionsData.total} results
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousPage}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <div className="flex items-center space-x-1">
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage} of {totalPages}
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNextPage}
                    disabled={currentPage === totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  );
}

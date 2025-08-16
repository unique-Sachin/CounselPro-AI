"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { PageTransition } from "@/components/page-transition";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Plus, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Edit, 
  Trash2,
  Phone,
  Mail
} from "lucide-react";
import { listCounselors } from "@/lib/services/counselors";
import { CounselorForm } from "@/components/counselors/counselor-form";
import { DeleteCounselorDialog } from "@/components/counselors/delete-counselor-dialog";

const ITEMS_PER_PAGE = 10;

// Animation variants
const tableVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      staggerChildren: 0.05
    }
  }
};

const rowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.2 }
  }
};

// Loading skeleton component
function CounselorTableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex items-center space-x-4 p-4">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  );
}

// Empty state component
function EmptyState() {
  return (
    <Card className="w-full">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <div className="text-center space-y-4">
          <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center">
            <Plus className="w-12 h-12 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">No counselors found</h3>
            <p className="text-muted-foreground max-w-sm">
              Get started by adding your first counselor to the platform
            </p>
          </div>
          <CounselorForm>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Counselor
            </Button>
          </CounselorForm>
        </div>
      </CardContent>
    </Card>
  );
}

export default function CounselorsPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  const skip = (currentPage - 1) * ITEMS_PER_PAGE;

  // Fetch counselors with React Query
  const {
    data: counselorsData,
    isLoading,
    error,
    isError
  } = useQuery({
    queryKey: ["counselors", skip, ITEMS_PER_PAGE],
    queryFn: () => listCounselors({ skip, limit: ITEMS_PER_PAGE }),
    staleTime: 30000, // 30 seconds
  });

  // Client-side filtering
  const filteredCounselors = counselorsData?.items?.filter((counselor) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      counselor.name.toLowerCase().includes(searchLower) ||
      counselor.email.toLowerCase().includes(searchLower) ||
      counselor.specialty.toLowerCase().includes(searchLower)
    );
  }) || [];

  const totalPages = counselorsData ? Math.ceil(counselorsData.total / ITEMS_PER_PAGE) : 0;

  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  return (
    <PageTransition>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Counselors</h1>
            <p className="text-muted-foreground">
              Manage your legal counseling team
            </p>
          </div>
          <CounselorForm />
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search counselors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Content */}
        {isError ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold">Error loading counselors</h3>
                <p className="text-muted-foreground">
                  {error instanceof Error ? error.message : "Something went wrong"}
                </p>
                <Button 
                  variant="outline" 
                  onClick={() => window.location.reload()}
                >
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Team Directory</CardTitle>
              <CardDescription>
                {isLoading 
                  ? "Loading counselors..." 
                  : `${counselorsData?.total || 0} total counselors`
                }
                {searchQuery && !isLoading && (
                  <>
                    {" • "}
                    {filteredCounselors.length} matching &ldquo;{searchQuery}&rdquo;
                  </>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <CounselorTableSkeleton />
              ) : counselorsData?.items?.length === 0 ? (
                <EmptyState />
              ) : (
                <motion.div
                  variants={tableVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Employee ID</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Mobile</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredCounselors.map((counselor) => (
                        <motion.tr key={counselor.uid} variants={rowVariants}>
                          <TableCell className="font-medium">
                            <div>
                              <div className="font-medium">{counselor.name}</div>
                              <div className="text-sm text-muted-foreground">
                                {counselor.years_of_experience || 0} years experience
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {counselor.uid.split('-')[0].toUpperCase()}
                            </code>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {counselor.specialty}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Mail className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{counselor.email}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {counselor.phone ? (
                              <div className="flex items-center space-x-2">
                                <Phone className="h-4 w-4 text-muted-foreground" />
                                <span className="text-sm">{counselor.phone}</span>
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                counselor.availability_status === "available" ? "default" :
                                counselor.availability_status === "busy" ? "destructive" : 
                                "secondary"
                              }
                            >
                              {counselor.availability_status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end space-x-2">
                              <CounselorForm 
                                mode="edit" 
                                counselor={counselor}
                              >
                                <Button variant="ghost" size="sm">
                                  <Edit className="h-4 w-4" />
                                  <span className="sr-only">Edit counselor</span>
                                </Button>
                              </CounselorForm>
                              <DeleteCounselorDialog counselor={counselor}>
                                <Button variant="ghost" size="sm">
                                  <Trash2 className="h-4 w-4" />
                                  <span className="sr-only">Delete counselor</span>
                                </Button>
                              </DeleteCounselorDialog>
                            </div>
                          </TableCell>
                        </motion.tr>
                      ))}
                    </TableBody>
                  </Table>
                </motion.div>
              )}

              {/* Pagination */}
              {!isLoading && counselorsData && counselorsData.total > ITEMS_PER_PAGE && (
                <div className="flex items-center justify-between px-2 py-4">
                  <div className="text-sm text-muted-foreground">
                    Showing {skip + 1} to {Math.min(skip + ITEMS_PER_PAGE, counselorsData.total)} of {counselorsData.total} results
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
                      <span className="text-sm font-medium">{currentPage}</span>
                      <span className="text-sm text-muted-foreground">of {totalPages}</span>
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
        )}
      </div>
    </PageTransition>
  );
}

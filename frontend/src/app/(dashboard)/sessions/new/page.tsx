"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { ArrowLeft, Calendar, FileText, Link, Users, Loader2 } from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { createSession } from "@/lib/services/sessions";
import { listCounselors } from "@/lib/services/counselors";
import { SessionCreate } from "@/lib/types";

// Form validation schema
const sessionFormSchema = z.object({
  counselor_uid: z.string().min(1, "Please select a counselor"),
  description: z.string().min(10, "Description must be at least 10 characters"),
  session_date: z.string().min(1, "Session date is required"),
  recording_link: z.string().url("Please enter a valid URL"),
});

type SessionFormData = z.infer<typeof sessionFormSchema>;

// Animation variants
const formVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      staggerChildren: 0.1
    }
  }
};

const fieldVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.2 }
  }
};

export default function NewSessionPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form setup
  const form = useForm<SessionFormData>({
    resolver: zodResolver(sessionFormSchema),
    defaultValues: {
      counselor_uid: "",
      description: "",
      session_date: "",
      recording_link: "",
    },
  });

  // Fetch counselors for the dropdown
  const {
    data: counselorsData,
    isLoading: loadingCounselors,
    error: counselorsError
  } = useQuery({
    queryKey: ["counselors", { skip: 0, limit: 100 }], // Get all counselors
    queryFn: () => listCounselors({ skip: 0, limit: 100 }),
    staleTime: 30000, // 30 seconds
  });

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data: SessionCreate) => createSession(data),
    onSuccess: (response) => {
      toast.success("Session created successfully!");
      // Redirect to session details page
      router.push(`/sessions/${response.uid}`);
    },
    onError: (error) => {
      console.error("Error creating session:", error);
      toast.error("Failed to create session. Please try again.");
      setIsSubmitting(false);
    },
  });

  const onSubmit = async (data: SessionFormData) => {
    setIsSubmitting(true);
    
    // Convert form data to API format
    const sessionData: SessionCreate = {
      counselor_uid: data.counselor_uid,
      description: data.description,
      session_date: new Date(data.session_date).toISOString(),
      recording_link: data.recording_link,
    };

    createSessionMutation.mutate(sessionData);
  };

  return (
    <PageTransition>
      <div className="container max-w-2xl mx-auto py-6">
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
            <h1 className="text-3xl font-bold tracking-tight">Create New Session</h1>
            <p className="text-muted-foreground mt-2">
              Schedule a new counseling session with detailed information
            </p>
          </div>
        </div>

        {/* Form */}
        <motion.div
          variants={formVariants}
          initial="hidden"
          animate="visible"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Session Details
              </CardTitle>
              <CardDescription>
                Fill in the information below to create a new counseling session
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  {/* Counselor Selection */}
                  <motion.div variants={fieldVariants}>
                    <FormField
                      control={form.control}
                      name="counselor_uid"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <Users className="h-4 w-4" />
                            Counselor *
                          </FormLabel>
                          <Select
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            disabled={loadingCounselors}
                          >
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder={
                                  loadingCounselors 
                                    ? "Loading counselors..." 
                                    : "Select a counselor"
                                } />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {counselorsData?.items?.map((counselor) => (
                                <SelectItem key={counselor.uid} value={counselor.uid}>
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{counselor.name}</span>
                                    <span className="text-muted-foreground text-sm">
                                      • {counselor.specialty}
                                    </span>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>

                  {/* Description */}
                  <motion.div variants={fieldVariants}>
                    <FormField
                      control={form.control}
                      name="description"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Session Description *
                          </FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Describe the purpose and goals of this session..."
                              className="min-h-[100px] resize-none"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>

                  {/* Session Date */}
                  <motion.div variants={fieldVariants}>
                    <FormField
                      control={form.control}
                      name="session_date"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <Calendar className="h-4 w-4" />
                            Session Date & Time *
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="datetime-local"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>

                  {/* Recording Link */}
                  <motion.div variants={fieldVariants}>
                    <FormField
                      control={form.control}
                      name="recording_link"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="flex items-center gap-2">
                            <Link className="h-4 w-4" />
                            Recording Link *
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="url"
                              placeholder="https://example.com/recording"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>

                  {/* Submit Button */}
                  <motion.div variants={fieldVariants} className="flex gap-4 pt-6">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => router.back()}
                      disabled={isSubmitting}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-1"
                    >
                      {isSubmitting && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      {isSubmitting ? "Creating Session..." : "Create Session"}
                    </Button>
                  </motion.div>
                </form>
              </Form>
            </CardContent>
          </Card>
        </motion.div>

        {/* Error state for counselors loading */}
        {counselorsError && (
          <Card className="mt-6">
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground">
                <p>Failed to load counselors. Please refresh the page to try again.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => window.location.reload()}
                >
                  Refresh Page
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}

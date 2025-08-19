"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Plus, Loader2 } from "lucide-react";
import { createCounselor, updateCounselor } from "@/lib/services/counselor-service";
import { CounselorResponse, CounselorUpdate } from "@/lib/types";

// Validation schema
const counselorFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(100, "Name must be less than 100 characters"),
  employee_id: z.string().min(3, "Employee ID must be at least 3 characters").max(20, "Employee ID must be less than 20 characters"),
  dept: z.string().min(2, "Department must be at least 2 characters").max(50, "Department must be less than 50 characters"),
  email: z.string().email("Please enter a valid email address"),
  mobile_number: z.string().min(10, "Mobile number must be at least 10 digits").regex(/^\+?[\d\s\-\(\)]{10,}$/, "Please enter a valid mobile number"),
});

type CounselorFormData = z.infer<typeof counselorFormSchema>;

interface CounselorFormProps {
  children?: React.ReactNode;
  counselor?: CounselorResponse; // For editing
  mode?: "create" | "edit";
}

export function CounselorForm({ children, counselor, mode = "create" }: CounselorFormProps) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const form = useForm<CounselorFormData>({
    resolver: zodResolver(counselorFormSchema),
    defaultValues: {
      name: counselor?.name || "",
      employee_id: counselor?.employee_id || "",
      dept: counselor?.dept || "",
      email: counselor?.email || "",
      mobile_number: counselor?.mobile_number || "",
    },
  });

  // Reset form when counselor data changes (for editing different counselors)
  useEffect(() => {
    if (counselor) {
      form.reset({
        name: counselor.name,
        employee_id: counselor.employee_id,
        dept: counselor.dept,
        email: counselor.email,
        mobile_number: counselor.mobile_number || "",
      });
    }
  }, [counselor, form]);

  const createCounselorMutation = useMutation({
    mutationFn: createCounselor,
    onSuccess: () => {
      // Close dialog
      setOpen(false);
      
      // Reset form
      form.reset();
      
      // Invalidate and refetch counselors list
      queryClient.invalidateQueries({ queryKey: ["counselors"] });
      
      // Show success toast
      toast.success("Counselor created successfully!");
    },
    onError: (error) => {
      console.error("Error creating counselor:", error);
      toast.error("Failed to create counselor. Please try again.");
    },
  });

  const updateCounselorMutation = useMutation({
    mutationFn: ({ uid, data }: { uid: string; data: CounselorUpdate }) => updateCounselor(uid, data),
    onSuccess: () => {
      // Close dialog
      setOpen(false);
      
      // Reset form
      form.reset();
      
      // Invalidate and refetch counselors list
      queryClient.invalidateQueries({ queryKey: ["counselors"] });
      
      // Show success toast
      toast.success("Counselor updated successfully!");
    },
    onError: (error) => {
      console.error("Error updating counselor:", error);
      toast.error("Failed to update counselor. Please try again.");
    },
  });

  const onSubmit = (data: CounselorFormData) => {
    // Map form data to API expected format
    const counselorData = {
      name: data.name,
      employee_id: data.employee_id,
      dept: data.dept,
      email: data.email,
      mobile_number: data.mobile_number,
      availability_status: "available" as const,
    };

    if (mode === 'edit' && counselor) {
      updateCounselorMutation.mutate({ 
        uid: counselor.uid, 
        data: counselorData
      });
    } else {
      createCounselorMutation.mutate(counselorData);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Counselor
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>{mode === 'edit' ? 'Edit Counselor' : 'Add New Counselor'}</DialogTitle>
          <DialogDescription>
            {mode === 'edit' 
              ? 'Update the counselor details below.' 
              : 'Fill in the details to add a new counselor to your team.'
            }
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="Dr. John Doe" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="employee_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Employee ID *</FormLabel>
                    <FormControl>
                      <Input placeholder="EMP001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="dept"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Department *</FormLabel>
                  <FormControl>
                    <Input placeholder="Family Law" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email Address *</FormLabel>
                  <FormControl>
                    <Input placeholder="john.doe@counselpro.ai" type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="mobile_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mobile Number *</FormLabel>
                  <FormControl>
                    <Input placeholder="+1 (555) 123-4567" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={createCounselorMutation.isPending}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={createCounselorMutation.isPending || updateCounselorMutation.isPending}
              >
                {(createCounselorMutation.isPending || updateCounselorMutation.isPending) && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {mode === 'edit' ? 'Update Counselor' : 'Create Counselor'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { deleteCounselor } from "@/lib/services/counselors";
import { CounselorResponse } from "@/lib/types";

interface DeleteCounselorDialogProps {
  counselor: CounselorResponse;
  children?: React.ReactNode;
}

export function DeleteCounselorDialog({ counselor, children }: DeleteCounselorDialogProps) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const deleteCounselorMutation = useMutation({
    mutationFn: (uid: string) => deleteCounselor(uid),
    onSuccess: () => {
      // Close dialog
      setOpen(false);
      
      // Invalidate and refetch counselors list
      queryClient.invalidateQueries({ queryKey: ["counselors"] });
      
      // Show success toast
      toast.success("Counselor deleted successfully!");
    },
    onError: (error) => {
      console.error("Error deleting counselor:", error);
      toast.error("Failed to delete counselor. Please try again.");
    },
  });

  const handleDelete = () => {
    deleteCounselorMutation.mutate(counselor.uid);
  };

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        {children || (
          <Button variant="ghost" size="sm">
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete{" "}
            <strong>{counselor.name}</strong> from your counselors list.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteCounselorMutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteCounselorMutation.isPending ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

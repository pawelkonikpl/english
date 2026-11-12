import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

/** Refresh every view that depends on what the learner studies. */
export function useInvalidateLearning(): () => void {
  const queryClient = useQueryClient();
  return useCallback(() => {
    for (const prefix of ["phrases", "review", "progress"]) {
      void queryClient.invalidateQueries({ queryKey: [prefix] });
    }
  }, [queryClient]);
}

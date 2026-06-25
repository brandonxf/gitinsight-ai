import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { getFindings, getJob, getResult, startAnalysis } from "./api";

const TERMINAL = new Set(["SUCCEEDED", "FAILED"]);

export function useStartAnalysis() {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (url: string) => startAnalysis(url),
    onSuccess: (data) => navigate(`/analysis/${data.job_id}`),
  });
}

/** Sondea el estado del job hasta que termina (SUCCEEDED/FAILED). */
export function useJobPolling(jobId: string) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && TERMINAL.has(status) ? false : 1500;
    },
  });
}

export function useResult(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["result", jobId],
    queryFn: () => getResult(jobId),
    enabled,
  });
}

export function useFindings(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["findings", jobId],
    queryFn: () => getFindings(jobId),
    enabled,
  });
}

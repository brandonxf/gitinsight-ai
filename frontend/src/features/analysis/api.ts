import { apiClient } from "../../lib/apiClient";

export type JobStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface AnalysisJob {
  id: string;
  repository_id: string;
  status: JobStatus;
  phase: string | null;
  progress_pct: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface CreateAnalysisResponse {
  job_id: string;
  status: JobStatus;
  links: { self: string; result: string };
}

export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  default_branch: string | null;
  commit_sha: string | null;
}

export interface TreeNode {
  name: string;
  type: "dir" | "file";
  children?: TreeNode[];
}

export interface Module {
  name: string;
  path: string;
  responsibility: string;
}

export interface AiStatus {
  available?: boolean;
  model?: string;
  error?: string;
}

export interface AnalysisResult {
  job: AnalysisJob;
  repository: Repository;
  primary_language: string | null;
  languages: Record<string, number>;
  frameworks: string[];
  structure: {
    top_level_dirs?: string[];
    top_level_files?: string[];
    total_files?: number;
    total_source_files?: number;
    total_size_bytes?: number;
    lines_of_code?: number;
    tree?: TreeNode[];
    architecture?: { pattern: string; signals: string[] };
  };
  summary: string | null;
  purpose: string | null;
  modules: Module[];
  flow_description: string | null;
  risk_level: string | null;
  quality_score: number | null;
  metrics: Record<string, any> & { ai?: AiStatus };
  diagrams: { architecture?: string; source?: string };
  generated_docs: { readme?: string };
}

export type FindingCategory =
  | "bug"
  | "code_smell"
  | "duplication"
  | "complexity"
  | "secret"
  | "vuln"
  | "insecure_config";

export type Severity = "info" | "low" | "medium" | "high" | "critical";

export interface Finding {
  id: string;
  category: FindingCategory;
  severity: Severity;
  rule_id: string | null;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  message: string;
  suggestion: string | null;
  metadata: Record<string, any>;
}

export interface FindingPage {
  items: Finding[];
  total: number;
  limit: number;
  offset: number;
}

export async function startAnalysis(url: string): Promise<CreateAnalysisResponse> {
  const { data } = await apiClient.post<CreateAnalysisResponse>("/analyses", { url });
  return data;
}

export async function getJob(jobId: string): Promise<AnalysisJob> {
  const { data } = await apiClient.get<AnalysisJob>(`/analyses/${jobId}`);
  return data;
}

export async function getResult(jobId: string): Promise<AnalysisResult> {
  const { data } = await apiClient.get<AnalysisResult>(`/analyses/${jobId}/result`);
  return data;
}

export async function getFindings(
  jobId: string,
  params: { category?: string; severity?: string; limit?: number } = {},
): Promise<FindingPage> {
  const { data } = await apiClient.get<FindingPage>(`/analyses/${jobId}/findings`, {
    params: { limit: 500, ...params },
  });
  return data;
}

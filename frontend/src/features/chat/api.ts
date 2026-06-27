import { apiClient } from "../../lib/apiClient";

export interface Citation {
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  symbol: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatSessionResponse {
  session_id: string;
  job_id: string;
}

export interface ChatHistory {
  session_id: string;
  messages: ChatMessage[];
}

export async function createChatSession(jobId: string): Promise<ChatSessionResponse> {
  const { data } = await apiClient.post<ChatSessionResponse>(
    `/analyses/${jobId}/chat/sessions`,
  );
  return data;
}

export async function postChatMessage(
  sessionId: string,
  message: string,
): Promise<ChatMessage> {
  const { data } = await apiClient.post<ChatMessage>(
    `/chat/sessions/${sessionId}/messages`,
    { message },
  );
  return data;
}

export async function getChatHistory(sessionId: string): Promise<ChatHistory> {
  const { data } = await apiClient.get<ChatHistory>(
    `/chat/sessions/${sessionId}/messages`,
  );
  return data;
}

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { ArrowRight, Chat, Code, Sparkles } from "../../components/icons";
import { Markdown } from "../analysis/markdown";
import {
  type ChatMessage,
  type Citation,
  createChatSession,
  postChatMessage,
} from "./api";

const SUGGESTIONS = [
  "¿Cuál es el propósito principal de este repositorio?",
  "¿Dónde está el punto de entrada de la aplicación?",
  "¿Qué módulos componen el proyecto y cómo se relacionan?",
];

export function ChatPanel({
  jobId,
  repoUrl,
  commitSha,
}: {
  jobId: string;
  repoUrl?: string | null;
  commitSha?: string | null;
}) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Crea la sesión de chat una sola vez al montar el panel.
  useEffect(() => {
    let active = true;
    createChatSession(jobId)
      .then((s) => active && setSessionId(s.session_id))
      .catch(() => active && setSessionError("No se pudo iniciar el chat."));
    return () => {
      active = false;
    };
  }, [jobId]);

  const send = useMutation({
    mutationFn: (message: string) => postChatMessage(sessionId as string, message),
    onSuccess: (assistant) => setMessages((m) => [...m, assistant]),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, send.isPending]);

  function ask(text: string) {
    const q = text.trim();
    if (!q || !sessionId || send.isPending) return;
    setMessages((m) => [
      ...m,
      { id: `local-${Date.now()}`, role: "user", content: q, citations: [], created_at: "" },
    ]);
    setInput("");
    send.mutate(q);
  }

  const sendError =
    send.error instanceof AxiosError
      ? (send.error.response?.data?.detail ?? "No se pudo enviar el mensaje.")
      : send.error
        ? "No se pudo enviar el mensaje."
        : null;

  return (
    <div className="panel flex h-[min(640px,75vh)] flex-col overflow-hidden">
      {/* Cabecera */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="grid h-8 w-8 place-items-center rounded-lg border border-electric-500/30 text-electric-300">
            <Chat className="h-4 w-4" />
          </div>
          <div>
            <p className="font-display text-sm font-semibold text-white">Chat con el repositorio</p>
            <p className="font-mono text-[11px] text-slate-500">respuestas con citas al código</p>
          </div>
        </div>
        <span className="hidden items-center gap-1.5 font-mono text-[11px] uppercase tracking-widest text-electric-400 sm:flex">
          <Sparkles className="h-3.5 w-3.5" /> RAG
        </span>
      </div>

      {/* Conversación */}
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
        {messages.length === 0 && (
          <div className="mx-auto max-w-md pt-6 text-center">
            <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl border border-white/[0.08] bg-ink-900 text-electric-300">
              <Chat className="h-6 w-6" />
            </div>
            <p className="text-sm text-slate-400">
              Pregúntale al repositorio en lenguaje natural. Las respuestas se basan en el
              código indexado y citan los archivos usados.
            </p>
            <div className="mt-5 flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  disabled={!sessionId}
                  className="rounded-lg border border-white/[0.08] bg-ink-850 px-3 py-2.5 text-left text-sm text-slate-300 transition-colors hover:border-electric-500/40 hover:text-white disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} repoUrl={repoUrl} commitSha={commitSha} />
        ))}

        {send.isPending && (
          <div className="flex items-center gap-2 font-mono text-xs text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-electric-400 animate-blink-soft" />
            pensando…
          </div>
        )}
        {sendError && <p className="text-sm text-red-400">{sendError}</p>}
      </div>

      {/* Entrada */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="border-t border-white/[0.06] p-3"
      >
        {sessionError ? (
          <p className="px-2 py-2 text-sm text-red-400">{sessionError}</p>
        ) : (
          <div className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-ink-900 p-1.5 focus-within:border-electric-500/50">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={sessionId ? "Pregunta algo sobre el código…" : "Iniciando chat…"}
              disabled={!sessionId || send.isPending}
              className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!sessionId || send.isPending || !input.trim()}
              className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-electric-500 text-white transition-colors hover:bg-electric-400 disabled:opacity-40"
              aria-label="Enviar"
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

function MessageBubble({
  message,
  repoUrl,
  commitSha,
}: {
  message: ChatMessage;
  repoUrl?: string | null;
  commitSha?: string | null;
}) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-electric-500/15 px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg border border-electric-500/30 text-electric-300">
        <Sparkles className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="prose-chat text-sm text-slate-200">
          <Markdown source={message.content} />
        </div>
        {message.citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {dedupeCitations(message.citations).map((c, i) => (
              <CitationChip key={i} citation={c} repoUrl={repoUrl} commitSha={commitSha} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CitationChip({
  citation,
  repoUrl,
  commitSha,
}: {
  citation: Citation;
  repoUrl?: string | null;
  commitSha?: string | null;
}) {
  const range = citation.line_start
    ? `:${citation.line_start}${citation.line_end ? `-${citation.line_end}` : ""}`
    : "";
  const label = `${citation.file_path}${range}`;
  const href = buildGithubLink(citation, repoUrl, commitSha);

  const inner = (
    <>
      <Code className="h-3 w-3 shrink-0" />
      <span className="truncate">{label}</span>
    </>
  );
  const cls =
    "inline-flex max-w-full items-center gap-1.5 rounded-md border border-white/[0.08] bg-ink-850 px-2 py-1 font-mono text-[11px] text-slate-400";

  return href ? (
    <a href={href} target="_blank" rel="noreferrer" className={`${cls} transition-colors hover:border-electric-500/40 hover:text-electric-200`}>
      {inner}
    </a>
  ) : (
    <span className={cls}>{inner}</span>
  );
}

function buildGithubLink(
  c: Citation,
  repoUrl?: string | null,
  commitSha?: string | null,
): string | undefined {
  if (!repoUrl) return undefined;
  const base = repoUrl.replace(/\.git$/, "").replace(/\/$/, "");
  const ref = commitSha || "HEAD";
  let url = `${base}/blob/${ref}/${c.file_path}`;
  if (c.line_start) url += `#L${c.line_start}${c.line_end ? `-L${c.line_end}` : ""}`;
  return url;
}

function dedupeCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  const out: Citation[] = [];
  for (const c of citations) {
    const key = `${c.file_path}:${c.line_start ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(c);
  }
  return out;
}

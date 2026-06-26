import { Fragment, type ReactNode } from "react";

/**
 * Renderizador Markdown mínimo y seguro (sin dependencias ni HTML embebido).
 * Soporta encabezados, listas, bloques de código, citas e inline (negrita,
 * código, enlaces). Suficiente para los README generados por la IA.
 */
export function Markdown({ source }: { source: string }) {
  return <div className="prose-invert space-y-3 text-sm leading-relaxed text-slate-200">{render(source)}</div>;
}

function render(source: string): ReactNode[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Bloque de código cercado.
    if (line.trim().startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        code.push(lines[i]);
        i++;
      }
      i++; // cierra ```
      blocks.push(
        <pre key={key++} className="overflow-auto rounded-lg bg-ink-950/60 p-4 font-mono text-xs text-slate-300">
          {code.join("\n")}
        </pre>,
      );
      continue;
    }

    // Encabezados.
    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const text = heading[2];
      const cls =
        level === 1
          ? "text-xl font-bold text-white"
          : level === 2
            ? "mt-4 text-lg font-bold text-white"
            : "mt-3 text-base font-semibold text-slate-100";
      blocks.push(
        <p key={key++} className={cls}>
          {inline(text)}
        </p>,
      );
      i++;
      continue;
    }

    // Listas (viñetas o numeradas).
    if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {
      const items: string[] = [];
      const ordered = /^\s*\d+\.\s+/.test(line);
      while (i < lines.length && /^\s*([-*+]|\d+\.)\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*+]|\d+\.)\s+/, ""));
        i++;
      }
      const ListTag = ordered ? "ol" : "ul";
      blocks.push(
        <ListTag
          key={key++}
          className={`space-y-1 pl-5 text-slate-300 ${ordered ? "list-decimal" : "list-disc"}`}
        >
          {items.map((it, idx) => (
            <li key={idx}>{inline(it)}</li>
          ))}
        </ListTag>,
      );
      continue;
    }

    // Cita.
    if (line.trim().startsWith(">")) {
      blocks.push(
        <blockquote key={key++} className="border-l-2 border-electric-400/40 pl-3 text-slate-400">
          {inline(line.replace(/^\s*>\s?/, ""))}
        </blockquote>,
      );
      i++;
      continue;
    }

    // Línea en blanco.
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Párrafo (acumula líneas consecutivas).
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trim().startsWith("```") &&
      !/^(#{1,6})\s+/.test(lines[i]) &&
      !/^\s*([-*+]|\d+\.)\s+/.test(lines[i]) &&
      !lines[i].trim().startsWith(">")
    ) {
      para.push(lines[i]);
      i++;
    }
    blocks.push(
      <p key={key++} className="text-slate-300">
        {inline(para.join(" "))}
      </p>,
    );
  }

  return blocks;
}

// Inline: **negrita**, `código`, [texto](url).
function inline(text: string): ReactNode {
  const tokens: ReactNode[] = [];
  const regex = /(\*\*([^*]+)\*\*)|(`([^`]+)`)|(\[([^\]]+)\]\(([^)]+)\))/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) tokens.push(<Fragment key={key++}>{text.slice(last, match.index)}</Fragment>);
    if (match[2]) {
      tokens.push(
        <strong key={key++} className="font-semibold text-white">
          {match[2]}
        </strong>,
      );
    } else if (match[4]) {
      tokens.push(
        <code key={key++} className="rounded bg-ink-950/60 px-1 py-0.5 font-mono text-xs text-electric-300">
          {match[4]}
        </code>,
      );
    } else if (match[6]) {
      tokens.push(
        <a key={key++} href={match[7]} target="_blank" rel="noreferrer" className="text-electric-300 hover:underline">
          {match[6]}
        </a>,
      );
    }
    last = regex.lastIndex;
  }
  if (last < text.length) tokens.push(<Fragment key={key++}>{text.slice(last)}</Fragment>);
  return tokens;
}

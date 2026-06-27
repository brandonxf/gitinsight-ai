"""Chunking para RAG (Fase 3): trocea el código en fragmentos coherentes.

Estrategia: para Python se chunkea por símbolos usando el `ast` de la stdlib
(funciones/clases de nivel superior + preámbulo del módulo). Para el resto de
lenguajes se usa una ventana por líneas. Cada unidad se reparte además en
sub-fragmentos si excede el tamaño objetivo, conservando el rango de líneas.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from app.analyzers.base import AnalysisContext
from app.core.logging import get_logger

logger = get_logger(__name__)

#: No se indexan archivos por encima de este tamaño (probablemente generados).
_MAX_FILE_BYTES = 200_000


@dataclass
class ChunkData:
    """Un fragmento listo para embeber y persistir."""

    file_path: str
    language: str | None
    symbol: str | None
    chunk_index: int
    line_start: int | None
    line_end: int | None
    content: str


def _pack_lines(
    lines: list[str], base_line: int, max_chars: int
) -> list[tuple[str, int, int]]:
    """Agrupa líneas en bloques de ~max_chars, devolviendo (texto, l_ini, l_fin)."""
    out: list[tuple[str, int, int]] = []
    buf: list[str] = []
    buf_start = base_line
    size = 0
    for i, line in enumerate(lines):
        line_no = base_line + i
        add = len(line) + 1
        if buf and size + add > max_chars:
            out.append(("\n".join(buf), buf_start, line_no - 1))
            buf, size, buf_start = [], 0, line_no
        buf.append(line)
        size += add
    if buf:
        out.append(("\n".join(buf), buf_start, base_line + len(lines) - 1))
    return out


def _python_units(source: str) -> list[tuple[str | None, int, int, str]] | None:
    """Unidades por símbolo para Python. None si el archivo no parsea."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    lines = source.splitlines()
    units: list[tuple[str | None, int, int, str]] = []
    covered: set[int] = set()

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        start = node.lineno
        if node.decorator_list:
            start = min(start, min(d.lineno for d in node.decorator_list))
        end = getattr(node, "end_lineno", node.lineno) or node.lineno
        units.append((node.name, start, end, "\n".join(lines[start - 1 : end])))
        covered.update(range(start, end + 1))

    leftover = [
        (i + 1, lines[i])
        for i in range(len(lines))
        if (i + 1) not in covered and lines[i].strip()
    ]
    if leftover:
        text = "\n".join(line for _, line in leftover)
        units.append((None, leftover[0][0], leftover[-1][0], text))

    units.sort(key=lambda u: u[1])
    return units


def build_chunks(
    context: AnalysisContext,
    *,
    max_files: int,
    max_chunks: int,
    max_chars: int,
) -> list[ChunkData]:
    """Construye los fragmentos a indexar a partir de los archivos del contexto."""
    files = sorted(
        (f for f in context.files if f.language and f.size_bytes <= _MAX_FILE_BYTES),
        key=lambda f: f.rel_path,
    )[:max_files]

    chunks: list[ChunkData] = []
    for f in files:
        try:
            source = f.abs_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not source.strip():
            continue

        units = _python_units(source) if f.language == "Python" else None
        if units is None:
            file_lines = source.splitlines()
            units = [(None, 1, len(file_lines), source)]

        ci = 0
        for symbol, ustart, _uend, text in units:
            for ctext, cstart, cend in _pack_lines(text.splitlines(), ustart, max_chars):
                if not ctext.strip():
                    continue
                chunks.append(
                    ChunkData(
                        file_path=f.rel_path,
                        language=f.language,
                        symbol=symbol,
                        chunk_index=ci,
                        line_start=cstart,
                        line_end=cend,
                        content=ctext,
                    )
                )
                ci += 1
                if len(chunks) >= max_chunks:
                    logger.info("ingest_rag.cap_reached", extra={"max_chunks": max_chunks})
                    return chunks
    return chunks

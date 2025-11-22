#!/usr/bin/env python
"""
Clasifica PDFs con gemini-flash-latest, define prefijos y genera un manifiesto para subir a S3.

Flujo:
1) Lee PDFs de --input-dir (no recursivo).
2) Llama a Gemini con un prompt corto para obtener topics y año.
3) Genera prefijo: papers/<topic>/<year|unknown_year>/hash_filename.pdf
4) Copia el archivo a --output-dir siguiendo el prefijo.
5) Escribe manifest.json con campos: s3_key, pdf_md5, original_path, target_path,
   title, topics, year, analysis_model, prompt_version.

Requisitos:
- GOOGLE_API_KEY en entorno.
- Opcionalmente, GEMINI_API_KEY.
- Este script carga automáticamente services/api/.env si existe.
- Paquete `google-genai` instalado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"
PROMPT_VERSION = "2025-01-24-prefetch"

PROMPT = """You are a fast classifier.
Given a PDF, return JSON with:
- topics: array of 1-2 short slugs (kebabcase), pick broad domains (nutrition, metabolism, diabetes, cardiovascular, sleep, exercise, mental_health, pdf_placeholder).
- year: publication year integer if you can infer it; else null.
- title: best effort title; empty string if unknown.
Rules: respond ONLY JSON."""


@dataclass
class FileRecord:
    s3_key: str
    pdf_md5: str
    original_path: str
    target_path: str
    title: str
    topics: List[str]
    year: Optional[int]
    analysis_model: str
    prompt_version: str


def load_env_files(additional: Optional[List[Path]] = None) -> list[Path]:
    """Carga variables de entorno desde archivos .env si no están definidas."""
    script_path = Path(__file__).resolve()
    parents = list(script_path.parents)
    default_candidates = []
    if len(parents) > 1:
        default_candidates.append(parents[1] / ".env")  # services/api/.env
    if len(parents) > 2:
        default_candidates.append(parents[2] / ".env")  # services/.env (si existe)
    if len(parents) > 3:
        default_candidates.append(parents[3] / ".env")  # raíz del repositorio
    default_candidates.append(Path.cwd() / ".env")  # cwd actual

    candidates: list[Path] = []
    if additional:
        candidates.extend(additional)
    candidates.extend(default_candidates)

    loaded: list[Path] = []
    seen: set[Path] = set()

    for candidate in candidates:
        candidate = candidate.expanduser()
        if candidate in seen:
            continue
        seen.add(candidate)

        if not candidate.exists() or not candidate.is_file():
            continue

        try:
            with candidate.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[len("export ") :].strip()
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    if not key:
                        continue
                    value = value.strip()
                    if value and value[0] in {"'", '"'} and value[-1] == value[0]:
                        value = value[1:-1]
                    if "#" in value and value.count('"') == 0 and value.count("'") == 0:
                        value = value.split("#", 1)[0].strip()
                    os.environ.setdefault(key, value)
            loaded.append(candidate)
        except OSError as exc:  # noqa: PERF203
            print(f"No se pudo leer {candidate}: {exc}")

    return loaded


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize(name: str) -> str:
    import re

    base = name.replace(" ", "_")
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return base.lower()


def wait_for_file_active(client: genai.Client, file_obj, timeout: int = 120, poll: float = 2.0):
    import time

    start = time.time()
    while time.time() - start < timeout:
        current = client.files.get(name=file_obj.name)
        if current.state.name == "ACTIVE":
            return current
        if current.state.name == "FAILED":
            raise RuntimeError(f"Procesamiento del PDF falló: {current.state}")
        time.sleep(poll)
    raise TimeoutError("Timeout esperando a que Gemini procese el PDF")


def classify_pdf(client: genai.Client, pdf_path: Path, model: str) -> dict:
    uploaded = client.files.upload(file=pdf_path, config={"mime_type": "application/pdf"})
    uploaded = wait_for_file_active(client, uploaded)

    file_part = types.Part(
        file_data=types.FileData(
            file_uri=uploaded.uri or uploaded.name,
            mime_type=uploaded.mime_type or "application/pdf",
        )
    )
    doc_content = types.Content(
        role="user",
        parts=[
            file_part,
            types.Part.from_text(text=PROMPT),
        ],
    )

    resp = client.models.generate_content(
        model=model,
        contents=[doc_content],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            max_output_tokens=512,
        ),
    )

    resp_text = getattr(resp, "text", None) or getattr(resp, "output_text", None)
    if not resp_text and getattr(resp, "candidates", None):
        content = resp.candidates[0].content if resp.candidates else None
        parts = content.parts if content else None
        if parts:
            for p in parts:
                if getattr(p, "text", None):
                    resp_text = p.text
                    break

    if not resp_text:
        debug = repr(resp)
        logger_msg = f"Gemini no retornó texto. Resp: {debug[:400]}"
        print(logger_msg)
        return {"topics": ["misc"], "year": None, "title": pdf_path.stem}

    try:
        data = json.loads(resp_text)
    except json.JSONDecodeError as exc:
        print(f"No JSON from Gemini: {exc}; raw={resp_text[:200]}")
        return {"topics": ["misc"], "year": None, "title": pdf_path.stem}

    # Normalizar
    topics = data.get("topics") or ["misc"]
    if isinstance(topics, str):
        topics = [topics]
    topics = [sanitize(t).replace(".", "_") for t in topics if t]
    if not topics:
        topics = ["misc"]
    year = data.get("year")
    if isinstance(year, str):
        year = int(year) if year.isdigit() else None
    title = data.get("title") or ""
    return {"topics": topics, "year": year, "title": title}


def build_s3_key(topics: List[str], year: Optional[int], pdf_md5: str, filename: str) -> str:
    topic = topics[0] if topics else "misc"
    year_part = str(year) if year else "unknown_year"
    return f"papers/{topic}/{year_part}/{pdf_md5[:8]}_{filename}"


def process_pdf(
    client: genai.Client,
    pdf_path: Path,
    output_dir: Path,
    model: str = DEFAULT_MODEL,
) -> FileRecord:
    info = classify_pdf(client, pdf_path, model)
    pdf_hash = md5_file(pdf_path)
    fname = sanitize(pdf_path.name)
    s3_key = build_s3_key(info["topics"], info["year"], pdf_hash, fname)

    target_path = output_dir / s3_key
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, target_path)

    return FileRecord(
        s3_key=s3_key,
        pdf_md5=pdf_hash,
        original_path=str(pdf_path),
        target_path=str(target_path),
        title=info["title"],
        topics=info["topics"],
        year=info["year"],
        analysis_model=model,
        prompt_version=PROMPT_VERSION,
    )


def run(input_dir: Path, output_dir: Path, model: str) -> list[FileRecord]:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Falta GOOGLE_API_KEY o GEMINI_API_KEY para usar Gemini")
    client = genai.Client(api_key=api_key)
    files = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])
    if not files:
        raise SystemExit(f"No se encontraron PDFs en {input_dir}")

    records: list[FileRecord] = []
    for idx, pdf in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Clasificando {pdf.name} ...")
        rec = process_pdf(client, pdf, output_dir, model)
        records.append(rec)
        print(f" -> {rec.s3_key}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Clasificar PDFs y generar manifiesto con prefijos S3.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Carpeta con PDFs de entrada.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Carpeta donde se copiarán con prefijos.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Modelo Gemini a usar (default {DEFAULT_MODEL}).")
    parser.add_argument(
        "--env-file",
        action="append",
        type=Path,
        help="Ruta(s) extra de archivos .env a cargar antes de ejecutar.",
    )
    args = parser.parse_args()

    loaded_envs = load_env_files(args.env_file)
    if loaded_envs:
        joined = ", ".join(str(p) for p in loaded_envs)
        print(f"Variables de entorno cargadas desde: {joined}")

    records = run(args.input_dir, args.output_dir, args.model)
    manifest_path = args.output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
    print(f"\nManifiesto escrito en {manifest_path}")
    print(f"Total archivos: {len(records)}")


if __name__ == "__main__":
    main()

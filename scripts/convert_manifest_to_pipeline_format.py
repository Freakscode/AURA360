#!/usr/bin/env python3
"""Convierte el manifest.json de Gemini Flash al formato esperado por el pipeline."""

import json
from pathlib import Path
from typing import Dict, List


# Mapeo de tópicos a categorías holísticas
TOPIC_TO_CATEGORY = {
    # Cuerpo
    "nutrition": "cuerpo",
    "exercise": "cuerpo",
    "metabolism": "cuerpo",
    "diabetes": "cuerpo",
    "gastroenterology": "cuerpo",
    "microbiome": "cuerpo",
    "sports-nutrition": "cuerpo",
    "exercise_physiology": "cuerpo",
    "food-safety": "cuerpo",

    # Mente
    "mental_health": "mente",
    "mental-health": "mente",
    "cognitive": "mente",
    "neuroscience": "mente",
    "psychology": "mente",

    # Alma
    "mindfulness": "alma",
    "meditation": "alma",
    "spirituality": "alma",

    # Misceláneo -> por defecto cuerpo (son papers de nutrición)
    "misc": "cuerpo",
}

# Mapeo de tópicos originales a tópicos biomédicos del sistema
TOPIC_MAPPING = {
    "nutrition": "nutrition",
    "exercise": "exercise_physiology",
    "metabolism": "metabolic_syndrome",
    "diabetes": "type2_diabetes",
    "gastroenterology": "gut_microbiome",
    "microbiome": "gut_microbiome",
    "mental_health": "mental_health",
    "mental-health": "mental_health",
    "food-safety": "nutrition",
    "sports-nutrition": "nutrition",
    "exercise_physiology": "exercise_physiology",
}


def convert_manifest_to_pipeline_format(
    manifest_path: Path,
    output_path: Path,
    base_papers_dir: Path
) -> None:
    """Convierte manifest.json al formato del pipeline."""

    # Leer manifest original
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    papers = []

    for i, entry in enumerate(manifest_data):
        # Extraer info del entry
        pdf_md5 = entry.get("pdf_md5", "")
        target_path = entry.get("target_path", "")
        title = entry.get("title", "Unknown Title")
        topics = entry.get("topics", ["misc"])
        year = entry.get("year")

        # Generar doc_id usando MD5
        doc_id = f"{pdf_md5[:8]}_{year or 'unknown'}"

        # Determinar filename relativo desde base_papers_dir
        if target_path:
            # Extraer solo la parte después de "papers/"
            parts = target_path.split("papers/")
            if len(parts) > 1:
                filename = parts[1]
            else:
                filename = Path(target_path).name
        else:
            filename = f"paper_{i}.pdf"

        # Determinar categoría principal basada en el primer tópico
        primary_topic = topics[0] if topics else "misc"
        category = TOPIC_TO_CATEGORY.get(primary_topic, "cuerpo")

        # Mapear tópicos al sistema biomédico
        mapped_topics = []
        for topic in topics:
            mapped = TOPIC_MAPPING.get(topic, topic)
            if mapped and mapped not in mapped_topics:
                mapped_topics.append(mapped)

        # Si no hay tópicos mapeados, usar nutrition como default
        if not mapped_topics:
            mapped_topics = ["nutrition"]

        # Crear entry para el pipeline
        paper_entry = {
            "doc_id": doc_id,
            "filename": filename,
            "category": category,
            "topics": mapped_topics,
            "confidence_score": 0.95,  # Asumimos alta confianza de Gemini
            "title": title,
            "year": year,
            "tags": [f"gemini-flash", f"prompt-2025-01-24"],
            "metadata": {
                "original_md5": pdf_md5,
                "analysis_model": entry.get("analysis_model", "gemini-2.5-flash"),
                "prompt_version": entry.get("prompt_version", "2025-01-24-prefetch"),
                "s3_key": entry.get("s3_key"),
            }
        }

        papers.append(paper_entry)

    # Guardar formato del pipeline
    pipeline_data = {
        "papers": papers,
        "metadata": {
            "source": "gemini-2.5-flash",
            "conversion_date": "2025-01-22",
            "total_papers": len(papers),
            "original_manifest": str(manifest_path),
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Convertidos {len(papers)} papers")
    print(f"📄 Guardado en: {output_path}")

    # Mostrar distribución por categoría
    from collections import Counter
    category_dist = Counter(p["category"] for p in papers)
    print(f"\n📊 Distribución por categoría:")
    for category, count in category_dist.items():
        print(f"   {category}: {count} papers")

    # Mostrar top tópicos
    topic_dist = Counter()
    for p in papers:
        topic_dist.update(p["topics"])

    print(f"\n🏷️  Top 5 tópicos:")
    for topic, count in topic_dist.most_common(5):
        print(f"   {topic}: {count} papers")


if __name__ == "__main__":
    import sys

    # Paths
    manifest_path = Path("/Users/freakscode/Proyectos/AURA360/tmp/output_refs_flash/manifest.json")
    output_path = Path("/Users/freakscode/Proyectos/AURA360/tmp/output_refs_flash/categorization_pipeline.json")
    base_papers_dir = Path("/Users/freakscode/Proyectos/AURA360/tmp/output_refs_flash/papers")

    if not manifest_path.exists():
        print(f"❌ Manifest no encontrado: {manifest_path}")
        sys.exit(1)

    convert_manifest_to_pipeline_format(manifest_path, output_path, base_papers_dir)
    print(f"\n✅ Listo! Ahora puedes ejecutar el pipeline con:")
    print(f"   python unified_paper_pipeline.py --config config/refs_flash_config.yaml")

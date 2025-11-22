#!/usr/bin/env python3
"""Pipeline unificado de validación, upload a GCS e ingesta a Qdrant para papers categorizados.

Este script integra todo el flujo de procesamiento de papers:
1. Carga papers locales + JSON de categorización
2. Validación interactiva/automática/skip
3. Upload a GCS/S3 con metadata
4. Ingesta a Qdrant via servicio vectordb
5. Generación de reportes consolidados

Uso:
    python unified_paper_pipeline.py --config config/pipeline_config.yaml
    python unified_paper_pipeline.py --config config/pipeline_config.yaml --dry-run
    python unified_paper_pipeline.py --config config/pipeline_config.yaml --validation-mode auto
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

# Importar componentes del pipeline
from paper_validation.cloud_uploader import CloudUploader
from paper_validation.models import (
    HolisticCategory,
    PaperEntry,
    PaperMetadata,
    PipelineConfig,
    ValidationMode,
)
from paper_validation.qdrant_ingester import run_ingestion
from paper_validation.reporter import ReportGenerator
from paper_validation.validator import InteractiveValidator


class UnifiedPaperPipeline:
    """Pipeline unificado para procesar papers categorizados."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configura logging del pipeline."""
        logger = logging.getLogger("paper_pipeline")
        logger.setLevel(getattr(logging, self.config.log_level))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (opcional)
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def run(self) -> None:
        """Ejecuta el pipeline completo."""
        self.logger.info(f"Iniciando pipeline: {self.run_id}")

        print(f"\n{'━' * 60}")
        print("🔍 AURA360 - Pipeline Unificado de Papers")
        print(f"{'━' * 60}\n")

        try:
            # Fase 1: Cargar papers
            papers = self._load_papers()
            if not papers:
                self.logger.error("No se encontraron papers para procesar")
                return

            print(f"✅ Encontrados: {len(papers)} papers con categorización\n")

            # Fase 2: Validación
            validator = InteractiveValidator(
                mode=self.config.validation_mode,
                auto_threshold=self.config.auto_approve_threshold
            )
            validated_papers = validator.validate_papers(papers)

            if not validated_papers:
                self.logger.warning("No hay papers validados para continuar")
                return

            validation_results = validator.get_results()

            # Fase 3: Upload a cloud storage
            upload_results = []
            if not self.config.skip_upload:
                uploader = CloudUploader(
                    provider=self.config.cloud_provider,
                    bucket=self.config.gcs_bucket or self.config.s3_bucket,
                    project=self.config.gcs_project,
                    region=self.config.s3_region,
                    dry_run=self.config.dry_run
                )
                upload_results = uploader.upload_papers(validated_papers)

                # Verificar uploads
                if not self.config.dry_run:
                    uploader.verify_uploads(validated_papers)
            else:
                self.logger.info("⏭️  Saltando fase de upload (skip_upload=True)")

            # Fase 4: Ingesta a Qdrant
            ingestion_results = []
            if not self.config.skip_ingestion:
                ingestion_results = asyncio.run(self._run_ingestion_phase(validated_papers))
            else:
                self.logger.info("⏭️  Saltando fase de ingesta (skip_ingestion=True)")

            # Fase 5: Generar reporte
            self._generate_final_report(
                papers,
                validation_results,
                upload_results,
                ingestion_results
            )

        except KeyboardInterrupt:
            self.logger.warning("\n⚠️  Pipeline interrumpido por el usuario")
            sys.exit(1)

        except Exception as e:
            self.logger.error(f"❌ Error en pipeline: {e}", exc_info=True)
            sys.exit(1)

    def _load_papers(self) -> List[PaperEntry]:
        """Carga papers desde JSON de categorización."""
        self.logger.info(f"Cargando papers desde: {self.config.categorization_file}")

        print(f"📂 Cargando papers desde: {self.config.local_papers_dir}")
        print(f"📋 Categorización desde: {self.config.categorization_file}\n")

        # Leer JSON de categorización
        with open(self.config.categorization_file, "r", encoding="utf-8") as f:
            categorization_data = json.load(f)

        papers = []

        # El JSON puede ser un array o un objeto con una key "papers"
        if isinstance(categorization_data, list):
            entries = categorization_data
        elif isinstance(categorization_data, dict) and "papers" in categorization_data:
            entries = categorization_data["papers"]
        else:
            entries = [categorization_data]  # Single entry

        for entry in entries:
            try:
                paper = self._parse_paper_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as e:
                self.logger.warning(f"Error parseando entry: {e}")
                continue

        return papers

    def _parse_paper_entry(self, entry: dict) -> PaperEntry | None:
        """Parsea una entrada de paper desde JSON."""
        # Validar campos requeridos
        if "doc_id" not in entry or "filename" not in entry:
            self.logger.warning(f"Entry sin doc_id o filename: {entry}")
            return None

        # Construir path local
        filename = entry["filename"]
        local_path = self.config.local_papers_dir / filename

        if not local_path.exists():
            self.logger.warning(f"Archivo no encontrado: {local_path}")
            # Continuar sin local_path (útil para testing)

        # Parsear categoría
        category_str = entry.get("category", "mente")
        try:
            category = HolisticCategory(category_str)
        except ValueError:
            self.logger.warning(f"Categoría inválida: {category_str}, usando 'mente'")
            category = HolisticCategory.MIND

        # Parsear metadata
        metadata = PaperMetadata(
            title=entry.get("title"),
            authors=entry.get("authors", []),
            journal=entry.get("journal"),
            year=entry.get("year"),
            doi=entry.get("doi"),
            abstract=entry.get("abstract"),
            url=entry.get("url"),
            tags=entry.get("tags", []),
            mesh_terms=entry.get("mesh_terms", []),
        )

        paper = PaperEntry(
            doc_id=entry["doc_id"],
            filename=filename,
            local_path=local_path if local_path.exists() else None,
            category=category,
            topics=entry.get("topics", []),
            confidence_score=entry.get("confidence_score"),
            metadata=metadata,
        )

        return paper

    async def _run_ingestion_phase(self, papers: List[PaperEntry]) -> list:
        """Ejecuta fase de ingesta de forma asíncrona."""
        config_dict = {
            "vectordb_api_url": self.config.vectordb_api_url,
            "qdrant_collection": self.config.qdrant_collection,
            "batch_size": self.config.batch_size,
            "dry_run": self.config.dry_run,
        }

        return await run_ingestion(papers, config_dict)

    def _generate_final_report(
        self,
        papers: List[PaperEntry],
        validation_results: list,
        upload_results: list,
        ingestion_results: list,
    ) -> None:
        """Genera y guarda reporte final."""
        reporter = ReportGenerator(self.run_id)

        report = reporter.generate_report(
            papers=papers,
            validation_results=validation_results,
            upload_results=upload_results,
            ingestion_results=ingestion_results,
            config=self.config.model_dump(mode="json"),
        )

        # Imprimir resumen en consola
        reporter.print_summary(report)

        # Guardar reportes en disco
        output_dir = Path.cwd() / "pipeline_reports"
        md_path, json_path = reporter.save_report(report, output_dir)

        print(f"📄 Reporte Markdown: {md_path}")
        print(f"📄 Reporte JSON: {json_path}\n")

        self.logger.info(f"Pipeline completado: {self.run_id}")


def load_config(config_path: Path, overrides: dict = None) -> PipelineConfig:
    """Carga configuración desde YAML con overrides opcionales."""
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Aplicar overrides de CLI
    if overrides:
        config_data.update(overrides)

    return PipelineConfig(**config_data)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Pipeline unificado de validación, upload e ingesta de papers"
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Ruta al archivo de configuración YAML"
    )

    parser.add_argument(
        "--validation-mode",
        type=str,
        choices=["interactive", "auto", "skip"],
        help="Modo de validación (override config)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        help="Umbral de confianza para auto-aprobación (override config)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo de prueba sin cambios reales"
    )

    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Saltar fase de upload"
    )

    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Saltar fase de ingesta"
    )

    args = parser.parse_args()

    # Validar que config existe
    if not args.config.exists():
        print(f"❌ Archivo de configuración no encontrado: {args.config}")
        sys.exit(1)

    # Preparar overrides
    overrides = {}
    if args.validation_mode:
        overrides["validation_mode"] = args.validation_mode
    if args.threshold is not None:
        overrides["auto_approve_threshold"] = args.threshold
    if args.dry_run:
        overrides["dry_run"] = True
    if args.skip_upload:
        overrides["skip_upload"] = True
    if args.skip_ingestion:
        overrides["skip_ingestion"] = True

    # Cargar configuración
    try:
        config = load_config(args.config, overrides)
        config.validate_config()
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        sys.exit(1)

    # Ejecutar pipeline
    pipeline = UnifiedPaperPipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()

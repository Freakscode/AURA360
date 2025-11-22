"""Generador de reportes del pipeline de validación."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

from .models import (
    IngestionResult,
    PaperEntry,
    PipelineReport,
    UploadResult,
    ValidationResult,
)


class ReportGenerator:
    """Generador de reportes consolidados del pipeline."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.start_time = datetime.now()

    def generate_report(
        self,
        papers: List[PaperEntry],
        validation_results: List[ValidationResult],
        upload_results: List[UploadResult],
        ingestion_results: List[IngestionResult],
        config: dict,
    ) -> PipelineReport:
        """Genera reporte consolidado del pipeline."""

        # Estadísticas de validación
        validation_stats = self._compute_validation_stats(validation_results)

        # Estadísticas de upload
        upload_stats = self._compute_upload_stats(upload_results)

        # Estadísticas de ingesta
        ingestion_stats = self._compute_ingestion_stats(ingestion_results)

        # Distribuciones
        category_dist = self._compute_category_distribution(papers)
        topic_dist = self._compute_topic_distribution(papers)

        # Recolectar errores
        errors = self._collect_errors(papers, upload_results, ingestion_results)

        report = PipelineReport(
            run_id=self.run_id,
            start_time=self.start_time,
            end_time=datetime.now(),
            config_used=config,
            total_papers=len(papers),
            validated_manually=validation_stats["manual"],
            auto_approved=validation_stats["auto"],
            modified=validation_stats["modified"],
            rejected=validation_stats["rejected"],
            skipped=validation_stats["skipped"],
            upload_success=upload_stats["success"],
            upload_failed=upload_stats["failed"],
            ingestion_success=ingestion_stats["success"],
            ingestion_failed=ingestion_stats["failed"],
            total_chunks=ingestion_stats["total_chunks"],
            category_distribution=category_dist,
            topic_distribution=topic_dist,
            validation_results=validation_results,
            upload_results=upload_results,
            ingestion_results=ingestion_results,
            errors=errors,
        )

        return report

    def save_report(
        self,
        report: PipelineReport,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Guarda reporte en formato Markdown y JSON."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar Markdown
        md_path = output_dir / f"validation_report_{timestamp}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())

        # Guardar JSON
        json_path = output_dir / f"validation_report_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        return md_path, json_path

    def _compute_validation_stats(self, results: List[ValidationResult]) -> dict:
        """Calcula estadísticas de validación."""
        stats = {
            "manual": sum(1 for r in results if r.action == "validated" and not r.paper.modified),
            "auto": sum(1 for r in results if r.action == "validated" and r.paper.confidence_score and r.paper.confidence_score >= 0.90),
            "modified": sum(1 for r in results if r.action == "modified"),
            "rejected": sum(1 for r in results if r.action == "rejected"),
            "skipped": sum(1 for r in results if r.action == "skipped"),
        }
        return stats

    def _compute_upload_stats(self, results: List[UploadResult]) -> dict:
        """Calcula estadísticas de upload."""
        stats = {
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
        }
        return stats

    def _compute_ingestion_stats(self, results: List[IngestionResult]) -> dict:
        """Calcula estadísticas de ingesta."""
        stats = {
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "total_chunks": sum(r.chunks_processed for r in results if r.success),
        }
        return stats

    def _compute_category_distribution(self, papers: List[PaperEntry]) -> dict:
        """Calcula distribución por categoría."""
        categories = [p.category.value for p in papers if p.validated]
        return dict(Counter(categories))

    def _compute_topic_distribution(self, papers: List[PaperEntry]) -> dict:
        """Calcula distribución por tópico."""
        topics = []
        for p in papers:
            if p.validated:
                topics.extend(p.topics)
        return dict(Counter(topics))

    def _collect_errors(
        self,
        papers: List[PaperEntry],
        upload_results: List[UploadResult],
        ingestion_results: List[IngestionResult],
    ) -> List[str]:
        """Recolecta todos los errores encontrados."""
        errors = []

        # Errores de papers
        for paper in papers:
            if paper.error_message:
                errors.append(f"[{paper.doc_id}] {paper.error_message}")

        # Errores de upload
        for result in upload_results:
            if not result.success and result.error_message:
                errors.append(f"[Upload:{result.doc_id}] {result.error_message}")

        # Errores de ingesta
        for result in ingestion_results:
            if not result.success and result.error_message:
                errors.append(f"[Ingestion:{result.doc_id}] {result.error_message}")

        return errors

    def print_summary(self, report: PipelineReport) -> None:
        """Imprime resumen del reporte en consola."""
        print(f"\n{'━' * 60}")
        print("REPORTE FINAL")
        print(f"{'━' * 60}\n")

        print(f"📋 Run ID: {report.run_id}")
        print(f"⏱️  Duración: {report.duration_seconds:.1f}s ({report.duration_seconds/60:.1f}min)\n")

        print("📊 RESUMEN:")
        print(f"   Total papers: {report.total_papers}")
        print(f"   ✅ Validados: {report.validated_manually + report.auto_approved}")
        print(f"   ✏️  Modificados: {report.modified}")
        print(f"   ❌ Rechazados: {report.rejected}\n")

        print("☁️  CLOUD STORAGE:")
        print(f"   ✅ Subidos: {report.upload_success}")
        print(f"   ❌ Fallos: {report.upload_failed}\n")

        print("🔍 QDRANT:")
        print(f"   ✅ Ingestados: {report.ingestion_success}")
        print(f"   ❌ Fallos: {report.ingestion_failed}")
        print(f"   📦 Total chunks: {report.total_chunks}\n")

        print("🏷️  DISTRIBUCIÓN POR CATEGORÍA:")
        for category, count in sorted(report.category_distribution.items()):
            emoji = {"mente": "🧠", "cuerpo": "💪", "alma": "✨"}.get(category, "📋")
            print(f"   {emoji} {category}: {count} papers")

        print("\n🏷️  TOP 5 TÓPICOS:")
        sorted_topics = sorted(report.topic_distribution.items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:5]:
            print(f"   • {topic}: {count} papers")

        if report.errors:
            print(f"\n⚠️  ERRORES ({len(report.errors)}):")
            for error in report.errors[:5]:
                print(f"   • {error}")
            if len(report.errors) > 5:
                print(f"   ... y {len(report.errors) - 5} más (ver reporte completo)")

        print(f"\n{'━' * 60}\n")

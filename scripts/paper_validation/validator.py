"""Validador interactivo de categorización de papers."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import List, Optional

from .models import (
    HolisticCategory,
    PaperEntry,
    ValidationMode,
    ValidationResult,
)


class InteractiveValidator:
    """Validador interactivo de papers con CLI."""

    def __init__(self, mode: ValidationMode, auto_threshold: float = 0.90):
        self.mode = mode
        self.auto_threshold = auto_threshold
        self.results: List[ValidationResult] = []
        self.auto_approve_remaining = False

    def validate_papers(self, papers: List[PaperEntry]) -> List[PaperEntry]:
        """Valida lista de papers según el modo configurado."""
        validated_papers = []

        print(f"\n{'━' * 60}")
        print(f"FASE 1: VALIDACIÓN ({self.mode.value.upper()})")
        print(f"{'━' * 60}\n")

        for i, paper in enumerate(papers, 1):
            if self.mode == ValidationMode.SKIP:
                # Skip: marcar como validado sin revisar
                paper.validated = True
                paper.status = "validated"
                validated_papers.append(paper)
                self._add_result(paper, "skipped")
                continue

            if self.mode == ValidationMode.AUTO or self.auto_approve_remaining:
                # Auto: aprobar si confidence > threshold
                if paper.confidence_score and paper.confidence_score >= self.auto_threshold:
                    paper.validated = True
                    paper.status = "validated"
                    paper.validation_timestamp = datetime.now()
                    validated_papers.append(paper)
                    self._add_result(paper, "validated")
                    print(f"✅ Auto-aprobado ({i}/{len(papers)}): {paper.filename}")
                    continue

            # Modo interactivo o papers que no cumplen threshold
            action = self._validate_single_paper(paper, i, len(papers))

            if action == "validated":
                paper.validated = True
                paper.status = "validated"
                paper.validation_timestamp = datetime.now()
                validated_papers.append(paper)
                self._add_result(paper, "validated")

            elif action == "modified":
                paper.validated = True
                paper.modified = True
                paper.status = "validated"
                paper.validation_timestamp = datetime.now()
                validated_papers.append(paper)
                self._add_result(paper, "modified")

            elif action == "rejected":
                paper.status = "rejected"
                self._add_result(paper, "rejected")

            elif action == "auto_rest":
                # Auto-aprobar el resto
                paper.validated = True
                paper.status = "validated"
                paper.validation_timestamp = datetime.now()
                validated_papers.append(paper)
                self._add_result(paper, "validated")
                self.auto_approve_remaining = True
                print(f"\n🤖 Auto-aprobando papers restantes con confidence >= {self.auto_threshold}...\n")

            elif action == "quit":
                print("\n⚠️  Validación interrumpida por el usuario.")
                break

        print(f"\n✅ Validación completada: {len(validated_papers)}/{len(papers)} papers aprobados\n")
        return validated_papers

    def _validate_single_paper(self, paper: PaperEntry, current: int, total: int) -> str:
        """Valida un paper individual de forma interactiva."""
        self._print_paper_info(paper, current, total)

        while True:
            print("\nOpciones:")
            print("[V] Validar   [M] Modificar   [R] Rechazar   [S] Skip   [A] Auto resto   [Q] Salir")
            choice = input("> ").strip().lower()

            if choice == "v":
                print(f"✅ Paper validado ({current}/{total})\n")
                return "validated"

            elif choice == "m":
                self._modify_paper(paper)
                print(f"✏️  Paper modificado y validado ({current}/{total})\n")
                return "modified"

            elif choice == "r":
                reason = input("Motivo del rechazo (opcional): ").strip()
                paper.error_message = reason or "Rechazado por el usuario"
                print(f"❌ Paper rechazado ({current}/{total})\n")
                return "rejected"

            elif choice == "s":
                print(f"⏭️  Paper omitido ({current}/{total})\n")
                return "rejected"

            elif choice == "a":
                return "auto_rest"

            elif choice == "q":
                confirm = input("¿Confirmar salida? [y/N]: ").strip().lower()
                if confirm == "y":
                    return "quit"

            else:
                print("❌ Opción inválida. Intenta de nuevo.")

    def _print_paper_info(self, paper: PaperEntry, current: int, total: int) -> None:
        """Imprime información del paper de forma legible."""
        print(f"\n{'─' * 60}")
        print(f"Paper {current}/{total}: {paper.filename}")
        print(f"{'─' * 60}")

        # Metadata
        if paper.metadata.title:
            print(f"📄 Título: {paper.metadata.title}")
        if paper.metadata.authors:
            authors_str = ", ".join(paper.metadata.authors[:3])
            if len(paper.metadata.authors) > 3:
                authors_str += f" +{len(paper.metadata.authors) - 3} más"
            print(f"✍️  Autores: {authors_str}")
        if paper.metadata.journal:
            print(f"📚 Journal: {paper.metadata.journal}")
        if paper.metadata.year:
            print(f"📅 Año: {paper.metadata.year}")

        # Categorización
        print(f"\nCategorización actual:")

        category_emoji = {
            "mente": "🧠",
            "cuerpo": "💪",
            "alma": "✨"
        }
        emoji = category_emoji.get(paper.category.value, "📋")
        print(f"  {emoji} Categoría: {paper.category.value}")

        if paper.topics:
            topics_str = ", ".join(paper.topics[:5])
            if len(paper.topics) > 5:
                topics_str += f" +{len(paper.topics) - 5} más"
            print(f"  🏷️  Tópicos: [{topics_str}]")

        if paper.confidence_score is not None:
            confidence_bar = "█" * int(paper.confidence_score * 10) + "░" * (10 - int(paper.confidence_score * 10))
            print(f"  📊 Confianza: {confidence_bar} {paper.confidence_score:.2f}")

        if paper.metadata.abstract:
            abstract_preview = paper.metadata.abstract[:200]
            if len(paper.metadata.abstract) > 200:
                abstract_preview += "..."
            print(f"\n📝 Abstract: {abstract_preview}")

    def _modify_paper(self, paper: PaperEntry) -> None:
        """Permite modificar la categorización de un paper."""
        print("\n📝 Modificando categorización...\n")

        # Modificar categoría
        print(f"Categoría actual: {paper.category.value}")
        print("Nueva categoría [mente/cuerpo/alma] (Enter para mantener):")
        new_category = input("> ").strip().lower()

        if new_category in ["mente", "cuerpo", "alma"]:
            paper.category = HolisticCategory(new_category)
            print(f"✅ Categoría actualizada a: {new_category}")

        # Modificar tópicos
        print(f"\nTópicos actuales: {', '.join(paper.topics)}")
        print("Nuevos tópicos (separados por coma, Enter para mantener):")
        new_topics = input("> ").strip()

        if new_topics:
            paper.topics = [t.strip() for t in new_topics.split(",") if t.strip()]
            print(f"✅ Tópicos actualizados: {', '.join(paper.topics)}")

        # Notas adicionales
        print("\nNotas adicionales (opcional):")
        notes = input("> ").strip()
        if notes:
            if not paper.metadata.tags:
                paper.metadata.tags = []
            paper.metadata.tags.append(f"validation_note: {notes}")

    def _add_result(self, paper: PaperEntry, action: str) -> None:
        """Registra el resultado de validación."""
        result = ValidationResult(
            paper=paper,
            action=action,
            original_category=paper.category,
            original_topics=paper.topics.copy(),
            timestamp=datetime.now()
        )
        self.results.append(result)

    def get_results(self) -> List[ValidationResult]:
        """Retorna los resultados de validación."""
        return self.results

    def get_statistics(self) -> dict:
        """Retorna estadísticas de validación."""
        stats = {
            "total": len(self.results),
            "validated": sum(1 for r in self.results if r.action == "validated"),
            "modified": sum(1 for r in self.results if r.action == "modified"),
            "rejected": sum(1 for r in self.results if r.action == "rejected"),
            "skipped": sum(1 for r in self.results if r.action == "skipped"),
        }
        return stats

"""Mapper service to convert Gemini extraction to Django backend format."""

import logging
from datetime import datetime
from typing import Any, Optional

from ..models.nutrition_plan import NutritionPlan

logger = logging.getLogger(__name__)


class DjangoMapperError(Exception):
    """Error during mapping to Django format."""


class DjangoMapper:
    """Maps Gemini extraction results to Django backend nutrition plan format."""

    @staticmethod
    def map_to_django_format(
        extraction: NutritionPlan,
        auth_user_id: str,
        job_id: str,
        source_uri: str,
        title: Optional[str] = None,
    ) -> dict[str, Any]:
        """Map Gemini extraction to Django nutrition plan format.

        Args:
            extraction: Gemini extraction result
            auth_user_id: User UUID from Supabase
            job_id: Job ID for tracking
            source_uri: URI of the source PDF
            title: Optional title for the plan

        Returns:
            Dictionary in Django backend format
        """
        try:
            # Build plan_data structure
            plan_data = {
                "plan": DjangoMapper._build_plan_section(extraction, source_uri),
                "subject": DjangoMapper._build_subject_section(extraction, auth_user_id),
                "assessment": DjangoMapper._build_assessment_section(extraction),
                "directives": DjangoMapper._build_directives_section(extraction),
                "supplements": DjangoMapper._build_supplements_section(extraction),
                "recommendations": [],  # TODO: Extract from notes if available
                "activity_guidance": extraction.notes or "",
                "free_text": {
                    "diagnosis_raw": "",
                    "instructions_raw": extraction.notes or "",
                    "notes_raw": extraction.notes or "",
                },
            }

            # Build callback payload
            payload = {
                "job_id": job_id,
                "auth_user_id": auth_user_id,
                "title": title or f"Plan Nutricional - {extraction.metadata.patient_name or 'Sin nombre'}",
                "language": "es",
                "issued_at": extraction.metadata.issue_date,
                "valid_until": extraction.metadata.valid_until,
                "is_active": True,
                "plan_data": plan_data,
                "metadata": {
                    "extraction_version": "gemini-2.0-flash",
                    "extracted_at": datetime.utcnow().isoformat(),
                    "pdf_filename": source_uri.split("/")[-1] if "/" in source_uri else source_uri,
                },
                "source": {
                    "kind": "pdf",
                    "uri": source_uri,
                    "extracted_at": datetime.utcnow().isoformat(),
                },
                "extractor": {
                    "name": "gemini-pdf-extraction-service",
                    "version": "0.2.0",
                    "model": "gemini-2.0-flash-exp",
                },
            }

            logger.info(f"Successfully mapped extraction to Django format for user {auth_user_id}")
            return payload

        except Exception as e:
            logger.error(f"Failed to map extraction to Django format: {e}", exc_info=True)
            raise DjangoMapperError(f"Mapping failed: {e}") from e

    @staticmethod
    def _build_plan_section(extraction: NutritionPlan, source_uri: str) -> dict[str, Any]:
        """Build plan section."""
        return {
            "title": f"Plan Nutricional - {extraction.metadata.patient_name or 'Sin nombre'}",
            "version": "1.0",
            "issued_at": extraction.metadata.issue_date,
            "valid_until": extraction.metadata.valid_until,
            "language": "es",
            "units": {"mass": "g", "volume": "ml", "energy": "kcal"},
            "source": {
                "kind": "pdf",
                "uri": source_uri,
                "extracted_at": datetime.utcnow().isoformat(),
                "extractor": "gemini-2.0-flash-exp",
            },
        }

    @staticmethod
    def _build_subject_section(extraction: NutritionPlan, auth_user_id: str) -> dict[str, Any]:
        """Build subject section."""
        # Calculate age from height/weight if BMI is present
        age_years = None
        sex = None  # Not available in extraction

        return {
            "user_id": auth_user_id,
            "name": extraction.metadata.patient_name or "Sin nombre",
            "demographics": {
                "sex": sex,
                "age_years": age_years,
                "height_cm": extraction.body_composition.height_cm,
                "weight_kg": extraction.body_composition.weight_kg,
            },
        }

    @staticmethod
    def _build_assessment_section(extraction: NutritionPlan) -> dict[str, Any]:
        """Build assessment section."""
        timeseries = []
        if extraction.body_composition.bmi or extraction.body_composition.body_fat_percentage:
            metrics = {}
            if extraction.body_composition.body_fat_percentage:
                metrics["fat_percent"] = extraction.body_composition.body_fat_percentage
            if extraction.body_composition.muscle_mass_kg:
                metrics["muscle_mass_kg"] = extraction.body_composition.muscle_mass_kg
            if extraction.body_composition.bone_mass_kg:
                metrics["bone_mass_kg"] = extraction.body_composition.bone_mass_kg

            timeseries.append({
                "date": extraction.metadata.issue_date or datetime.utcnow().date().isoformat(),
                "metrics": metrics,
                "method_notes": "Extracción desde PDF",
            })

        # Build diagnosis from BMI if available
        diagnoses = []
        if extraction.body_composition.bmi:
            bmi = extraction.body_composition.bmi
            if bmi >= 30:
                severity = "alto" if bmi >= 35 else "moderado"
                diagnoses.append({
                    "label": f"Obesidad (IMC {bmi})",
                    "severity": severity,
                    "notes": f"IMC: {bmi} kg/m²",
                })
            elif bmi >= 25:
                diagnoses.append({
                    "label": f"Sobrepeso (IMC {bmi})",
                    "severity": "bajo",
                    "notes": f"IMC: {bmi} kg/m²",
                })

        return {
            "timeseries": timeseries,
            "diagnoses": diagnoses,
            "goals": [],  # TODO: Extract from notes if available
        }

    @staticmethod
    def _build_directives_section(extraction: NutritionPlan) -> dict[str, Any]:
        """Build directives section."""
        # Build meals
        meals = []
        for meal in extraction.meals:
            components = []

            # Add components for each exchange type
            exchanges = meal.exchanges.model_dump()
            for group_key, quantity in exchanges.items():
                if quantity > 0:
                    group_name = DjangoMapper._map_exchange_group_name(group_key)
                    components.append({
                        "group": group_name,
                        "quantity": {"portions": quantity, "notes": None},
                        "must_present": True,
                    })

            meals.append({
                "name": meal.name,
                "time_window": meal.time or "Sin horario",
                "components": components,
                "notes": meal.notes,
            })

        # Build substitutions (exchange tables)
        substitutions = []
        for table in extraction.exchange_tables:
            items = []
            for item in table.items:
                # Parse grams (may be string like "90" or "90g")
                try:
                    grams = float(item.grams.replace("g", "").strip()) if isinstance(item.grams, str) else item.grams
                except (ValueError, AttributeError):
                    grams = None

                items.append({
                    "name": item.food,
                    "grams": grams,
                    "portion_equiv": 1.0,  # Assume 1 portion
                    "notes": item.portion if item.portion != "string" else None,
                })

            substitutions.append({
                "group": table.category,
                "items": items,
            })

        return {
            "weekly_frequency": {
                "min_days_per_week": 5,  # Default value
                "notes": "Seguir el plan diariamente",
            },
            "conditional_allowances": [],
            "restrictions": [],  # TODO: Extract from notes
            "meals": meals,
            "substitutions": substitutions,
        }

    @staticmethod
    def _build_supplements_section(extraction: NutritionPlan) -> list[dict[str, Any]]:
        """Build supplements section."""
        # TODO: Extract supplements from notes if available
        return []

    @staticmethod
    def _map_exchange_group_name(group_key: str) -> str:
        """Map exchange group key to display name."""
        mapping = {
            "harinas": "Harinas",
            "carnes": "Carnes",
            "grasas": "Grasas",
            "verduras": "Verduras",
            "lacteos": "Lácteos",
            "frutas": "Frutas",
            "azucares": "Azúcares",
        }
        return mapping.get(group_key, group_key.capitalize())

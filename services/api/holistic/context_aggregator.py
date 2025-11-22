"""Servicio de agregación de contexto de usuario para RAG personalizado."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Avg, Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

__all__ = ["UserContextAggregator"]


class UserContextAggregator:
    """Agrega datos del usuario en snapshots consolidados listos para embedding.

    Este servicio consulta datos de diferentes módulos (mind, body, soul) y los
    consolida en texto estructurado optimizado para vectorización.
    """

    def aggregate_mind_context(
        self,
        user_id: str,
        timeframe: str = "7d",
    ) -> dict[str, Any]:
        """Agrega contexto mental: mood entries, tags, notas.

        Args:
            user_id: UUID del usuario en auth.users
            timeframe: Ventana temporal ("7d", "30d", "90d")

        Returns:
            Dict con "text" (consolidated) y "metadata" (stats)
        """
        from holistic.models import MoodEntry, MoodLevel

        # Calcular fecha de inicio
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(timeframe, 7)
        start_date = timezone.now() - timedelta(days=days)

        # Query mood entries
        try:
            moods = MoodEntry.objects.filter(
                auth_user_id=user_id,
                recorded_at__gte=start_date,
            ).order_by("-recorded_at")
        except Exception as exc:
            logger.warning(
                f"Error querying mood entries for user {user_id}: {exc}",
                exc_info=True,
            )
            return {
                "text": f"Contexto mental reciente ({timeframe}): Sin datos disponibles.",
                "metadata": {"error": str(exc), "mood_count": 0},
            }

        if not moods.exists():
            return {
                "text": f"Contexto mental reciente ({timeframe}): Usuario no ha registrado estados de ánimo.",
                "metadata": {"mood_count": 0},
            }

        # Calcular estadísticas
        mood_stats = moods.aggregate(
            count=Count("id"),
            # avg_level=Avg("level"),  # No podemos promediar strings directamente
        )

        # Mapear levels a números para calcular promedio
        level_values = {
            MoodLevel.VERY_LOW: 1,
            MoodLevel.LOW: 2,
            MoodLevel.MODERATE: 3,
            MoodLevel.GOOD: 4,
            MoodLevel.EXCELLENT: 5,
        }

        levels = [level_values.get(m.level, 3) for m in moods]
        avg_mood = sum(levels) / len(levels) if levels else 3.0
        variance = (
            sum((x - avg_mood) ** 2 for x in levels) / len(levels)
            if len(levels) > 1
            else 0.0
        )

        # Extraer tags más comunes
        all_tags = []
        for mood in moods:
            all_tags.extend(mood.tags or [])

        tag_counter = Counter(all_tags)
        top_tags = [tag for tag, _ in tag_counter.most_common(5)]

        # Extraer notas recientes (últimas 3)
        recent_notes = [
            m.note for m in list(moods[:3]) if m.note and m.note.strip()
        ]

        # Determinar mood predominante
        mood_level_counts = Counter(m.level for m in moods)
        predominant_mood = mood_level_counts.most_common(1)[0][0] if mood_level_counts else "moderate"

        # Construir texto consolidado
        mood_summary = self._mood_level_to_spanish(predominant_mood)

        text_parts = [
            f"Contexto mental reciente ({timeframe}):",
            f"- Estados de ánimo predominantes: {mood_summary}",
        ]

        if top_tags:
            text_parts.append(f"- Tags emocionales frecuentes: {', '.join(top_tags)}")

        if recent_notes:
            notes_text = " | ".join(recent_notes[:2])  # Máximo 2 notas
            text_parts.append(f"- Notas recientes: {notes_text}")

        text_parts.append(
            f"- Tendencia general: {'estable' if variance < 0.5 else 'variable'}"
        )

        consolidated_text = "\n".join(text_parts)

        return {
            "text": consolidated_text,
            "metadata": {
                "mood_count": mood_stats["count"],
                "avg_mood_level": round(avg_mood, 2),
                "mood_variance": round(variance, 2),
                "predominant_mood": predominant_mood,
                "top_tags": top_tags,
                "timeframe_days": days,
            },
        }

    def aggregate_body_context(
        self,
        user_id: str,
        timeframe: str = "7d",
    ) -> dict[str, Any]:
        """Agrega contexto físico: activities, nutrition, sleep, nutrition plan.

        Args:
            user_id: UUID del usuario en auth.users
            timeframe: Ventana temporal ("7d", "30d", "90d")

        Returns:
            Dict con "text" (consolidated) y "metadata" (stats)
        """
        from body.models import BodyActivity, NutritionLog, NutritionPlan, SleepLog

        # Calcular fecha de inicio
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(timeframe, 7)
        start_date = timezone.now() - timedelta(days=days)

        text_parts = [f"Contexto físico reciente ({timeframe}):"]
        metadata = {"timeframe_days": days}

        # 1. Actividad física
        try:
            activities = BodyActivity.objects.filter(
                auth_user_id=user_id,
                session_date__gte=start_date.date(),
            )

            if activities.exists():
                activity_stats = activities.aggregate(
                    total_minutes=Count("duration_minutes"),
                    count=Count("id"),
                )

                # Tipos de actividad más comunes
                activity_types = Counter(a.activity_type for a in activities)
                top_activities = [
                    act_type for act_type, _ in activity_types.most_common(3)
                ]

                total_mins = sum(a.duration_minutes or 0 for a in activities)
                activity_summary = f"{activity_stats['count']} sesiones, {total_mins} minutos totales"
                if top_activities:
                    activity_summary += f" ({', '.join(top_activities)})"

                text_parts.append(f"- Actividad física: {activity_summary}")
                metadata["activity_minutes_total"] = total_mins
                metadata["activity_sessions_count"] = activity_stats["count"]
                metadata["top_activity_types"] = top_activities
            else:
                text_parts.append("- Actividad física: Sin registros recientes")
                metadata["activity_minutes_total"] = 0
                metadata["activity_sessions_count"] = 0

        except Exception as exc:
            logger.warning(f"Error querying activities for user {user_id}: {exc}")
            text_parts.append("- Actividad física: Datos no disponibles")
            metadata["activity_error"] = str(exc)

        # 2. Sueño
        try:
            sleep_logs = SleepLog.objects.filter(
                auth_user_id=user_id,
                wake_time__gte=start_date,
            )

            if sleep_logs.exists():
                avg_sleep_hours = sum(
                    s.duration_hours or 0 for s in sleep_logs
                ) / sleep_logs.count()

                quality_counts = Counter(s.quality for s in sleep_logs)
                most_common_quality = (
                    quality_counts.most_common(1)[0][0] if quality_counts else "fair"
                )

                sleep_summary = f"{avg_sleep_hours:.1f}h promedio, calidad {most_common_quality}"
                text_parts.append(f"- Sueño: {sleep_summary}")
                metadata["avg_sleep_hours"] = round(avg_sleep_hours, 2)
                metadata["sleep_quality_mode"] = most_common_quality
                metadata["sleep_logs_count"] = sleep_logs.count()
            else:
                text_parts.append("- Sueño: Sin registros recientes")
                metadata["avg_sleep_hours"] = 0
                metadata["sleep_logs_count"] = 0

        except Exception as exc:
            logger.warning(f"Error querying sleep logs for user {user_id}: {exc}")
            text_parts.append("- Sueño: Datos no disponibles")
            metadata["sleep_error"] = str(exc)

        # 3. Nutrición
        try:
            nutrition_logs = NutritionLog.objects.filter(
                auth_user_id=user_id,
                timestamp__gte=start_date,
            )

            if nutrition_logs.exists():
                total_logs = nutrition_logs.count()
                # Calcular promedios de macros
                total_calories = sum(
                    (n.macros or {}).get("calories", 0) for n in nutrition_logs
                )
                avg_calories = total_calories / total_logs if total_logs > 0 else 0

                nutrition_summary = (
                    f"{total_logs} comidas registradas, {avg_calories:.0f} cal promedio"
                )
                text_parts.append(f"- Nutrición: {nutrition_summary}")
                metadata["nutrition_logs_count"] = total_logs
                metadata["avg_calories"] = round(avg_calories, 0)
            else:
                text_parts.append("- Nutrición: Sin registros recientes")
                metadata["nutrition_logs_count"] = 0

        except Exception as exc:
            logger.warning(f"Error querying nutrition logs for user {user_id}: {exc}")
            text_parts.append("- Nutrición: Datos no disponibles")
            metadata["nutrition_error"] = str(exc)

        # 4. Plan nutricional activo
        try:
            active_plan = NutritionPlan.objects.filter(
                auth_user_id=user_id,
                is_active=True,
                valid_until__gte=timezone.now().date(),
            ).first()

            if active_plan:
                plan_data = active_plan.plan_data or {}
                assessment = plan_data.get("assessment", {})

                objectives = assessment.get("objective", [])
                diagnoses = assessment.get("diagnosis", [])

                plan_summary_parts = ["Plan nutricional activo"]
                if objectives:
                    obj_text = ", ".join(objectives[:2])
                    plan_summary_parts.append(f"objetivos: {obj_text}")
                if diagnoses:
                    diag_text = ", ".join(diagnoses[:2])
                    plan_summary_parts.append(f"diagnósticos: {diag_text}")

                plan_summary = f"- {' - '.join(plan_summary_parts)}"
                text_parts.append(plan_summary)
                metadata["nutrition_plan_id"] = str(active_plan.id)
                metadata["nutrition_plan_objectives"] = objectives[:3]
                metadata["nutrition_plan_diagnoses"] = diagnoses[:3]
            else:
                text_parts.append("- Plan nutricional activo: ninguno")
                metadata["nutrition_plan_id"] = None

        except Exception as exc:
            logger.warning(f"Error querying nutrition plan for user {user_id}: {exc}")
            text_parts.append("- Plan nutricional activo: Datos no disponibles")
            metadata["nutrition_plan_error"] = str(exc)

        consolidated_text = "\n".join(text_parts)

        return {
            "text": consolidated_text,
            "metadata": metadata,
        }

    def aggregate_soul_context(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """Agrega contexto espiritual: IKIGAI + psychosocial context.

        Args:
            user_id: UUID del usuario en auth.users

        Returns:
            Dict con "text" (consolidated) y "metadata" (themes, counts)
        """
        from holistic.models import UserProfileExtended

        try:
            profile = UserProfileExtended.objects.filter(
                auth_user_id=user_id
            ).first()
        except Exception as exc:
            logger.warning(
                f"Error querying extended profile for user {user_id}: {exc}"
            )
            return {
                "text": "Contexto espiritual: Datos no disponibles.",
                "metadata": {"error": str(exc)},
            }

        if not profile:
            return {
                "text": "Contexto espiritual: Usuario no ha completado perfil IKIGAI.",
                "metadata": {"has_profile": False},
            }

        text_parts = ["Contexto espiritual:"]
        metadata = {"has_profile": True}

        # IKIGAI
        if profile.ikigai_statement and profile.ikigai_statement.strip():
            text_parts.append(
                f"- Propósito de vida (IKIGAI): {profile.ikigai_statement[:200]}"
            )
            metadata["has_ikigai_statement"] = True
        else:
            metadata["has_ikigai_statement"] = False

        ikigai_dimensions = []
        if profile.ikigai_passion:
            passions = ", ".join(profile.ikigai_passion[:3])
            text_parts.append(f"- Pasiones: {passions}")
            ikigai_dimensions.append("passion")

        if profile.ikigai_mission:
            missions = ", ".join(profile.ikigai_mission[:3])
            text_parts.append(f"- Misión: {missions}")
            ikigai_dimensions.append("mission")

        if profile.ikigai_vocation:
            vocations = ", ".join(profile.ikigai_vocation[:3])
            text_parts.append(f"- Vocación: {vocations}")
            ikigai_dimensions.append("vocation")

        if profile.ikigai_profession:
            professions = ", ".join(profile.ikigai_profession[:3])
            text_parts.append(f"- Profesión: {professions}")
            ikigai_dimensions.append("profession")

        metadata["ikigai_dimensions_defined"] = ikigai_dimensions

        # Contexto psicosocial
        if profile.psychosocial_context and profile.psychosocial_context.strip():
            psycho_excerpt = profile.psychosocial_context[:200]
            text_parts.append(f"- Contexto psicosocial: {psycho_excerpt}")
            metadata["has_psychosocial_context"] = True
        else:
            metadata["has_psychosocial_context"] = False

        if profile.support_network and profile.support_network.strip():
            support_excerpt = profile.support_network[:150]
            text_parts.append(f"- Red de apoyo: {support_excerpt}")
            metadata["has_support_network"] = True
        else:
            metadata["has_support_network"] = False

        if profile.current_stressors and profile.current_stressors.strip():
            stressors_excerpt = profile.current_stressors[:150]
            text_parts.append(f"- Estresores actuales: {stressors_excerpt}")
            metadata["has_current_stressors"] = True
        else:
            metadata["has_current_stressors"] = False

        consolidated_text = "\n".join(text_parts)

        return {
            "text": consolidated_text,
            "metadata": metadata,
        }

    def aggregate_holistic_context(
        self,
        user_id: str,
        timeframe: str = "30d",
    ) -> dict[str, Any]:
        """Combina mind + body + soul en un snapshot holístico completo.

        Args:
            user_id: UUID del usuario en auth.users
            timeframe: Ventana temporal ("7d", "30d", "90d")

        Returns:
            Dict con "text" (consolidated) y "metadata" (combined)
        """
        mind = self.aggregate_mind_context(user_id, timeframe)
        body = self.aggregate_body_context(user_id, timeframe)
        soul = self.aggregate_soul_context(user_id)

        consolidated_text = "\n\n".join(
            [
                "CONTEXTO HOLÍSTICO COMPLETO:",
                mind["text"],
                body["text"],
                soul["text"],
            ]
        )

        metadata = {
            "mind": mind["metadata"],
            "body": body["metadata"],
            "soul": soul["metadata"],
            "timeframe": timeframe,
        }

        return {
            "text": consolidated_text,
            "metadata": metadata,
        }

    @staticmethod
    def _mood_level_to_spanish(level: str) -> str:
        """Convierte mood level enum a texto en español."""
        mapping = {
            "very_low": "muy bajo",
            "low": "bajo",
            "moderate": "moderado",
            "good": "bueno",
            "excellent": "excelente",
        }
        return mapping.get(level, level)

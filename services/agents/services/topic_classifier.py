"""
Servicio de clasificación de contexto de usuario a topics biomédicos.

Usa LLM (Gemini) para extraer topics relevantes del contexto del usuario,
mapeando a los 37 topics definidos en services/vectordb/config/topics.yaml.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

from google import genai

logger = logging.getLogger(__name__)


# Topics biomédicos disponibles (sync con vectordb/config/topics.yaml)
AVAILABLE_TOPICS = [
    "sleep_health",
    "circadian_rhythm",
    "sleep_deprivation",
    "insomnia",
    "hypersomnia",
    "obstructive_sleep_apnea",
    "metabolism_disorders",
    "obesity",
    "type2_diabetes",
    "insulin_signaling",
    "endocrine_disorders",
    "stress_response",
    "inflammation",
    "oxidative_stress",
    "cardiovascular_health",
    "neurodegeneration",
    "cognitive_function",
    "mental_health",
    "gut_microbiome",
    "nutrition",
    "exercise_physiology",
    "chrononutrition",
    "reproductive_health",
    "pcos",
    "adolescent_health",
    "aging_longevity",
    "immunometabolism",
    "liver_health",
    "sleep_medicine",
    "neuroendocrine",
    "chronic_pain",
    "immune_disorders",
    "metabolic_brain",
    "biomarker_discovery",
]


# Mapeo de topics a descripciones para el LLM
TOPIC_DESCRIPTIONS = {
    "sleep_health": "Calidad del sueño, higiene del sueño, duración del sueño",
    "circadian_rhythm": "Ritmo circadiano, cronobiología, reloj biológico",
    "sleep_deprivation": "Privación del sueño, deuda de sueño, restricción del sueño",
    "insomnia": "Insomnio, dificultad para dormir, despertar temprano",
    "hypersomnia": "Somnolencia excesiva diurna, narcolepsia",
    "obstructive_sleep_apnea": "Apnea del sueño, OSA, resistencia de las vías respiratorias",
    "metabolism_disorders": "Síndrome metabólico, dislipidemia, hiperglucemia",
    "obesity": "Obesidad, IMC, adiposidad, pérdida de peso",
    "type2_diabetes": "Diabetes tipo 2, resistencia a la insulina, intolerancia a la glucosa",
    "insulin_signaling": "Señalización de insulina, sensibilidad a la insulina, captación de glucosa",
    "endocrine_disorders": "Trastornos endocrinos, desequilibrio hormonal",
    "stress_response": "Respuesta al estrés, cortisol, eje HPA",
    "inflammation": "Inflamación, citoquinas proinflamatorias, activación inmune",
    "oxidative_stress": "Estrés oxidativo, especies reactivas de oxígeno, antioxidantes",
    "cardiovascular_health": "Salud cardiovascular, hipertensión, aterosclerosis",
    "neurodegeneration": "Neurodegeneración, Alzheimer, Parkinson, neuroinflamación",
    "cognitive_function": "Función cognitiva, memoria, función ejecutiva, atención",
    "mental_health": "Salud mental, ansiedad, depresión, trastornos del ánimo",
    "gut_microbiome": "Microbioma intestinal, microbiota, flora intestinal",
    "nutrition": "Nutrición, ingesta dietética, macronutrientes, intervención nutricional",
    "exercise_physiology": "Fisiología del ejercicio, actividad física, entrenamiento aeróbico",
    "chrononutrition": "Crononutrición, tiempo de comidas, alimentación restringida en el tiempo",
    "reproductive_health": "Salud reproductiva, fertilidad, función ovárica",
    "pcos": "Síndrome de ovario poliquístico, SOP, hirsutismo",
    "adolescent_health": "Salud adolescente, salud juvenil",
    "aging_longevity": "Envejecimiento, longevidad, envejecimiento saludable",
    "immunometabolism": "Inmunometabolismo, metabolismo inmune, inflamación metabólica",
    "liver_health": "Salud hepática, esteatosis hepática, hígado graso no alcohólico",
    "sleep_medicine": "Medicina del sueño, polisomnografía, clínica del sueño",
    "neuroendocrine": "Neuroendocrino, neuropéptidos, hormonas hipofisarias",
    "chronic_pain": "Dolor crónico, manejo del dolor, nocicepción",
    "immune_disorders": "Trastornos inmunes, autoinmune, desregulación inmune",
    "metabolic_brain": "Metabolismo cerebral, neurometabolismo",
    "biomarker_discovery": "Descubrimiento de biomarcadores, marcadores diagnósticos",
}


CLASSIFICATION_PROMPT = """Eres un experto en clasificación de contexto médico y de bienestar.

Analiza el siguiente contexto del usuario y extrae los topics biomédicos más relevantes de la lista proporcionada.

CONTEXTO DEL USUARIO:
{context}

TOPICS DISPONIBLES:
{topics_list}

INSTRUCCIONES:
1. Identifica entre 1 y 5 topics que sean MÁS relevantes para el contexto
2. Prioriza topics específicos sobre generales
3. Si mencionan problemas de sueño, incluye topics relacionados (sleep_health, insomnia, etc.)
4. Si mencionan nutrición o dieta, incluye topics relacionados (nutrition, gut_microbiome, etc.)
5. Si mencionan estrés o ansiedad, incluye topics de salud mental
6. SOLO devuelve topics que estén en la lista proporcionada

FORMATO DE RESPUESTA (JSON):
{{
  "topics": ["topic1", "topic2", "topic3"],
  "reasoning": "Breve explicación de por qué se seleccionaron estos topics"
}}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional."""


class TopicClassifier:
    """Clasificador de contexto de usuario a topics biomédicos usando LLM."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash-exp"):
        """
        Inicializa el clasificador.

        Args:
            api_key: API key de Google Gemini (usa GOOGLE_API_KEY si no se proporciona)
            model: Modelo de Gemini a usar
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY no está configurada")

        self.model_name = model
        self.client = genai.Client(api_key=self.api_key)

        # Cache de clasificaciones (LRU cache en memoria)
        self._cache: dict[str, list[str]] = {}
        self._max_cache_size = 100

    def classify(self, context: str | dict[str, Any]) -> list[str]:
        """
        Clasifica el contexto del usuario en topics biomédicos.

        Args:
            context: Contexto del usuario (texto o dict estructurado)

        Returns:
            Lista de topics relevantes (entre 1 y 5)
        """
        # Convertir context a string si es dict
        if isinstance(context, dict):
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
        else:
            context_str = str(context)

        # Verificar cache
        cache_key = self._hash_context(context_str)
        if cache_key in self._cache:
            logger.info("Topic classification cache hit")
            return self._cache[cache_key]

        # Construir lista de topics con descripciones
        topics_list = "\n".join(
            f"- {topic}: {TOPIC_DESCRIPTIONS.get(topic, '')}" for topic in AVAILABLE_TOPICS
        )

        # Construir prompt
        prompt = CLASSIFICATION_PROMPT.format(context=context_str, topics_list=topics_list)

        try:
            # Llamar al LLM
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,  # Baja temperatura para respuestas consistentes
                    max_output_tokens=500,
                ),
            )

            # Parsear respuesta JSON
            response_text = response.text.strip()
            # Limpiar markdown code blocks si existen
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)
            topics = result.get("topics", [])
            reasoning = result.get("reasoning", "")

            # Validar que los topics estén en la lista
            valid_topics = [t for t in topics if t in AVAILABLE_TOPICS]

            if not valid_topics:
                logger.warning(f"No valid topics extracted from context: {context_str[:100]}")
                # Fallback: retornar topic genérico basado en categoría
                return self._get_fallback_topics(context_str)

            logger.info(f"Classified {len(valid_topics)} topics: {valid_topics} | Reasoning: {reasoning}")

            # Guardar en cache
            self._update_cache(cache_key, valid_topics)

            return valid_topics

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e} | Response: {response.text[:200]}")
            return self._get_fallback_topics(context_str)
        except Exception as e:
            logger.error(f"Topic classification failed: {e}")
            return self._get_fallback_topics(context_str)

    def _hash_context(self, context: str) -> str:
        """Genera hash del contexto para cache."""
        import hashlib

        return hashlib.md5(context.encode()).hexdigest()

    def _update_cache(self, key: str, topics: list[str]) -> None:
        """Actualiza cache con límite de tamaño."""
        if len(self._cache) >= self._max_cache_size:
            # Eliminar entrada más antigua (FIFO simple)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = topics

    def _get_fallback_topics(self, context: str) -> list[str]:
        """
        Retorna topics de fallback basados en keywords simples.

        Args:
            context: Contexto del usuario

        Returns:
            Lista de topics de fallback
        """
        context_lower = context.lower()
        fallback = []

        # Keywords para detección simple
        if any(kw in context_lower for kw in ["sueño", "dormir", "insomni", "despertar"]):
            fallback.extend(["sleep_health", "insomnia"])
        if any(kw in context_lower for kw in ["estrés", "ansiedad", "depresión", "mental"]):
            fallback.extend(["mental_health", "stress_response"])
        if any(kw in context_lower for kw in ["nutrición", "dieta", "aliment", "comida"]):
            fallback.extend(["nutrition", "gut_microbiome"])
        if any(kw in context_lower for kw in ["ejercicio", "actividad física", "deporte"]):
            fallback.append("exercise_physiology")
        if any(kw in context_lower for kw in ["peso", "obesidad", "adelgaz"]):
            fallback.extend(["obesity", "metabolism_disorders"])

        if not fallback:
            # Si no hay keywords, retornar topics generales
            fallback = ["mental_health", "nutrition", "sleep_health"]

        logger.warning(f"Using fallback topics: {fallback}")
        return fallback[:5]  # Máximo 5 topics


@lru_cache(maxsize=1)
def get_topic_classifier() -> TopicClassifier:
    """Retorna instancia singleton del clasificador."""
    return TopicClassifier()


__all__ = ["TopicClassifier", "get_topic_classifier", "AVAILABLE_TOPICS", "TOPIC_DESCRIPTIONS"]

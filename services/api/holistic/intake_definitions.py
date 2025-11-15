"""Definiciones estáticas del formulario de intake holístico.

Las preguntas se exponen como un registro inmutable para garantizar que el backend
pueda validar respuestas provenientes del frontend y generar recomendaciones
consistentes.
"""

from __future__ import annotations

from typing import Any, Final


IntakeQuestion = dict[str, Any]


INTAKE_QUESTION_REGISTRY: Final[dict[str, IntakeQuestion]] = {
    # ------------------------- Físico -------------------------
    "F1": {
        "dimension": "physical",
        "type": "likert",
        "choices": [
            "very_low",
            "low",
            "moderate",
            "good",
            "excellent",
        ],
    },
    "F2": {
        "dimension": "physical",
        "type": "single_choice",
        "choices": [
            "never",
            "weekly_1_2",
            "weekly_3_4",
            "weekly_5_plus",
        ],
    },
    "F3": {
        "dimension": "physical",
        "type": "compound",
        "schema": {
            "frequency": {
                "type": "single_choice",
                "choices": [
                    "almost_never",
                    "one_two",
                    "three_four",
                    "five_plus",
                ],
                "required": True,
            },
            "consulted_professional": {
                "type": "boolean",
                "required": False,
            },
        },
    },
    "F4": {
        "dimension": "physical",
        "type": "multi_choice",
        "choices": [
            "irregular_nutrition",
            "sedentarism",
            "physical_discomfort",
            "screen_overuse",
            "irregular_schedule",
            "other",
        ],
        "min_selections": 1,
        "allow_other_text": True,
        "other_text_max_length": 120,
    },
    # ------------------------- Mental -------------------------
    "M1": {
        "dimension": "mental",
        "type": "likert",
        "choices": [
            "very_low",
            "low",
            "moderate",
            "high",
            "very_high",
        ],
    },
    "M2": {
        "dimension": "mental",
        "type": "multi_choice",
        "choices": [
            "work",
            "finances",
            "relationships",
            "health",
            "caregiving",
            "social_environment",
            "other",
        ],
        "min_selections": 1,
        "allow_other_text": True,
        "other_text_max_length": 120,
    },
    "M3": {
        "dimension": "mental",
        "type": "single_choice",
        "choices": [
            "almost_never",
            "weekly_1_2",
            "weekly_3_4",
            "almost_daily",
        ],
    },
    "M4": {
        "dimension": "mental",
        "type": "compound",
        "schema": {
            "has_strategies": {
                "type": "boolean",
                "required": True,
            },
            "strategies": {
                "type": "multi_choice",
                "choices": [
                    "breathing",
                    "journaling",
                    "therapy",
                    "mindfulness",
                    "movement",
                    "other",
                ],
                "required": False,
                "allow_other_text": True,
                "other_text_max_length": 120,
            },
        },
    },
    # ------------------------- Espiritual ---------------------
    "S1": {
        "dimension": "spiritual",
        "type": "single_choice",
        "choices": [
            "not_aligned",
            "slightly_aligned",
            "partially_aligned",
            "very_aligned",
            "fully_aligned",
        ],
    },
    "S2": {
        "dimension": "spiritual",
        "type": "multi_choice",
        "choices": [
            "meditation",
            "gratitude",
            "creative_space",
            "service",
            "religious_practice",
            "time_in_nature",
            "none",
        ],
        "min_selections": 1,
        "mutually_exclusive_option": "none",
    },
    "S3": {
        "dimension": "spiritual",
        "type": "likert",
        "choices": [
            "very_low",
            "low",
            "moderate",
            "high",
            "very_high",
        ],
    },
    "S4": {
        "dimension": "spiritual",
        "type": "compound",
        "schema": {
            "has_guide": {
                "type": "boolean",
                "required": True,
            },
            "guide_type": {
                "type": "single_choice",
                "choices": [
                    "mentor",
                    "community",
                    "literature",
                    "other",
                ],
                "required": False,
            },
        },
    },
}


REQUIRED_QUESTION_IDS: Final[tuple[str, ...]] = tuple(INTAKE_QUESTION_REGISTRY.keys())


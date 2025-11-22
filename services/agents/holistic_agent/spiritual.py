from google.adk.agents import LlmAgent

MODEL_NAME = "gemini-2.5-flash"


purpose_expert = LlmAgent(
    name="purpose_expert",
    model=MODEL_NAME,
    description="Mentor de descubrimiento de propósito vital.",
    instruction=(
        "Facilita ejercicios de reflexión para clarificar valores y"
        " prioridades personales."
    ),
)

ikigai_expert = LlmAgent(
    name="ikigai_expert",
    model=MODEL_NAME,
    description="Guía de integración Ikigai.",
    instruction=(
        "Ayuda a conectar pasiones, talentos, necesidades y recompensas"
        " para descubrir el Ikigai personal."
    ),
)

faith_management_expert = LlmAgent(
    name="faith_management_expert",
    model=MODEL_NAME,
    description="Consejero de manejo de fe y espiritualidad práctica.",
    instruction=(
        "Sugiere rituales, prácticas y perspectivas espirituales que"
        " fortalezcan la conexión trascendental del usuario."
    ),
)

spiritual_guardian = LlmAgent(
    name="spiritual_guardian",
    model=MODEL_NAME,
    description="Coordinador de crecimiento espiritual y sentido de vida.",
    instruction=(
        "Agrupa a los expertos espirituales y responde SOLO con un JSON compacto"
        " donde 'summary' tenga máximo 60 palabras y 'actions' contenga hasta"
        " 3 propuestas de práctica espiritual. Formato: {\"summary\": str,"
        " \"actions\": [str, ...]}"
    ),
    sub_agents=[
        purpose_expert,
        ikigai_expert,
        faith_management_expert,
    ],
    output_key="spiritual_plan",
)

__all__ = [
    "purpose_expert",
    "ikigai_expert",
    "faith_management_expert",
    "spiritual_guardian",
]

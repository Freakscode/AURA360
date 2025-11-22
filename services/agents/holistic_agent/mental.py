from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

MODEL_NAME = "gemini-2.5-flash"


neurodivergence_expert = LlmAgent(
    name="neurodivergence_expert",
    model=MODEL_NAME,
    description="Especialista en diversidad neurológica y apoyos personalizados.",
    instruction=(
        "Identifica necesidades neurodivergentes y responde SOLO con un JSON"
        " {\"summary\": str, \"actions\": [str, ...]} con máximo 50 palabras"
        " en summary y hasta 3 acciones concretas."
    ),
    output_key="neurodivergence_plan",
)

anxiety_expert = LlmAgent(
    name="anxiety_expert",
    model=MODEL_NAME,
    description="Coach de regulación emocional frente a ansiedad.",
    instruction=(
        "Detecta desencadenantes de ansiedad y responde SOLO con un JSON"
        " {\"summary\": str, \"actions\": [str, ...]} con máximo 50 palabras"
        " en summary y hasta 3 técnicas recomendadas."
    ),
    output_key="anxiety_plan",
)

depression_expert = LlmAgent(
    name="depression_expert",
    model=MODEL_NAME,
    description="Acompañante en procesos de depresión y recuperación.",
    instruction=(
        "Evalúa señales de ánimo bajo y responde SOLO con un JSON"
        " {\"summary\": str, \"actions\": [str, ...]} con máximo 50 palabras"
        " en summary y hasta 3 acciones para fortalecer resiliencia."
    ),
    output_key="depression_plan",
)

mental_parallel = ParallelAgent(
    name="mental_parallel",
    description="Recopila análisis neurodivergente, ansiedad y depresión en paralelo.",
    sub_agents=[
        neurodivergence_expert,
        anxiety_expert,
        depression_expert,
    ],
)

mental_synthesizer = LlmAgent(
    name="mental_synthesizer",
    model=MODEL_NAME,
    description="Sintetiza las recomendaciones mentales en un plan unificado.",
    instruction="""
        Recibes los siguientes JSON:
        - Neurodivergencia: {neurodivergence_plan}
        - Ansiedad: {anxiety_plan}
        - Depresión: {depression_plan}
        Devuelve UN SOLO JSON {"summary": str, "actions": [str, ...]} con máximo
        60 palabras en summary y hasta 4 acciones integradas, sin texto adicional.
    """,
    output_key="mental_plan",
)

mental_guardian = SequentialAgent(
    name="mental_guardian",
    description="Coordinador de bienestar mental y emocional.",
    sub_agents=[
        mental_parallel,
        mental_synthesizer,
    ],
)

__all__ = [
    "neurodivergence_expert",
    "anxiety_expert",
    "depression_expert",
    "mental_parallel",
    "mental_synthesizer",
    "mental_guardian",
]

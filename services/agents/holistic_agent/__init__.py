"""Sistema multiagente holístico basado en Google ADK."""

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from .knowledge import knowledge_retriever
from .physical import physical_guardian
from .mental import mental_guardian
from .spiritual import spiritual_guardian

MODEL_NAME = "gemini-2.5-flash"

# Paso 1: agentes guardianes ya definidos en submódulos (físico, mental, espiritual)

# Paso 2: paralelizar los guardianes para procesar al mismo tiempo la información de onboarding.
holistic_parallel = ParallelAgent(
    name="holistic_parallel",
    description="Ejecuta en paralelo los guardianes físico, mental y espiritual.",
    sub_agents=[
        physical_guardian,
        mental_guardian,
        spiritual_guardian,
    ],
)

# Paso 3: agente sintetizador que consolida los resultados del paso paralelo.
holistic_synthesizer = LlmAgent(
    name="holistic_synthesizer",
    model=MODEL_NAME,
    description="Integra los hallazgos de mente, cuerpo y alma en un plan unificado.",
    instruction="""
        Recibes tres planes parciales en estado: physical_plan, mental_plan y spiritual_plan.
        Cada uno es un JSON con 'summary' y 'actions'. Devuelve UN SOLO mensaje final
        estructurado en JSON con el formato {"summary": str, "mind": {..}, "body": {..},
        "spirit": {..}, "next_steps": [str, ...]} donde cada sección sintetiza
        exclusivamente la información recibida. No añadas texto fuera del JSON.
    """,
)

holistic_coordinator = SequentialAgent(
    name="holistic_coordinator",
    description="Orquestador que paraleliza guardianes y sintetiza conclusiones.",
    sub_agents=[
        knowledge_retriever,
        holistic_parallel,
        holistic_synthesizer,
    ],
)

__all__ = [
    "holistic_coordinator",
    "knowledge_retriever",
    "holistic_parallel",
    "holistic_synthesizer",
    "physical_guardian",
    "mental_guardian",
    "spiritual_guardian",
]

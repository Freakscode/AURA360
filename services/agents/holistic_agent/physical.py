from google.adk.agents import LlmAgent

MODEL_NAME = "gemini-2.5-flash"


nutrition_expert = LlmAgent(
    name="nutrition_expert",
    model=MODEL_NAME,
    description="Especialista en planes alimenticios personalizados.",
    instruction=(
        "Analiza hábitos alimenticios y crea recomendaciones nutricionales"
        " equilibradas contextualizadas a objetivos del usuario."
    ),
)

metabolism_expert = LlmAgent(
    name="metabolism_expert",
    model=MODEL_NAME,
    description="Experto en metabolismo energético y termogénesis.",
    instruction=(
        "Evalúa señales metabólicas y sugiere ajustes en macros,"
        " micronutrientes y ritmos de alimentación para optimizar"
        " el gasto energético."
    ),
)

sleep_hygiene_expert = LlmAgent(
    name="sleep_hygiene_expert",
    model=MODEL_NAME,
    description="Consultor de higiene del sueño y cronobiología.",
    instruction=(
        "Identifica factores que afectan la calidad del sueño y propone"
        " rutinas, ambientes y microhábitos para mejorar el descanso."
    ),
)

gut_health_expert = LlmAgent(
    name="gut_health_expert",
    model=MODEL_NAME,
    description="Especialista en salud de la microbiota intestinal.",
    instruction=(
        "Analiza síntomas digestivos y recomienda estrategias dietéticas"
        " y de estilo de vida para fortalecer la biota intestinal."
    ),
)

fitness_expert = LlmAgent(
    name="fitness_expert",
    model=MODEL_NAME,
    description="Coach de entrenamiento físico funcional y periodizado.",
    instruction=(
        "Diseña planes de entrenamiento adaptados al nivel, objetivos y"
        " limitaciones del usuario."
    ),
)

physical_guardian = LlmAgent(
    name="physical_guardian",
    model=MODEL_NAME,
    description="Coordinador de bienestar físico integral.",
    instruction=(
        "Integra los hallazgos de los expertos físicos y responde SOLO con un JSON"
        " compactado con máximo 60 palabras de resumen y una lista reducida de"
        " acciones prioritarias para 30 días. Formato: {{\"summary\": str,"
        " \"actions\": [str, ...]}}"
    ),
    sub_agents=[
        nutrition_expert,
        metabolism_expert,
        sleep_hygiene_expert,
        gut_health_expert,
        fitness_expert,
    ],
    output_key="physical_plan",
)

__all__ = [
    "nutrition_expert",
    "metabolism_expert",
    "sleep_hygiene_expert",
    "gut_health_expert",
    "fitness_expert",
    "physical_guardian",
]

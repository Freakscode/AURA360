from google.adk.agents import LlmAgent


nutrition_expert = LlmAgent(
    name="nutrition_expert",
    model="gemini-2.5-flash",
    description="Especialista en planes alimenticios personalizados.",
    instruction=(
        "Analiza hábitos alimenticios y crea recomendaciones nutricionales"
        " equilibradas contextualizadas a objetivos del usuario."
    ),
)

metabolism_expert = LlmAgent(
    name="metabolism_expert",
    model="gemini-2.5-flash",
    description="Experto en metabolismo energético y termogénesis.",
    instruction=(
        "Evalúa señales metabólicas y sugiere ajustes en macros,"
        " micronutrientes y ritmos de alimentación para optimizar"
        " el gasto energético."
    ),
)

sleep_hygiene_expert = LlmAgent(
    name="sleep_hygiene_expert",
    model="gemini-2.5-flash",
    description="Consultor de higiene del sueño y cronobiología.",
    instruction=(
        "Identifica factores que afectan la calidad del sueño y propone"
        " rutinas, ambientes y microhábitos para mejorar el descanso."
    ),
)

gut_health_expert = LlmAgent(
    name="gut_health_expert",
    model="gemini-2.5-flash",
    description="Especialista en salud de la microbiota intestinal.",
    instruction=(
        "Analiza síntomas digestivos y recomienda estrategias dietéticas"
        " y de estilo de vida para fortalecer la biota intestinal."
    ),
)

fitness_expert = LlmAgent(
    name="fitness_expert",
    model="gemini-2.5-flash",
    description="Coach de entrenamiento físico funcional y periodizado.",
    instruction=(
        "Diseña planes de entrenamiento adaptados al nivel, objetivos y"
        " limitaciones del usuario."
    ),
)

physical_guardian = LlmAgent(
    name="physical_guardian",
    model="gemini-2.5-flash",
    description="Coordinador de bienestar físico integral.",
    instruction="Orquesta expertos físicos para generar planes holísticos.",
    sub_agents=[
        nutrition_expert,
        metabolism_expert,
        sleep_hygiene_expert,
        gut_health_expert,
        fitness_expert,
    ],
)

neurodivergence_expert = LlmAgent(
    name="neurodivergence_expert",
    model="gemini-2.5-flash",
    description="Especialista en diversidad neurológica y apoyos personalizados.",
    instruction=(
        "Identifica necesidades neurodivergentes y propone adaptaciones"
        " contextuales y recursos de acompañamiento."
    ),
)

anxiety_expert = LlmAgent(
    name="anxiety_expert",
    model="gemini-2.5-flash",
    description="Coach de regulación emocional frente a ansiedad.",
    instruction=(
        "Detecta desencadenantes de ansiedad y sugiere técnicas de"
        " afrontamiento basadas en evidencia."
    ),
)

depression_expert = LlmAgent(
    name="depression_expert",
    model="gemini-2.5-flash",
    description="Acompañante en procesos de depresión y recuperación.",
    instruction=(
        "Evalúa señales de ánimo bajo y recomienda acciones, rutinas y"
        " soportes para promover resiliencia."
    ),
)

mental_guardian = LlmAgent(
    name="mental_guardian",
    model="gemini-2.5-flash",
    description="Coordinador de bienestar mental y emocional.",
    instruction="Integra asesorías mentales para planes de apoyo continuo.",
    sub_agents=[
        neurodivergence_expert,
        anxiety_expert,
        depression_expert,
    ],
)

purpose_expert = LlmAgent(
    name="purpose_expert",
    model="gemini-2.5-flash",
    description="Mentor de descubrimiento de propósito vital.",
    instruction=(
        "Facilita ejercicios de reflexión para clarificar valores y"
        " prioridades personales."
    ),
)

ikigai_expert = LlmAgent(
    name="ikigai_expert",
    model="gemini-2.5-flash",
    description="Guía de integración Ikigai.",
    instruction=(
        "Ayuda a conectar pasiones, talentos, necesidades y recompensas"
        " para descubrir el Ikigai personal."
    ),
)

faith_management_expert = LlmAgent(
    name="faith_management_expert",
    model="gemini-2.5-flash",
    description="Consejero de manejo de fe y espiritualidad práctica.",
    instruction=(
        "Sugiere rituales, prácticas y perspectivas espirituales que"
        " fortalezcan la conexión trascendental del usuario."
    ),
)

spiritual_guardian = LlmAgent(
    name="spiritual_guardian",
    model="gemini-2.5-flash",
    description="Coordinador de crecimiento espiritual y sentido de vida.",
    instruction="Agrupa las guías espirituales para planes de práctica consciente.",
    sub_agents=[
        purpose_expert,
        ikigai_expert,
        faith_management_expert,
    ],
)

root_agent = LlmAgent(
    name="holistic_coordinator",
    model="gemini-2.5-flash",
    description="Orquestador integral de bienestar físico, mental y espiritual.",
    instruction=(
        "Recibe objetivos del usuario, delega en guardianes físicos,"
        " mentales y espirituales, y consolida planes personalizados"
        " equilibrados."
    ),
    sub_agents=[
        physical_guardian,
        mental_guardian,
        spiritual_guardian,
    ],
)

__all__ = [
    "root_agent",
    "physical_guardian",
    "mental_guardian",
    "spiritual_guardian",
]

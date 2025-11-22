import { IntakeSectionConfig } from './models/wellness-intake.models';

export const WELLNESS_INTAKE_SECTIONS: IntakeSectionConfig[] = [
  {
    key: 'physical',
    title: 'Salud física',
    description: 'Exploramos hábitos diarios para entender tu energía y rutinas actuales.',
    questions: [
      {
        id: 'F1',
        title: '¿Cómo describirías tu nivel de energía física promedio durante el día?',
        type: 'likert',
        options: [
          { value: 'very_low', label: 'Muy baja' },
          { value: 'low', label: 'Baja' },
          { value: 'moderate', label: 'Moderada' },
          { value: 'good', label: 'Buena' },
          { value: 'excellent', label: 'Excelente' },
        ],
      },
      {
        id: 'F2',
        title: '¿Con qué frecuencia realizas actividad física moderada al menos 30 minutos?',
        type: 'single',
        options: [
          { value: 'never', label: 'Nunca' },
          { value: 'weekly_1_2', label: '1-2 veces / semana' },
          { value: 'weekly_3_4', label: '3-4 veces / semana' },
          { value: 'weekly_5_plus', label: '5+ veces / semana' },
        ],
      },
      {
        id: 'F3',
        title: '¿Cuántas noches a la semana duermes al menos 7 horas continuas?',
        description:
          'Si duermes menos de 3 noches completas, cuéntanos si has buscado apoyo profesional.',
        type: 'compound',
      },
      {
        id: 'F4',
        title: '¿Qué hábitos crees que impactan tu bienestar corporal hoy?',
        description: 'Selecciona todas las opciones que apliquen.',
        type: 'multi',
        options: [
          { value: 'irregular_nutrition', label: 'Alimentación irregular' },
          { value: 'sedentarism', label: 'Sedentarismo' },
          { value: 'physical_discomfort', label: 'Dolor o restricción física' },
          { value: 'screen_overuse', label: 'Uso prolongado de pantallas' },
          { value: 'irregular_schedule', label: 'Horarios desordenados' },
          { value: 'other', label: 'Otro (especifica)' },
        ],
      },
    ],
  },
  {
    key: 'mental',
    title: 'Bienestar mental',
    description: 'Identificamos la claridad mental, el estrés y tus herramientas de autorregulación.',
    questions: [
      {
        id: 'M1',
        title: '¿Cómo describirías tu claridad mental para tomar decisiones diarias?',
        type: 'likert',
        options: [
          { value: 'very_low', label: 'Muy baja' },
          { value: 'low', label: 'Baja' },
          { value: 'moderate', label: 'Moderada' },
          { value: 'high', label: 'Alta' },
          { value: 'very_high', label: 'Muy alta' },
        ],
      },
      {
        id: 'M2',
        title: 'En las últimas dos semanas, ¿qué factores te han generado más estrés?',
        description: 'Selecciona todas las opciones aplicables.',
        type: 'multi',
        options: [
          { value: 'work', label: 'Trabajo / estudios' },
          { value: 'finances', label: 'Finanzas' },
          { value: 'relationships', label: 'Relaciones personales' },
          { value: 'health', label: 'Salud propia' },
          { value: 'caregiving', label: 'Cuidado de otras personas' },
          { value: 'social_environment', label: 'Entorno social / comunidad' },
          { value: 'other', label: 'Otro (especifica)' },
        ],
      },
      {
        id: 'M3',
        title: '¿Con qué frecuencia sientes ansiedad o inquietud persistente?',
        type: 'single',
        options: [
          { value: 'almost_never', label: 'Casi nunca' },
          { value: 'weekly_1_2', label: '1-2 días / semana' },
          { value: 'weekly_3_4', label: '3-4 días / semana' },
          { value: 'almost_daily', label: 'Casi a diario' },
        ],
      },
      {
        id: 'M4',
        title: '¿Cuentas con estrategias claras para regular tus emociones?',
        description: 'Marca Sí para indicar qué herramientas utilizas actualmente.',
        type: 'compound',
      },
    ],
  },
  {
    key: 'spiritual',
    title: 'Propósito y sentido',
    description:
      'Exploramos qué tan alineadas se sienten tus acciones con tus valores y redes de guía.',
    questions: [
      {
        id: 'S1',
        title: '¿Qué tan alineadas sientes tus acciones diarias con tus valores personales?',
        type: 'single',
        options: [
          { value: 'not_aligned', label: 'Nada alineadas' },
          { value: 'slightly_aligned', label: 'Poco alineadas' },
          { value: 'partially_aligned', label: 'Parcialmente alineadas' },
          { value: 'very_aligned', label: 'Muy alineadas' },
          { value: 'fully_aligned', label: 'Completamente alineadas' },
        ],
      },
      {
        id: 'S2',
        title: '¿Qué prácticas realizas para cultivar tu bienestar interior?',
        type: 'multi',
        options: [
          { value: 'meditation', label: 'Meditación / respiración' },
          { value: 'gratitude', label: 'Gratitud / journaling' },
          { value: 'creative_space', label: 'Espacios creativos' },
          { value: 'service', label: 'Servicio o voluntariado' },
          { value: 'religious_practice', label: 'Ritos o prácticas religiosas' },
          { value: 'time_in_nature', label: 'Tiempo en naturaleza' },
          { value: 'none', label: 'Actualmente ninguna', exclusive: true },
        ],
      },
      {
        id: 'S3',
        title: '¿Qué nivel de sentido de propósito percibes en tu vida actualmente?',
        type: 'likert',
        options: [
          { value: 'very_low', label: 'Muy bajo' },
          { value: 'low', label: 'Bajo' },
          { value: 'moderate', label: 'Moderado' },
          { value: 'high', label: 'Alto' },
          { value: 'very_high', label: 'Muy alto' },
        ],
      },
      {
        id: 'S4',
        title: '¿Cuentas con una red o guía espiritual/filosófica cuando enfrentas retos?',
        type: 'compound',
      },
    ],
  },
];

import 'package:aura_mobile/features/body/domain/entities/activity_session.dart';
import 'package:aura_mobile/features/body/domain/entities/nutrition_log_entry.dart';
import 'package:aura_mobile/features/body/domain/entities/sleep_log.dart';
import 'package:aura_mobile/features/body/infrastructure/mappers/body_api_mapper.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('BodyApiMapper', () {
    test('mapSnapshot parses nested lists into domain entities', () {
      final snapshot = BodyApiMapper.mapSnapshot({
        'activities': [
          {
            'id': 'act-1',
            'activity_type': 'cardio',
            'intensity': 'high',
            'duration_minutes': 30,
            'session_date': '2025-10-10',
            'notes': 'Entrenamiento HIIT',
          },
        ],
        'nutrition': [
          {
            'id': 'meal-1',
            'meal_type': 'dinner',
            'timestamp': '2025-10-10T19:30:00Z',
            'items': ['Salmón', 'Verduras'],
            'calories': 620,
            'protein': 42,
            'carbs': 35,
            'fats': 22,
            'notes': 'Cena ligera',
          },
        ],
        'sleep': [
          {
            'id': 'sleep-1',
            'bedtime': '2025-10-10T23:00:00Z',
            'wake_time': '2025-10-11T07:00:00Z',
            'duration_hours': 8,
            'quality': 'excellent',
            'notes': 'Sin interrupciones',
          },
        ],
      });

      expect(snapshot.activities, isA<List<ActivitySession>>());
      expect(snapshot.nutrition, isA<List<NutritionLogEntry>>());
      expect(snapshot.sleep, isA<List<SleepLog>>());

      final activity = snapshot.activities.first;
      expect(activity.type, ActivityType.cardio);
      expect(activity.intensity, ActivityIntensity.high);
      expect(activity.durationMinutes, 30);

      final meal = snapshot.nutrition.first;
      expect(meal.mealType, MealType.dinner);
      expect(meal.calories, 620);
      expect(meal.protein, 42);
      expect(meal.carbs, 35);
      expect(meal.fats, 22);

      final sleep = snapshot.sleep.first;
      expect(sleep.quality, SleepQuality.excellent);
      expect(sleep.durationHours, 8);
    });

    test('activityToPayload emits ISO date and skips empty notes', () {
      final session = ActivitySession(
        id: 'any',
        type: ActivityType.flexibility,
        durationMinutes: 20,
        date: DateTime(2025, 10, 12),
        intensity: ActivityIntensity.low,
        notes: '',
      );

      final payload = BodyApiMapper.activityToPayload(session);
      expect(payload['activity_type'], 'flexibility');
      expect(payload['intensity'], 'low');
      expect(payload['duration_minutes'], 20);
      expect(payload['session_date'], '2025-10-12');
      expect(payload.containsKey('notes'), isFalse);
    });
  });
}

# Contributing to AURA360

Thank you for your interest in contributing to AURA360! This document provides guidelines and instructions for contributing.

## Development Setup

Please refer to the [README.md](./README.md) for initial setup instructions.

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Scopes
Use the service or app name:
- `mobile`: Flutter mobile app
- `web`: Angular web frontend
- `api`: Django backend
- `agents`: Agents service
- `vectordb`: Vector database service
- `pdf`: PDF extraction service
- `docs`: Documentation
- `core`: Cross-cutting concerns

### Examples
```bash
feat(mobile): add mood tagging functionality
fix(api): resolve JWT validation issue
docs(agents): update RAG pipeline documentation
chore(vectordb): upgrade Qdrant to v1.8.0
```

## Code Style

### Python
- Follow PEP 8
- 4-space indentation
- `snake_case` for functions/variables, `PascalCase` for classes
- Type hints on public APIs
- Docstrings for all public functions/classes

```python
def calculate_wellness_score(
    mind_score: float,
    body_score: float,
    soul_score: float
) -> float:
    """Calculate overall wellness score from component scores.

    Args:
        mind_score: Mental wellness score (0-100)
        body_score: Physical wellness score (0-100)
        soul_score: Spiritual wellness score (0-100)

    Returns:
        Overall wellness score (0-100)
    """
    return (mind_score + body_score + soul_score) / 3
```

### Flutter/Dart
- Follow [Effective Dart](https://dart.dev/guides/language/effective-dart)
- 2-space indentation
- `snake_case.dart` for filenames
- `PascalCase` for classes, `camelCase` for variables
- Trailing commas for better formatting
- Run `dart format .` before committing
- Resolve all `flutter analyze` warnings

```dart
class MoodEntry {
  final String id;
  final DateTime timestamp;
  final int moodLevel;
  final List<String> tags;

  const MoodEntry({
    required this.id,
    required this.timestamp,
    required this.moodLevel,
    required this.tags,
  });
}
```

### Angular/TypeScript
- Follow [Angular Style Guide](https://angular.io/guide/styleguide)
- 2-space indentation
- Single quotes for strings
- 100 character line width
- Run `ng lint` before committing

```typescript
export interface WellnessProfile {
  userId: string;
  mindScore: number;
  bodyScore: number;
  soulScore: number;
  lastUpdated: Date;
}
```

## Testing Guidelines

### Write Tests For
- All new features
- Bug fixes (regression tests)
- Public API changes
- Critical business logic

### Test Structure
- **Unit tests**: Fast, isolated tests for individual functions/classes
- **Integration tests**: Test interactions between components
- **E2E tests**: Test complete user flows

### Flutter Testing
```dart
// Mirror source structure in test/
// lib/features/mood/mood_controller.dart
// test/features/mood/mood_controller_test.dart

void main() {
  group('MoodController', () {
    test('should create mood entry', () {
      // Test implementation
    });
  });
}
```

### Python Testing
```python
# Use pytest
# tests/unit/ for unit tests
# tests/integration/ for integration tests

def test_wellness_score_calculation():
    score = calculate_wellness_score(80, 75, 85)
    assert score == 80.0
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Write clear, focused commits
   - Follow commit conventions
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and checks**
   ```bash
   # Mobile
   cd apps/mobile
   flutter analyze
   flutter test

   # Backend
   cd services/api
   uv run python manage.py test

   # Agents
   cd services/agents
   uv run pytest
   ```

4. **Push and create PR**
   ```bash
   git push origin feat/your-feature-name
   ```
   - Fill out the PR template
   - Link related issues
   - Request reviews

5. **Address review feedback**
   - Make requested changes
   - Push updates to the same branch
   - Respond to comments

6. **Merge**
   - Squash commits if needed
   - Ensure CI passes
   - Delete feature branch after merge

## Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feat/*`: Feature branches
- `fix/*`: Bug fix branches
- `hotfix/*`: Emergency production fixes

## Environment Variables

**Never commit sensitive data!**

- Use `.env.example` templates
- Document all required variables
- Use meaningful variable names with prefixes:
  - `AGENT_SERVICE_*` for agents service
  - `SUPABASE_*` for Supabase config
  - `QDRANT_*` for Qdrant config

## Documentation

- Update relevant docs in `/docs` when changing features
- Keep README.md up to date
- Document breaking changes prominently
- Include code examples in documentation

## Getting Help

- Check existing documentation in `/docs`
- Search existing issues
- Ask questions in discussions
- Reach out to maintainers

## Code Review Guidelines

When reviewing PRs:
- Be constructive and respectful
- Focus on code quality and maintainability
- Check for test coverage
- Verify documentation updates
- Test locally when needed

Thank you for contributing to AURA360!

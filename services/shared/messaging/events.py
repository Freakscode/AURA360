"""
Event Schemas for AURA360

Defines the structure of all events flowing through Kafka.
Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the system"""

    # User events
    USER_MOOD_CREATED = "user.mood.created"
    USER_ACTIVITY_CREATED = "user.activity.created"
    USER_IKIGAI_UPDATED = "user.ikigai.updated"
    USER_PROFILE_UPDATED = "user.profile.updated"

    # Context aggregation events
    CONTEXT_AGGREGATED = "context.aggregated"
    CONTEXT_VECTORIZED = "context.vectorized"

    # Guardian events
    GUARDIAN_REQUEST = "guardian.request"
    GUARDIAN_RESPONSE = "guardian.response"
    GUARDIAN_RESPONSE_CHUNK = "guardian.response.chunk"

    # Vectordb events
    VECTORDB_INGEST_REQUESTED = "vectordb.ingest.requested"
    VECTORDB_INGEST_COMPLETED = "vectordb.ingest.completed"
    VECTORDB_INGEST_FAILED = "vectordb.ingest.failed"


class BaseEvent(BaseModel):
    """Base event structure for all events"""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None  # For distributed tracing
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# USER EVENTS
# ============================================================================


class UserEvent(BaseEvent):
    """User-related events (mood entries, activities, profile updates)"""

    data: Dict[str, Any]


class MoodCreatedEvent(UserEvent):
    """Event emitted when user creates a mood entry"""

    event_type: EventType = EventType.USER_MOOD_CREATED
    data: Dict[str, Any]  # Contains: mood_score, tags, notes, created_at

    @classmethod
    def from_mood_entry(
        cls,
        user_id: str,
        mood_data: dict,
        trace_id: Optional[str] = None
    ) -> "MoodCreatedEvent":
        return cls(
            user_id=user_id,
            trace_id=trace_id or str(uuid4()),
            data=mood_data
        )


class ActivityCreatedEvent(UserEvent):
    """Event emitted when user logs an activity"""

    event_type: EventType = EventType.USER_ACTIVITY_CREATED
    data: Dict[str, Any]  # Contains: activity_type, duration, calories, etc.


class IkigaiUpdatedEvent(UserEvent):
    """Event emitted when user updates IKIGAI profile"""

    event_type: EventType = EventType.USER_IKIGAI_UPDATED
    data: Dict[str, Any]  # Contains: passions, missions, vocations, professions


# ============================================================================
# CONTEXT EVENTS
# ============================================================================


class ContextEvent(BaseEvent):
    """Context aggregation and vectorization events"""

    context_data: Dict[str, Any]


class ContextAggregatedEvent(ContextEvent):
    """Event emitted after context is aggregated from multiple sources"""

    event_type: EventType = EventType.CONTEXT_AGGREGATED
    context_data: Dict[str, Any]
    # Contains: mood_summary, activity_summary, ikigai_summary, psychosocial_factors


class ContextVectorizedEvent(ContextEvent):
    """Event emitted after context is vectorized"""

    event_type: EventType = EventType.CONTEXT_VECTORIZED
    context_data: Dict[str, Any]
    vectors: List[List[float]]
    embedding_model: str
    embedding_version: str


# ============================================================================
# GUARDIAN EVENTS
# ============================================================================


class GuardianEvent(BaseEvent):
    """Guardian-related events (requests and responses)"""

    guardian_type: str  # "mental", "physical", "spiritual", "holistic"


class GuardianRequestEvent(GuardianEvent):
    """Event to request advice from a Guardian"""

    event_type: EventType = EventType.GUARDIAN_REQUEST
    query: str
    context: Dict[str, Any]
    request_id: UUID = Field(default_factory=uuid4)  # For request-reply correlation

    @classmethod
    def create(
        cls,
        user_id: str,
        guardian_type: str,
        query: str,
        context: dict,
        trace_id: Optional[str] = None
    ) -> "GuardianRequestEvent":
        return cls(
            user_id=user_id,
            guardian_type=guardian_type,
            query=query,
            context=context,
            trace_id=trace_id or str(uuid4())
        )


class GuardianResponseEvent(GuardianEvent):
    """Event containing Guardian's response"""

    event_type: EventType = EventType.GUARDIAN_RESPONSE
    request_id: UUID  # Correlation ID from request
    response: str
    confidence_score: float
    retrieval_context: List[Dict[str, Any]]
    processing_time_ms: float


class GuardianResponseChunkEvent(GuardianEvent):
    """Event for streaming Guardian responses (chunk by chunk)"""

    event_type: EventType = EventType.GUARDIAN_RESPONSE_CHUNK
    request_id: UUID
    chunk: str
    sequence: int
    is_final: bool = False


# ============================================================================
# VECTORDB EVENTS
# ============================================================================


class VectordbEvent(BaseEvent):
    """Vectordb ingestion events"""

    collection_name: str


class VectordbIngestRequestedEvent(VectordbEvent):
    """Event to request ingestion of vectors into Qdrant"""

    event_type: EventType = EventType.VECTORDB_INGEST_REQUESTED
    vectors: List[List[float]]
    payloads: List[Dict[str, Any]]
    ingest_id: UUID = Field(default_factory=uuid4)


class VectordbIngestCompletedEvent(VectordbEvent):
    """Event emitted after successful ingestion"""

    event_type: EventType = EventType.VECTORDB_INGEST_COMPLETED
    ingest_id: UUID
    num_vectors: int
    processing_time_ms: float


class VectordbIngestFailedEvent(VectordbEvent):
    """Event emitted when ingestion fails"""

    event_type: EventType = EventType.VECTORDB_INGEST_FAILED
    ingest_id: UUID
    error_message: str
    error_type: str


# ============================================================================
# EVENT REGISTRY
# ============================================================================

EVENT_TYPE_TO_CLASS = {
    EventType.USER_MOOD_CREATED: MoodCreatedEvent,
    EventType.USER_ACTIVITY_CREATED: ActivityCreatedEvent,
    EventType.USER_IKIGAI_UPDATED: IkigaiUpdatedEvent,
    EventType.CONTEXT_AGGREGATED: ContextAggregatedEvent,
    EventType.CONTEXT_VECTORIZED: ContextVectorizedEvent,
    EventType.GUARDIAN_REQUEST: GuardianRequestEvent,
    EventType.GUARDIAN_RESPONSE: GuardianResponseEvent,
    EventType.GUARDIAN_RESPONSE_CHUNK: GuardianResponseChunkEvent,
    EventType.VECTORDB_INGEST_REQUESTED: VectordbIngestRequestedEvent,
    EventType.VECTORDB_INGEST_COMPLETED: VectordbIngestCompletedEvent,
    EventType.VECTORDB_INGEST_FAILED: VectordbIngestFailedEvent,
}


def deserialize_event(event_type: str, data: dict) -> BaseEvent:
    """
    Deserialize JSON data into appropriate event class

    Args:
        event_type: String representation of EventType
        data: Dictionary containing event data

    Returns:
        Instance of appropriate event class
    """
    event_enum = EventType(event_type)
    event_class = EVENT_TYPE_TO_CLASS.get(event_enum, BaseEvent)
    return event_class(**data)

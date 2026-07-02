"""Data models for the social match system."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    """用户画像数据模型."""

    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    personality_traits: list[str] = Field(default_factory=list)
    social_preferences: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    vector: Optional[list[float]] = None  # 64-dim embedding
    conversation_history: list[dict] = Field(default_factory=list)
    created_at: str = Field(default_factory=datetime.now().isoformat)
    updated_at: str = Field(default_factory=datetime.now().isoformat)


class ChatMessage(BaseModel):
    """对话消息."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = Field(default_factory=datetime.now().isoformat)


class MatchResult(BaseModel):
    """匹配结果."""

    candidate_id: str
    candidate_name: str
    score: float  # 0.0 - 1.0
    reasons: list[str] = Field(default_factory=list)
    common_interests: list[str] = Field(default_factory=list)


class IceBreakerResponse(BaseModel):
    """破冰话术."""

    suggestion: str
    tone: str  # "casual", "professional", "humorous", etc.
    suggested_topics: list[str] = Field(default_factory=list)


class ConversationRequest(BaseModel):
    """对话请求."""

    session_id: str
    message: str


class MatchRequest(BaseModel):
    """匹配请求."""

    session_id: str
    limit: int = Field(default=50, ge=1, le=50)


class AgentResponse(BaseModel):
    """通用Agent响应."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

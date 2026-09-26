from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import strip_required


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> object:
        return strip_required(value)


class ChatSource(BaseModel):
    document_id: int
    title: str
    page_number: int | None = None
    snippet: str | None = None
    category: str | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    grounding: list[str] = Field(default_factory=list)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    sources: list[ChatSource] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    grounding: list[str] = Field(default_factory=list)
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

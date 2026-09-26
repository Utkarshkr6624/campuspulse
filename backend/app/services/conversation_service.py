"""Conversation persistence for CampusPulse AI."""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.ai.orchestrator import ChatOrchestrator, OrchestratorResult
from app.ai.provider import ChatMessage
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db.session import commit_or_conflict
from app.models.conversation import Conversation, Message
from app.schemas.ai import (
    ChatResponse,
    ChatSource,
    ConversationRead,
    ConversationSummary,
    MessageRead,
)


def list_conversations(db: Session, student_id: int) -> list[ConversationSummary]:
    statement = (
        select(Conversation, func.count(Message.id))
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.student_id == student_id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    )
    rows = db.execute(statement).all()
    return [
        ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=count,
        )
        for conversation, count in rows
    ]


def get_conversation(db: Session, student_id: int, conversation_id: int) -> Conversation:
    statement = (
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.student_id == student_id)
        .options(joinedload(Conversation.messages))
    )
    conversation = db.scalars(statement).unique().first()
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return conversation


def get_conversation_read(db: Session, student_id: int, conversation_id: int) -> ConversationRead:
    conversation = get_conversation(db, student_id, conversation_id)
    return ConversationRead(
        id=conversation.id,
        student_id=conversation.student_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[serialize_message(item) for item in conversation.messages],
    )


def delete_conversation(db: Session, student_id: int, conversation_id: int) -> None:
    conversation = get_conversation(db, student_id, conversation_id)
    db.delete(conversation)
    commit_or_conflict(db, "Conversation could not be deleted.")


def chat(db: Session, student_id: int, message: str, conversation_id: int | None = None) -> ChatResponse:
    if conversation_id is None:
        conversation = Conversation(student_id=student_id, title=_title_from_message(message))
        db.add(conversation)
        commit_or_conflict(db, "Conversation could not be created.")
        db.refresh(conversation)
    else:
        conversation = get_conversation(db, student_id, conversation_id)

    user_message = Message(
        conversation_id=conversation.id,
        role="USER",
        content=message,
    )
    db.add(user_message)
    commit_or_conflict(db, "Message could not be saved.")
    db.refresh(user_message)

    # Reload conversation messages for prior history (exclude the just-saved user turn).
    conversation = get_conversation(db, student_id, conversation.id)
    history = [
        ChatMessage(role="user" if item.role == "USER" else "assistant", content=item.content)
        for item in conversation.messages
        if item.role in {"USER", "ASSISTANT"} and item.id != user_message.id
    ][-settings.ai_max_history_messages :]

    orchestrator = ChatOrchestrator(db, student_id)
    result = orchestrator.handle(message, history=history)

    assistant = Message(
        conversation_id=conversation.id,
        role="ASSISTANT",
        content=result.answer,
        sources_json=_dump_sources(result),
        tools_json=json.dumps(result.tools_used),
        grounding_json=json.dumps(result.grounding),
    )
    db.add(assistant)
    if conversation.title == "New conversation":
        conversation.title = _title_from_message(message)
    commit_or_conflict(db, "Assistant reply could not be saved.")
    db.refresh(assistant)

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant.id,
        answer=result.answer,
        sources=[
            ChatSource(
                document_id=item.document_id,
                title=item.title,
                page_number=item.page_number,
                snippet=item.snippet,
                category=item.category,
            )
            for item in result.sources
        ],
        tools_used=result.tools_used,
        grounding=result.grounding,
    )


def serialize_message(message: Message) -> MessageRead:
    return MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        sources=_load_sources(message.sources_json),
        tools_used=_load_list(message.tools_json),
        grounding=_load_list(message.grounding_json),
        created_at=message.created_at,
    )


def _title_from_message(message: str) -> str:
    cleaned = " ".join(message.split()).strip()
    return cleaned[:80] if cleaned else "New conversation"


def _dump_sources(result: OrchestratorResult) -> str:
    return json.dumps(
        [
            {
                "document_id": item.document_id,
                "title": item.title,
                "page_number": item.page_number,
                "snippet": item.snippet,
                "category": item.category,
            }
            for item in result.sources
        ]
    )


def _load_sources(raw: str | None) -> list[ChatSource]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [ChatSource(**item) for item in payload]


def _load_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in payload]

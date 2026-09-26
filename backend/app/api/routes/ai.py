from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.ai import ChatRequest, ChatResponse, ConversationRead, ConversationSummary
from app.services import conversation_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    payload: ChatRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ChatResponse:
    return conversation_service.chat(
        db,
        student.id,
        payload.message,
        conversation_id=payload.conversation_id,
    )


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    return conversation_service.list_conversations(db, student.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ConversationRead:
    return conversation_service.get_conversation_read(db, student.id, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    conversation_service.delete_conversation(db, student.id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

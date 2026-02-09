"""
Chat API Endpoints

Real-time chat and conversation management with AI agents.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ..v1.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


# ============== Schemas ==============

class MessageRequest(BaseModel):
    """Send a message to the chat agent"""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    agent_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """A single chat message matching frontend ApiChatMessage"""
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ChatAction(BaseModel):
    """An action suggestion"""
    label: str
    action: str
    data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Response from chat agent - matches frontend ApiChatMessageResponse"""
    conversation_id: str
    message: ChatMessage
    suggestions: List[str] = []
    actions: List[ChatAction] = []


class ConversationInfo(BaseModel):
    """Conversation summary"""
    id: str
    title: Optional[str] = None
    agent_name: str
    message_count: int
    is_active: bool
    started_at: datetime
    last_message_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """Full conversation with messages"""
    id: str
    title: Optional[str] = None
    agent_name: str
    messages: List[Dict[str, Any]]
    context_data: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    last_message_at: datetime



# ============== In-Memory Storage (for demo) ==============

# In production, use database
_conversations: Dict[str, Dict[str, Any]] = {}
_active_connections: Dict[str, List[WebSocket]] = {}


# ============== Endpoints ==============

@router.post("", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the chat agent.

    If conversation_id is not provided, a new conversation is started.
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    user_id = current_user.get("id", "")

    # Get or create conversation
    conversation_id = request.conversation_id or str(uuid4())

    if conversation_id not in _conversations:
        _conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "agent_name": "chat_agent",
            "messages": [],
            "context_data": {},
            "started_at": datetime.utcnow().isoformat(),
            "last_message_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

    conversation = _conversations[conversation_id]

    # Add user message
    user_message = {
        "id": str(uuid4()),
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    conversation["messages"].append(user_message)

    # Get agent response
    try:
        result = await orchestrator.chat(
            message=request.message,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db,
        )

        # Add agent response to conversation
        now = datetime.utcnow().isoformat()
        agent_message = {
            "id": str(uuid4()),
            "role": "assistant",
            "content": result.message,
            "agent_name": result.agent_name,
            "timestamp": now,
            "metadata": result.output,
        }
        conversation["messages"].append(agent_message)
        conversation["last_message_at"] = now

        # Extract suggestions from output
        suggestions = result.output.get("suggestions", [])

        # Build actions list
        actions = [
            ChatAction(label=a.get("label", ""), action=a.get("action", ""), data=a.get("data"))
            for a in (result.actions or [])
        ]

        return MessageResponse(
            conversation_id=conversation_id,
            message=ChatMessage(
                role="assistant",
                content=result.message,
                timestamp=now,
                metadata=result.output,
            ),
            suggestions=suggestions,
            actions=actions,
        )

    except Exception as e:
        # Fallback response on error
        now = datetime.utcnow().isoformat()
        error_msg = {
            "id": str(uuid4()),
            "role": "assistant",
            "content": "I'm having trouble processing that. Could you try again?",
            "agent_name": "chat_agent",
            "timestamp": now,
        }
        conversation["messages"].append(error_msg)

        return MessageResponse(
            conversation_id=conversation_id,
            message=ChatMessage(
                role="assistant",
                content=error_msg["content"],
                timestamp=now,
                metadata={"error": str(e)},
            ),
            suggestions=["Show my tasks", "I need help", "What can you do?"],
            actions=[],
        )


@router.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's conversations.
    """
    user_id = current_user.get("id", "")

    # Filter conversations for this user
    user_conversations = [
        conv for conv in _conversations.values()
        if conv.get("user_id") == user_id
    ]

    # Apply active filter
    if is_active is not None:
        user_conversations = [
            conv for conv in user_conversations
            if conv.get("is_active") == is_active
        ]

    # Sort by last message
    user_conversations.sort(
        key=lambda c: c.get("last_message_at", ""),
        reverse=True
    )

    # Apply limit
    user_conversations = user_conversations[:limit]

    return [
        ConversationInfo(
            id=conv["id"],
            title=conv.get("title") or _generate_title(conv),
            agent_name=conv.get("agent_name", "chat_agent"),
            message_count=len(conv.get("messages", [])),
            is_active=conv.get("is_active", True),
            started_at=datetime.fromisoformat(conv["started_at"]),
            last_message_at=datetime.fromisoformat(conv["last_message_at"]),
        )
        for conv in user_conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific conversation with all messages.
    """
    user_id = current_user.get("id", "")

    conversation = _conversations.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this conversation"
        )

    # Normalize message roles: "agent" → "assistant"
    messages = []
    for m in conversation.get("messages", []):
        msg = dict(m)
        if msg.get("role") == "agent":
            msg["role"] = "assistant"
        messages.append(msg)

    return ConversationDetail(
        id=conversation["id"],
        title=conversation.get("title") or _generate_title(conversation),
        agent_name=conversation.get("agent_name", "chat_agent"),
        messages=messages,
        context_data=conversation.get("context_data", {}),
        started_at=datetime.fromisoformat(conversation["started_at"]),
        last_message_at=datetime.fromisoformat(conversation["last_message_at"]),
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation.
    """
    user_id = current_user.get("id", "")

    conversation = _conversations.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation"
        )

    del _conversations[conversation_id]

    return {"message": "Conversation deleted", "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    End an active conversation.
    """
    user_id = current_user.get("id", "")

    conversation = _conversations.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to end this conversation"
        )

    conversation["is_active"] = False

    return {"message": "Conversation ended", "conversation_id": conversation_id}


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Clients send messages and receive responses in real-time.
    """
    await websocket.accept()

    user_id = None
    conversation_id = None

    try:
        # Expect initial auth message
        auth_data = await websocket.receive_json()
        user_id = auth_data.get("user_id")
        conversation_id = auth_data.get("conversation_id") or str(uuid4())

        if not user_id:
            await websocket.send_json({"error": "Authentication required"})
            await websocket.close()
            return

        # Track connection
        if user_id not in _active_connections:
            _active_connections[user_id] = []
        _active_connections[user_id].append(websocket)

        # Send confirmation
        await websocket.send_json({
            "type": "connected",
            "conversation_id": conversation_id,
        })

        # Create conversation if needed
        if conversation_id not in _conversations:
            _conversations[conversation_id] = {
                "id": conversation_id,
                "user_id": user_id,
                "agent_name": "chat_agent",
                "messages": [],
                "context_data": {},
                "started_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }

        # Message loop
        from ...agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            # Add user message
            conversation = _conversations[conversation_id]
            user_message = {
                "id": str(uuid4()),
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
            conversation["messages"].append(user_message)

            # Send typing indicator
            await websocket.send_json({"type": "typing", "agent": "chat_agent"})

            # Get response
            try:
                result = await orchestrator.chat(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

                agent_message = {
                    "id": str(uuid4()),
                    "role": "assistant",
                    "content": result.message,
                    "agent_name": result.agent_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": result.output,
                }
                conversation["messages"].append(agent_message)
                conversation["last_message_at"] = datetime.utcnow().isoformat()

                await websocket.send_json({
                    "type": "message",
                    "message_id": agent_message["id"],
                    "content": result.message,
                    "agent_name": result.agent_name,
                    "timestamp": agent_message["timestamp"],
                    "suggestions": result.output.get("suggestions", []),
                    "actions": result.actions,
                })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": "I'm having trouble processing that. Please try again.",
                    "error": str(e),
                })

    except WebSocketDisconnect:
        # Clean up connection
        if user_id and user_id in _active_connections:
            _active_connections[user_id] = [
                ws for ws in _active_connections[user_id]
                if ws != websocket
            ]
            if not _active_connections[user_id]:
                del _active_connections[user_id]

    except Exception as e:
        # Handle other errors
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except:
            pass


# ============== Helper Functions ==============

def _generate_title(conversation: Dict[str, Any]) -> str:
    """Generate a title from the first message"""
    messages = conversation.get("messages", [])
    if not messages:
        return "New Conversation"

    first_message = messages[0].get("content", "")
    if len(first_message) > 50:
        return first_message[:47] + "..."
    return first_message or "New Conversation"

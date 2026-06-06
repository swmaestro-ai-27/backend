from fastapi import FastAPI, Depends, HTTPException, Request
import models
import schemas
from agents.adapters import DatabaseAgentAdapter
from agents.graphs.character_chat import AgentGenerationError, CharacterChatGraph
from agents.graphs.deduction_evaluate import DeductionEvaluateGraph
from database import SessionLocal, engine, migrate_sqlite_schema
from sqlalchemy.orm import Session


models.Base.metadata.create_all(bind=engine)
migrate_sqlite_schema(engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(request: Request) -> str:
    user_id = (
        request.headers.get("x-user-id")
        or request.headers.get("user-id")
        or request.headers.get("user_id")
    )
    if not user_id:
        raise HTTPException(status_code=422, detail="X-User-Id header is required")
    return user_id


# 단서 조회처리
@app.post("/api/clues/{clue_id}")
def update_clue_state(
    clue_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    try:
        adapter.get_clue(clue_id)
    except KeyError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Clue {clue_id} not found") from exc
    clue_state = (
        db.query(models.ClueState)
        .filter(models.ClueState.user_id == user_id)
        .filter(models.ClueState.clue_id == clue_id)
        .first()
    )

    if clue_state:
        clue_state.interacted = True
    else:
        clue_state = models.ClueState(user_id=user_id, clue_id=clue_id, interacted=True)
        db.add(clue_state)
        db.flush()

    db.commit()
    return {"message": f"Clue {clue_id} state updated successfully."}


# 단서 조회 여부
@app.get("/api/clues", response_model=schemas.ClueListResponse)
def get_clues(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    clue_list = (
        db.query(models.ClueState)
        .filter(models.ClueState.user_id == user_id)
        .all()
    )

    response = [
        schemas.ClueStateElement(
            user_id=c.user_id,
            clue_id=c.clue_id,
            interacted=c.interacted,
        )
        for c in clue_list
    ]

    return schemas.ClueListResponse(clues=response)


# 인물 조회처리
@app.post("/api/character/{character_id}")
def update_character_state(
    character_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    try:
        adapter.get_character(character_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Character {character_id} not found",
        ) from exc

    character_state = (
        db.query(models.CharacterState)
        .filter(models.CharacterState.user_id == user_id)
        .filter(models.CharacterState.character_id == character_id)
        .first()
    )

    if character_state:
        character_state.interacted = True
    else:
        character_state = models.CharacterState(
            user_id=user_id,
            character_id=character_id,
            interacted=True,
        )
        db.add(character_state)

    db.commit()
    return {"message": f"Character {character_id} state updated successfully."}


# 인물 조회 여부
@app.get("/api/characters", response_model=schemas.CharacterListResponse)
def get_characters(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    character_list = (
        db.query(models.CharacterState)
        .filter(models.CharacterState.user_id == user_id)
        .all()
    )

    response_data = [
        schemas.CharacterStateElement(
            user_id=ch.user_id,
            character_id=ch.character_id,
            interacted=ch.interacted,
        )
        for ch in character_list
    ]

    return schemas.CharacterListResponse(characters=response_data)


# 인물 대화 불러오기
@app.get("/api/characters/{character_id}/messages")
def get_character_messages(
    character_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    messages_from_db = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == user_id)
        .filter(models.ChatMessage.character_id == character_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )

    response_messages = [
        schemas.ChatMessageElement(
            id=m.id,
            user_id=m.user_id,
            sender=m.sender,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages_from_db
    ]

    return schemas.CharacterChatLogResponse(
        character_id=character_id,
        messages=response_messages,
    )


# 인물과 대화
@app.post("/api/characters/{character_id}/messages", response_model=schemas.ChatMessageResponse)
def create_character_message(
    character_id: int,
    payload: schemas.ChatMessageCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    graph = CharacterChatGraph(adapter)
    try:
        result = graph.invoke(
            {
                "user_id": user_id,
                "character_id": character_id,
                "user_message": payload.content,
            }
        )
    except KeyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=f"Character {character_id} not found",
        ) from exc
    except AgentGenerationError as exc:
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    db.commit()

    return schemas.ChatMessageResponse(
        character_id=character_id,
        content=result["content"],
    )

@app.post("/api/deductions", response_model=schemas.DeductionResponse)
def submit_deduction(
    payload: schemas.DeductionRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    graph = DeductionEvaluateGraph(adapter)
    result = graph.invoke(
        {
            "user_id": user_id,
            "content": payload.content,
            "selected_target_id": payload.character,
            "selected_clue_ids": payload.clues,
        }
    )
    return schemas.DeductionResponse(
        comment=result["comment"],
        result=result["result"],
    )

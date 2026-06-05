from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
import models
import schemas
from agents.adapters import DatabaseAgentAdapter
from agents.graphs.aria_clue_explain import AriaClueExplainGraph
from agents.graphs.character_chat import CharacterChatGraph
from agents.graphs.deduction_evaluate import DeductionEvaluateGraph
from database import SessionLocal, engine
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(user_id: str = Header(..., alias="user_id")) -> str:
    return user_id

# 단서 조회처리
@app.post("/api/clues/{clue_id}")
def update_clue_state(
    clue_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    # 있는지 확인
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

    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    graph = AriaClueExplainGraph(adapter)
    graph.invoke({"user_id": user_id, "clue_id": clue_id})
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
        schemas.ClueStateElement(user_id=c.user_id, clue_id=c.clue_id, interacted=c.interacted)
        for c in clue_list
    ]

    return schemas.ClueListResponse(clues= response)

# 인물 조회처리
@app.post("/api/characters/{character_id}")
def update_character_state(
    character_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):

    character_state = (
        db.query(models.CharacterState)
        .filter(models.CharacterState.user_id == user_id)
        .filter(models.CharacterState.character_id == character_id)
        .first()
    )

    if character_state:
        character_state.interacted = True
    else:
        character_state = models.CharacterState(user_id=user_id, character_id=character_id, interacted=True)
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

    # 명세서의 JSON 구조 {"characters": [...]} 형태로 변환 (characters_id 매칭)
    response_data = [
        schemas.CharacterStateElement(
            user_id=ch.user_id,
            characters_id=ch.character_id,
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
            created_at=m.created_at
        )
        for m in messages_from_db
    ]

    return schemas.CharacterChatLogResponse(
        character_id=character_id,
        messages=response_messages
    )

# 인물과 대화
@app.post("/api/characters/{character_id}/messages", response_model=schemas.ChatMessageResponse)
def create_character_message(
    character_id: int,
    payload: schemas.ChatMessageCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    adapter = DatabaseAgentAdapter(db, user_id=user_id)
    graph = CharacterChatGraph(adapter)
    result = graph.invoke(
        {
            "user_id": user_id,
            "character_id": character_id,
            "user_message": payload.content,
        }
    )
    db.commit()

    return schemas.ChatMessageResponse(
        character_id = character_id,
        content=result["content"]
    )

@app.post("/api/deductions", response_model = schemas.DeductionResponse)
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

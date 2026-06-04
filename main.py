from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel
from typing import Annotated
import models
import schemas
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

# 단서 조회처리
@app.post("/api/clues/{clue_id}")
def update_clue_state(user_id: Annotated[str, Header()], clue_id: int, db: Session = Depends(get_db)):
    # 있는지 확인
    clue_state = db.query(models.ClueState).filter(
        models.ClueState.clue_id == clue_id,
        models.ClueState.user_id == user_id
    ).first()

    if clue_state:
        clue_state.interacted = True
    else:
        clue_state = models.ClueState(clue_id = clue_id, interacted = True)
        db.add(clue_state)

    db.commit()
    return {"message": f"Clue {clue_id} state updated successfully."}

# 단서 조회 여부
@app.get("/api/clues", response_model=schemas.ClueListResponse)
def get_clues(user_id: Annotated[str, Header()], db: Session = Depends(get_db)):

    clue_list = db.query(models.ClueState).filter(
        models.ClueState.user_id == user_id
    ).all()

    response = [
        schemas.ClueStateElement(user_id=user_id, clue_id = c.clue_id, interacted = c.interacted)
        for c in clue_list
    ]

    return schemas.ClueListResponse(clues= response)

# 인물 조회처리
@app.post("/api/character/{character_id}")
def update_character_state(user_id: Annotated[str, Header()], character_id: int, db: Session = Depends(get_db)):

    character_state = db.query(models.CharacterState).filter(
        models.CharacterState.character_id == character_id,
        models.CharacterState.user_id == user_id
    ).first()

    if character_state:
        character_state.interacted = True
    else:
        character_state = models.CharacterState(character_id = character_id, interacted = True)

    db.commit()
    return {"message": f"Character {character_id} state updated successfully."}

# 인물 조회 여부
@app.get("/api/characters", response_model=schemas.CharacterListResponse)
def get_characters(user_id: Annotated[str, Header()], db: Session = Depends(get_db)):
    character_list = db.query(models.CharacterState).filter(
        models.CharacterState.user_id == user_id
    ).all()

    # 명세서의 JSON 구조 {"characters": [...]} 형태로 변환 (characters_id 매칭)
    response_data = [
        schemas.CharacterStateElement(user_id=user_id, characters_id=ch.character_id, interacted=ch.is_interacted)
        for ch in character_list
    ]

    return schemas.CharacterListResponse(characters=response_data)

# 인물 대화 불러오기
@app.get("/api/characters/{character_id}/messages")
def get_character_messages(user_id: Annotated[str, Header()], character_id: int, db: Session = Depends(get_db)):

    messages_from_db = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.character_id == character_id,
                models.ChatMessage.sender == user_id
            )
        .order_by(models.ChatMessage.createdAt.asc())
        .all()
    )

    response_messages = [
        schemas.ChatMessageElement(
            id=m.id,
            sender=m.sender,
            content=m.content,
            created_at=m.createdAt
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
    user_id: Annotated[str, Header()],
    character_id: int,
    payload: schemas.ChatMessageCreate,
    db: Session = Depends(get_db)
):
    user_msg = models.ChatMessage(user_id=user_id, sender = "me", character_id = character_id, content=payload.content)
    db.add(user_msg)

    reply_content = "이 곳에는 LLM의 응답이 들어가게 됨."

    system_msg = models.ChatMessage(user_id=user_id, sender = character_id, character_id = character_id, content = reply_content)
    db.add(system_msg)

    db.commit()

    return schemas.ChatMessageResponse(
        character_id = character_id,
        content=reply_content
    )

@app.post("/api/deductions", response_model = schemas.DeductionResponse)
def submit_deduction(payload: schemas.DeductionRequest):

    is_correct = False
    comment_msg = "틀렸음"

    # 추리 성공 조건


    return schemas.DeductionResponse(
        comment = comment_msg,
        result = is_correct
    )

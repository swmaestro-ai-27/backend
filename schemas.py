from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

# 단서 (Clues) 관련 스키마
# GET /api/clues 응답 내부의 개별 단서 객체
class ClueStateElement(BaseModel):
    user_id: str
    clue_id: int
    interacted: bool

    class Config:
        from_attributes = True

# GET /api/clues 최종 응답 구조
class ClueListResponse(BaseModel):
    clues: List[ClueStateElement]



# 인물 상태 (Characters State) 관련 스키마
# GET /api/characters 응답 내부의 개별 인물 객체
class CharacterStateElement(BaseModel):
    user_id: str
    characters_id: int  # 명세의 "characters_id" 반영
    interacted: bool

    class Config:
        from_attributes = True

# GET /api/characters 최종 응답 구조
class CharacterListResponse(BaseModel):
    characters: List[CharacterStateElement]



# 인물 대화 (Messages) 관련 스키마
# POST /api/characters/{characters_id}/messages 요청 바디
class ChatMessageCreate(BaseModel):
    content: str

# POST /api/characters/{characters_id}/messages 응답 구조
class ChatMessageResponse(BaseModel):
    character_id: int
    content: str

    class Config:
        from_attributes = True

# GET /api/characters/{characters_id}/messages 응답 내부의 개별 메시지 객체
class ChatMessageElement(BaseModel):
    id: int
    user_id: str
    sender: str
    content: str
    created_at: datetime = Field(alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True

# GET /api/characters/{characters_id}/messages 최종 응답 구조
class CharacterChatLogResponse(BaseModel):
    character_id: int     # 명세의 camelCase 반영
    messages: List[ChatMessageElement]



# 결과 제출 (Deductions) 관련 스키마
# POST /api/deductions 요청 바디
class DeductionRequest(BaseModel):
    content: str
    character: int       # 지목할 인물 ID
    clues: List[int]     # 뒷받침 증거 ID 리스트

# POST /api/deductions 응답 구조
class DeductionResponse(BaseModel):
    comment: str
    result: bool

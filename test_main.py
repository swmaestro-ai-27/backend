import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agents.adapters import DatabaseAgentAdapter
from main import app, get_db
import models

# 테스트용 데이터베이스 설정 (인메모리 SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테스트 데이터베이스 의존성 오버라이드
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 각 테스트 실행 전후로 데이터베이스 테이블 생성 및 삭제
@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db(monkeypatch):
    monkeypatch.setattr(
        DatabaseAgentAdapter,
        "generate_character_reply",
        lambda self, prompt, character, user_message, context_clues: (
            "이 곳에는 LLM의 응답이 들어가게 됨."
        ),
    )
    monkeypatch.setattr(
        DatabaseAgentAdapter,
        "generate_deduction_evaluation",
        lambda self, prompt: (
            '{"result": false, "comment": "ARIA API 오답 평가"}'
        ),
    )
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)

# --- 테스트 코드 ---

def test_update_clue_state_new():
    response = client.post("/api/clues/1", headers={"user-id": "testuser"})
    assert response.status_code == 200
    assert response.json() == {"message": "Clue 1 state updated successfully."}

    db = TestingSessionLocal()
    clue_state = db.query(models.ClueState).filter_by(user_id="testuser", clue_id=1).first()
    assert clue_state is not None
    assert clue_state.interacted is True
    db.close()

def test_update_clue_state_existing():
    # 먼저 상태 생성
    client.post("/api/clues/1", headers={"user-id": "testuser"})
    # 다시 호출하여 업데이트 테스트
    response = client.post("/api/clues/1", headers={"user-id": "testuser"})
    assert response.status_code == 200
    assert response.json() == {"message": "Clue 1 state updated successfully."}

def test_update_unknown_clue_returns_404():
    response = client.post("/api/clues/999", headers={"user-id": "testuser"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Clue 999 not found"

def test_update_clue_state_accepts_client_selected_clue():
    response = client.post("/api/clues/3", headers={"user-id": "testuser"})

    assert response.status_code == 200
    assert response.json() == {"message": "Clue 3 state updated successfully."}

def test_get_clues():
    client.post("/api/clues/1", headers={"user-id": "testuser"})
    client.post("/api/clues/2", headers={"user-id": "testuser"})

    response = client.get("/api/clues", headers={"user-id": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "clues" in data
    assert len(data["clues"]) == 2
    assert data["clues"][0]["clue_id"] == 1
    assert data["clues"][0]["interacted"] is True
    assert {clue["clue_id"] for clue in data["clues"]} == {1, 2}

def test_get_clues_empty():
    response = client.get("/api/clues", headers={"user-id": "newuser"})
    assert response.status_code == 200
    assert response.json() == {"clues": []}

def test_update_character_state():
    response = client.post("/api/character/1", headers={"user-id": "testuser"})
    assert response.status_code == 200
    assert response.json() == {"message": "Character 1 state updated successfully."}

    db = TestingSessionLocal()
    char_state = db.query(models.CharacterState).filter_by(user_id="testuser", character_id=1).first()
    assert char_state is not None
    assert char_state.interacted is True
    db.close()

def test_update_unknown_character_returns_404():
    response = client.post("/api/character/999", headers={"user-id": "testuser"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Character 999 not found"

def test_get_characters():
    client.post("/api/character/1", headers={"user-id": "testuser"})
    response = client.get("/api/characters", headers={"user-id": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert len(data["characters"]) == 1
    assert data["characters"][0]["character_id"] == 1
    assert data["characters"][0]["interacted"] is True

def test_get_character_messages_empty():
    response = client.get("/api/characters/1/messages", headers={"user-id": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["character_id"] == 1
    assert data["messages"] == []

def test_create_message_unknown_character_returns_404():
    response = client.post(
        "/api/characters/999/messages",
        headers={"user-id": "testuser"},
        json={"content": "Hello"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Character 999 not found"

def test_create_and_get_character_messages():
    # 메시지 생성
    response_post = client.post(
        "/api/characters/1/messages",
        headers={"user-id": "testuser"},
        json={"content": "Hello"}
    )
    assert response_post.status_code == 200
    data_post = response_post.json()
    assert data_post["character_id"] == 1
    assert data_post["content"] == "이 곳에는 LLM의 응답이 들어가게 됨."

    # 메시지 조회
    response_get = client.get("/api/characters/1/messages", headers={"user-id": "testuser"})
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert len(data_get["messages"]) == 2
    assert data_get["messages"][0]["sender"] == "me"
    assert data_get["messages"][0]["content"] == "Hello"
    assert data_get["messages"][1]["sender"] == "민재"

def test_submit_deduction():
    payload = {
        "content": "test deduction",
        "character": 1,
        "clues": [1, 2, 3]
    }
    response = client.post(
        "/api/deductions",
        headers={"user-id": "testuser"},
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert "comment" in data
    assert "result" in data
    assert data["result"] is False
    assert data["comment"] == "ARIA API 오답 평가"

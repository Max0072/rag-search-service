"""
Test API endpoints for call management

Tests for:
- POST /calls - Create a new call
- GET /calls/{call_id} - Get call by ID
- GET /calls - List calls with pagination
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.api.main import app
from app.database.main_db import get_main_db
from app.database.vector_db import get_vector_db

client = TestClient(app)


@pytest.fixture(scope="function")
def cleanup_test_call():
    """Cleanup fixture that runs after each test"""
    call_ids_to_clean = []

    def register_call(call_id: str):
        call_ids_to_clean.append(call_id)

    yield register_call

    # Cleanup after test
    main_db = get_main_db()
    vector_db = get_vector_db()

    for call_id in call_ids_to_clean:
        try:
            # Delete from vector DB
            vector_db.delete_by_call_id(call_id, index_type="chunks")
            vector_db.delete_by_call_id(call_id, index_type="summaries")
            # Delete from main DB
            main_db.delete_call(call_id)
        except Exception as e:
            print(f"Cleanup error for {call_id}: {e}")


def test_create_call(cleanup_test_call):
    """Test creating a new call via API"""
    call_id = "test-api-call-001"
    cleanup_test_call(call_id)

    # Create call via API
    response = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "Alice: Hello. Bob: Hi there. Alice: Let's discuss the project. Bob: Sounds good.",
        "summary": "Brief project discussion between Alice and Bob",
        "date": datetime.now().isoformat(),
        "attendants": ["Alice", "Bob"],
        "topic": "Project Discussion",
        "meeting_type": "internal",
        "duration_minutes": 15,
        "meta": {"priority": "medium"}
    })

    # Check response
    assert response.status_code == 201
    data = response.json()

    assert data["call_id"] == call_id
    assert data["topic"] == "Project Discussion"
    assert data["meeting_type"] == "internal"
    assert len(data["attendants"]) == 2
    assert "Alice" in data["attendants"]
    assert "Bob" in data["attendants"]
    assert data["chunks_count"] > 0
    assert data["created_at"] is not None


def test_get_call_by_id(cleanup_test_call):
    """Test retrieving a call by ID"""
    call_id = "test-api-call-002"
    cleanup_test_call(call_id)

    # First create a call
    create_response = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "Charlie: Good morning. Diana: Morning! Let's start.",
        "summary": "Morning standup",
        "date": datetime.now().isoformat(),
        "attendants": ["Charlie", "Diana"],
        "topic": "Daily Standup"
    })
    assert create_response.status_code == 201

    # Get the call by ID
    response = client.get(f"/api/v1/calls/{call_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["call_id"] == call_id
    assert data["topic"] == "Daily Standup"
    assert len(data["attendants"]) == 2


def test_get_nonexistent_call():
    """Test getting a call that doesn't exist"""
    response = client.get("/api/v1/calls/nonexistent-call-id")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_calls(cleanup_test_call):
    """Test listing calls with pagination"""
    # Create two test calls
    call_id_1 = "test-api-call-list-001"
    call_id_2 = "test-api-call-list-002"
    cleanup_test_call(call_id_1)
    cleanup_test_call(call_id_2)

    for call_id in [call_id_1, call_id_2]:
        client.post("/api/v1/calls", json={
            "call_id": call_id,
            "full_transcript": "Test transcript for listing",
            "summary": "Test summary",
            "date": datetime.now().isoformat(),
            "attendants": ["TestUser"],
            "topic": "Test Topic"
        })

    # List calls
    response = client.get("/api/v1/calls?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()

    assert "calls" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] >= 2

    # Check that our test calls are in the list
    call_ids = [call["call_id"] for call in data["calls"]]
    assert call_id_1 in call_ids or call_id_2 in call_ids


def test_list_calls_pagination(cleanup_test_call):
    """Test pagination parameters"""
    # Test with different limits
    response = client.get("/api/v1/calls?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert len(data["calls"]) <= 5

    # Test invalid limit
    response = client.get("/api/v1/calls?limit=200")
    assert response.status_code == 400

    # Test invalid offset
    response = client.get("/api/v1/calls?offset=-1")
    assert response.status_code == 400


def test_create_call_with_minimal_data(cleanup_test_call):
    """Test creating a call with only required fields"""
    call_id = "test-api-call-minimal"
    cleanup_test_call(call_id)

    response = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "Simple transcript.",
        "summary": "Simple summary",
        "date": datetime.now().isoformat(),
        "attendants": ["User1"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["call_id"] == call_id
    assert data["topic"] is None or data["topic"] == ""
    assert data["meeting_type"] is None or data["meeting_type"] == ""


def test_create_duplicate_call():
    """Test that creating a duplicate call_id fails gracefully"""
    call_id = "test-api-call-duplicate"

    # Create first call
    response1 = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "First transcript.",
        "summary": "First summary",
        "date": datetime.now().isoformat(),
        "attendants": ["User1"]
    })

    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "Second transcript.",
        "summary": "Second summary",
        "date": datetime.now().isoformat(),
        "attendants": ["User2"]
    })

    # Should fail with 500 or appropriate error
    assert response2.status_code == 500

    # Cleanup
    main_db = get_main_db()
    vector_db = get_vector_db()
    vector_db.delete_by_call_id(call_id, index_type="chunks")
    vector_db.delete_by_call_id(call_id, index_type="summaries")
    main_db.delete_call(call_id)


def test_delete_call(cleanup_test_call):
    """Test deleting a call via API"""
    call_id = "test-api-call-delete"
    cleanup_test_call(call_id)

    # First create a call
    create_response = client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "This will be deleted.",
        "summary": "Test deletion",
        "date": datetime.now().isoformat(),
        "attendants": ["User1"]
    })
    assert create_response.status_code == 201

    # Verify it exists
    get_response = client.get(f"/api/v1/calls/{call_id}")
    assert get_response.status_code == 200

    # Delete it
    delete_response = client.delete(f"/api/v1/calls/{call_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["call_id"] == call_id
    assert "deleted successfully" in data["message"]

    # Verify it's gone
    get_response_after = client.get(f"/api/v1/calls/{call_id}")
    assert get_response_after.status_code == 404


def test_delete_nonexistent_call():
    """Test deleting a call that doesn't exist"""
    response = client.delete("/api/v1/calls/nonexistent-call-delete")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_clear_all_databases():
    """Test clearing all databases"""
    # Create a test call
    call_id = "test-api-call-clear-all"
    client.post("/api/v1/calls", json={
        "call_id": call_id,
        "full_transcript": "Test for clear all.",
        "summary": "Will be cleared",
        "date": datetime.now().isoformat(),
        "attendants": ["User1"]
    })

    # Clear all databases
    response = client.delete("/api/v1/admin/clear-all")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert data["deleted_calls"] >= 1
    assert data["calls_after"] == 0

    # Verify all calls are gone
    list_response = client.get("/api/v1/calls?limit=100")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0
    assert len(list_response.json()["calls"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
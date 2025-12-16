"""Tests for user profile endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from db.session import get_db, Base, engine
from db.models.user import User, UserProfile
from core.security import get_password_hash

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_user(client, db_session):
    """Create and authenticate a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    profile = UserProfile(
        user_id=user.id,
        first_name="Test",
        last_name="User"
    )
    db_session.add(profile)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    return user, token


def test_get_profile(authenticated_user, client):
    """Test getting user profile."""
    user, token = authenticated_user
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


def test_update_profile(authenticated_user, client):
    """Test updating user profile."""
    user, token = authenticated_user
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "first_name": "Updated",
            "organization": "Test Org"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["organization"] == "Test Org"
    assert data["last_name"] == "User"  # Should remain unchanged


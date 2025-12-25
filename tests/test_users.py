# 사용자 API 테스트
import pytest


class TestUserRegistration:
    """회원가입 테스트"""

    def test_register_success(self, client):
        """회원가입 성공"""
        response = client.post(
            "/api/users",
            json={
                "email": "newuser@example.com",
                "password": "NewP@ssw0rd!",
                "name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["email"] == "newuser@example.com"
        assert data["payload"]["name"] == "New User"

    def test_register_duplicate_email(self, client, test_user):
        """이메일 중복으로 회원가입 실패"""
        response = client.post(
            "/api/users",
            json={
                "email": "user1@example.com",
                "password": "P@ssw0rd!",
                "name": "Duplicate User"
            }
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "DUPLICATE_EMAIL"

    def test_register_invalid_email(self, client):
        """잘못된 이메일 형식으로 회원가입 실패"""
        response = client.post(
            "/api/users",
            json={
                "email": "invalid-email",
                "password": "P@ssw0rd!",
                "name": "Test User"
            }
        )
        assert response.status_code == 422


class TestUserProfile:
    """사용자 프로필 테스트"""

    def test_get_my_profile(self, client, user_token):
        """내 정보 조회 성공"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["email"] == "user1@example.com"

    def test_get_my_profile_without_auth(self, client):
        """인증 없이 내 정보 조회 실패"""
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_update_my_profile(self, client, user_token):
        """내 정보 수정 성공"""
        response = client.patch(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["payload"]["name"] == "Updated Name"

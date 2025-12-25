# 인증 API 테스트
import pytest


class TestLogin:
    """로그인 테스트"""

    def test_login_success(self, client, test_user):
        """로그인 성공"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user1@example.com",
                "password": "P@ssw0rd!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "access_token" in data["payload"]
        assert "refresh_token" in data["payload"]
        assert data["payload"]["token_type"] == "bearer"

    def test_login_invalid_email(self, client):
        """존재하지 않는 이메일로 로그인 실패"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "P@ssw0rd!"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    def test_login_invalid_password(self, client, test_user):
        """잘못된 비밀번호로 로그인 실패"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user1@example.com",
                "password": "WrongPassword!"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"


class TestRefreshToken:
    """토큰 재발급 테스트"""

    def test_refresh_token_success(self, client, test_user):
        """Refresh Token으로 Access Token 재발급 성공"""
        # 로그인하여 토큰 획득
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "user1@example.com",
                "password": "P@ssw0rd!"
            }
        )
        refresh_token = login_response.json()["payload"]["refresh_token"]

        # 토큰 재발급
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "access_token" in data["payload"]


class TestLogout:
    """로그아웃 테스트"""

    def test_logout_success(self, client, user_token):
        """로그아웃 성공"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["message"] == "로그아웃 성공"

    def test_logout_without_token(self, client):
        """토큰 없이 로그아웃 실패"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401

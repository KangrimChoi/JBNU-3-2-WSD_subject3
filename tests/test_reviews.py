# 리뷰 API 테스트
import pytest
from src.models.review import Review


@pytest.fixture
def test_review(db_session, test_user, test_book):
    """테스트용 리뷰"""
    review = Review(
        user_id=test_user.id,
        book_id=test_book.id,
        rating=5,
        content="Great book!"
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


class TestReviewCreate:
    """리뷰 작성 테스트"""

    def test_create_review_success(self, client, user_token, test_book):
        """리뷰 작성 성공"""
        response = client.post(
            f"/api/books/{test_book.id}/reviews",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "rating": 4,
                "content": "Good book!"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_success"] is True
        assert "id" in data["payload"]
        assert "created_at" in data["payload"]

    def test_create_review_duplicate(self, client, user_token, test_book, test_review):
        """중복 리뷰 작성 실패"""
        response = client.post(
            f"/api/books/{test_book.id}/reviews",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "rating": 3,
                "content": "Another review"
            }
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "DUPLICATE_REVIEW"


class TestReviewRead:
    """리뷰 조회 테스트"""

    def test_get_reviews_list(self, client, test_book, test_review):
        """리뷰 목록 조회 성공"""
        response = client.get(f"/api/books/{test_book.id}/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "reviews" in data["payload"]


class TestReviewUpdate:
    """리뷰 수정 테스트"""

    def test_update_review_success(self, client, user_token, test_review):
        """리뷰 수정 성공"""
        response = client.patch(
            f"/api/reviews/{test_review.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "rating": 3,
                "content": "Updated review"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert "id" in data["payload"]
        assert "updated_at" in data["payload"]


class TestReviewDelete:
    """리뷰 삭제 테스트"""

    def test_delete_review_success(self, client, user_token, test_review):
        """리뷰 삭제 성공"""
        response = client.delete(
            f"/api/reviews/{test_review.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True

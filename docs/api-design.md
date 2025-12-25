# API 설계 문서

이 문서는 도서 관리 RESTful API의 설계 및 구현 내용을 정리한 문서입니다.

---

## 명세서와의 차이점 요약

### 1. Auth (인증)

| 항목 | 명세서 | 현재 구현 | 비고 |
|------|--------|----------|------|
| 로그인 응답 필드명 | `accessToken` (camelCase) | `access_token` (snake_case) | Python 컨벤션 준수 |
| 로그인 응답 내용 | `accessToken`만 반환 | `access_token`, `refresh_token`, `token_type` 반환 | 클라이언트 편의성 향상 |
| 토큰 갱신 요청 필드명 | `refreshToken` | `refresh_token` | Python 컨벤션 준수 |
| 토큰 갱신 응답 | `accessToken`, `refreshToken` 둘 다 반환 | `access_token`만 반환 | Refresh Token은 기존 것 유지 |

### 2. Users (사용자)

| 항목 | 명세서 | 현재 구현 | 비고 |
|------|--------|----------|------|
| `/users/me` 응답 | `password` 필드 포함 | `password` 필드 제외 | 보안상 비밀번호 노출 방지 |
| 추가 엔드포인트 | 없음 | `GET /api/users`, `GET /api/users/{id}` | 관리자 전용 기능 추가 |

### 3. Books (도서)

| 항목 | 명세서 | 현재 구현 | 비고 |
|------|--------|----------|------|
| 필드 네이밍 | `publicationDate` (camelCase) 혼용 | `publication_date` (snake_case 통일) | 일관성 유지 |
| 필수 필드 | 모든 필드 필수 | `description`, `cover_image_url`, `publication_date`는 Optional | 실용성 개선 |
| ISBN 형식 | 하이픈 포함 (978-0060935467) | 하이픈 없이 10~13자리 허용 | 유연한 입력 허용 |

---

## 공통 응답 형식

### 성공 응답 (APIResponse)
```json
{
  "is_success": true,
  "message": "작업 성공 메시지",
  "payload": { ... }
}
```

### 에러 응답 (ErrorResponse)
```json
{
  "timestamp": "2025-03-05T12:34:56Z",
  "path": "/api/endpoint",
  "status": 400,
  "code": "ERROR_CODE",
  "message": "에러 메시지",
  "details": { "field": "상세 에러 정보" }
}
```

### HTTP 상태 코드 (12종 이상)

| 코드 | 설명 | 사용 예시 |
|------|------|-----------|
| **200** OK | 성공 | GET, PATCH 성공 |
| **201** Created | 리소스 생성 성공 | POST 생성 성공 (회원가입, 도서 등록, 리뷰 작성) |
| **204** No Content | 삭제 성공 (응답 본문 없음) | DELETE 성공 (도서 삭제) |
| **307** Temporary Redirect | 임시 리다이렉트 | OAuth 로그인 리다이렉트 |
| **400** Bad Request | 잘못된 요청 | 유효성 검사 실패 |
| **401** Unauthorized | 인증 필요/실패 | 토큰 누락, 만료, 잘못된 자격증명 |
| **403** Forbidden | 권한 없음 | USER가 ADMIN 전용 API 호출 |
| **404** Not Found | 리소스 없음 | 존재하지 않는 도서/리뷰/댓글 조회 |
| **409** Conflict | 중복/충돌 | 이메일 중복, ISBN 중복, 중복 리뷰 |
| **422** Unprocessable Entity | 처리 불가 | Pydantic 유효성 검사 실패 (자동 처리) |
| **429** Too Many Requests | 요청 한도 초과 | Rate Limiting (분당 60회 초과) |
| **500** Internal Server Error | 서버 오류 | 예기치 않은 에러 |

### 에러 코드 목록
| HTTP | 코드 | 설명 |
|------|------|------|
| 400 | BAD_REQUEST | 잘못된 요청 형식 |
| 400 | VALIDATION_FAILED | 필드 유효성 검사 실패 |
| 401 | UNAUTHORIZED | 인증 필요/실패 |
| 401 | TOKEN_EXPIRED | 토큰 만료 |
| 401 | INVALID_REFRESH_TOKEN | Refresh Token 무효 |
| 401 | INVALID_CREDENTIALS | 이메일 또는 비밀번호 불일치 |
| 403 | FORBIDDEN | 접근 권한 없음 |
| 404 | BOOK_NOT_FOUND | 도서 없음 |
| 404 | USER_NOT_FOUND | 사용자 없음 |
| 404 | REVIEW_NOT_FOUND | 리뷰 없음 |
| 404 | COMMENT_NOT_FOUND | 댓글 없음 |
| 404 | LIBRARY_ITEM_NOT_FOUND | 서재 항목 없음 |
| 404 | WISHLIST_ITEM_NOT_FOUND | 위시리스트 항목 없음 |
| 404 | LIKE_NOT_FOUND | 좋아요 없음 |
| 409 | DUPLICATE_EMAIL | 이메일 중복 |
| 409 | DUPLICATE_ISBN | ISBN 중복 |
| 409 | DUPLICATE_REVIEW | 중복 리뷰 |
| 409 | DUPLICATE_LIKE | 중복 좋아요 |
| 409 | DUPLICATE_LIBRARY_ITEM | 서재 중복 |
| 409 | DUPLICATE_WISHLIST_ITEM | 위시리스트 중복 |
| 500 | INTERNAL_SERVER_ERROR | 서버 오류 |

---

## API 엔드포인트 상세

### 1. 인증 API (Auth)

#### POST /api/auth/login - 로그인
JWT 토큰을 발급받습니다.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!"
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "로그인 성공",
  "payload": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

**Errors:**
- 401: 이메일 또는 비밀번호 불일치

---

#### GET /api/auth/google - Google 소셜 로그인
Google OAuth 2.0 인증 페이지로 리다이렉트합니다.

**Response (307):**
리다이렉트: `https://accounts.google.com/o/oauth2/v2/auth?...`

---

#### GET /api/auth/google/callback - Google OAuth 콜백
Google 인증 후 콜백을 처리하고 JWT 토큰을 발급합니다.

**Query Parameters:**
- `code`: Google 인증 코드 (자동 전달)
- `state`: CSRF 방지 토큰 (자동 전달)

**Response (200):**
```json
{
  "is_success": true,
  "message": "Google 로그인 성공",
  "payload": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@gmail.com",
      "name": "Google User"
    }
  }
}
```

**Errors:**
- 401: Google 인증 실패

---

#### POST /api/auth/firebase - Firebase 인증
Firebase ID Token을 검증하고 JWT 토큰을 발급합니다.

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "Firebase 인증 성공",
  "payload": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "Firebase User"
    }
  }
}
```

**Errors:**
- 401: 유효하지 않은 Firebase ID Token

---

#### POST /api/auth/refresh - 토큰 갱신
Refresh Token으로 새로운 Access Token을 발급받습니다.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "토큰 갱신 성공",
  "payload": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

**Errors:**
- 401: 유효하지 않거나 만료된 Refresh Token

---

#### POST /api/auth/logout - 로그아웃
현재 토큰을 무효화합니다. (인증 필요)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "로그아웃 성공",
  "payload": null
}
```

---

### 2. 사용자 API (Users)

#### POST /api/users - 회원가입

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!",
  "name": "홍길동"
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "회원가입이 정상적으로 진행되었습니다.",
  "payload": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "created_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 409: 이메일 중복 (DUPLICATE_EMAIL)
- 422: 입력값 검증 실패

---

#### GET /api/users/me - 내 정보 조회 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "프로필 조회 성공",
  "payload": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "role": "user",
    "updated_at": "2025-03-05T12:34:56"
  }
}
```

---

#### PATCH /api/users/me - 내 정보 수정 (인증 필요)

**Request Body (이름 변경):**
```json
{
  "name": "김철수"
}
```

**Request Body (비밀번호 변경):**
```json
{
  "current_password": "P@ssw0rd!",
  "new_password": "NewP@ss1!"
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "프로필 수정 성공",
  "payload": {
    "id": 1,
    "email": "user@example.com",
    "name": "김철수",
    "role": "user",
    "updated_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 400: 수정 내용 없음
- 401: 현재 비밀번호 불일치
- 403: 관리자 계정 수정 불가

---

#### DELETE /api/users/me - 회원 탈퇴 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "회원 탈퇴가 완료되었습니다",
  "payload": null
}
```

**Errors:**
- 403: 관리자 계정 삭제 불가

---

#### GET /api/users - 사용자 목록 조회 (ADMIN 전용)

**Response (200):**
```json
{
  "is_success": true,
  "message": "사용자 목록 조회 성공",
  "payload": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "홍길동",
      "role": "user",
      "updated_at": "2025-03-05T12:34:56"
    }
  ]
}
```

---

#### GET /api/users/{user_id} - 특정 사용자 조회 (ADMIN 전용)

**Response (200):**
```json
{
  "is_success": true,
  "message": "사용자 조회 성공",
  "payload": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "role": "user",
    "updated_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 404: 사용자를 찾을 수 없음 (USER_NOT_FOUND)

---

### 3. 도서 API (Books)

#### POST /api/books - 도서 등록 (ADMIN 전용)

**Request Body:**
```json
{
  "title": "앵무새 죽이기",
  "categories": ["문학", "영미소설"],
  "authors": ["하퍼 리"],
  "description": "인종차별이 심했던 앨라배마 주를 배경으로 다룬 소설이다.",
  "isbn": "9780060935467",
  "cover_image_url": "https://example.com/images/book.png",
  "price": 35000,
  "publication_date": "1960-07-11"
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "도서가 성공적으로 등록되었습니다.",
  "payload": {
    "id": 1,
    "title": "앵무새 죽이기",
    "categories": ["문학", "영미소설"],
    "authors": ["하퍼 리"],
    "description": "인종차별이 심했던 앨라배마 주를 배경으로 다룬 소설이다.",
    "isbn": "9780060935467",
    "cover_image_url": "https://example.com/images/book.png",
    "price": 35000,
    "publication_date": "1960-07-11",
    "created_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 409: ISBN 중복 (DUPLICATE_ISBN)

---

#### GET /api/books - 도서 목록 조회

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `category`: 카테고리 필터 (선택)
- `sort_by`: 정렬 기준 (0: 내림차순/최신순, 1: 오름차순/오래된순)

**Response (200):**
```json
{
  "is_success": true,
  "message": "도서 목록 조회에 성공했습니다.",
  "payload": {
    "books": [
      {
        "id": 1,
        "title": "앵무새 죽이기",
        "categories": ["문학", "영미소설"],
        "authors": ["하퍼 리"],
        "description": "인종차별이 심했던 앨라배마 주를 배경으로 다룬 소설이다.",
        "isbn": "9780060935467",
        "cover_image_url": "https://example.com/images/book.png",
        "price": 35000,
        "publication_date": "1960-07-11"
      }
    ],
    "pagination": {
      "total_books": 153,
      "total_pages": 8,
      "current_page": 1,
      "page_size": 20,
      "page_sort": 0
    }
  }
}
```

---

#### GET /api/books/{book_id} - 도서 상세 조회

**Response (200):**
```json
{
  "is_success": true,
  "message": "도서 상세 조회에 성공했습니다.",
  "payload": {
    "id": 1,
    "title": "앵무새 죽이기",
    "categories": ["문학", "영미소설"],
    "authors": ["하퍼 리"],
    "description": "인종차별이 심했던 앨라배마 주를 배경으로 다룬 소설이다.",
    "isbn": "9780060935467",
    "cover_image_url": "https://example.com/images/book.png",
    "price": 35000,
    "publication_date": "1960-07-11"
  }
}
```

**Errors:**
- 404: 도서를 찾을 수 없음 (BOOK_NOT_FOUND)

---

#### PATCH /api/books/{book_id} - 도서 수정 (ADMIN 전용)

**Request Body (부분 수정 가능):**
```json
{
  "title": "수정된 제목",
  "price": 40000
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "도서가 성공적으로 수정되었습니다.",
  "payload": { ... }
}
```

**Errors:**
- 404: 도서를 찾을 수 없음
- 409: ISBN 중복

---

#### DELETE /api/books/{book_id} - 도서 삭제 (ADMIN 전용, Soft Delete)

**Response (200):**
```json
{
  "is_success": true,
  "message": "도서를 성공적으로 삭제했습니다.",
  "payload": null
}
```

---

### 4. 리뷰 API (Reviews)

#### POST /api/books/{book_id}/reviews - 리뷰 작성 (인증 필요)
한 사용자가 같은 도서에 중복 리뷰 불가

**Request Body:**
```json
{
  "content": "정말 좋은 책입니다!",
  "rating": 5
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "리뷰가 성공적으로 작성되었습니다.",
  "payload": {
    "id": 1,
    "created_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 404: 도서를 찾을 수 없음
- 409: 이미 리뷰 작성함 (DUPLICATE_REVIEW)

---

#### GET /api/books/{book_id}/reviews - 리뷰 목록 조회

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `size`: 페이지당 리뷰 수 (기본값: 10)

**Response (200):**
```json
{
  "is_success": true,
  "message": "리뷰 목록이 성공적으로 조회되었습니다.",
  "payload": {
    "reviews": [
      {
        "id": 1,
        "author": { "name": "홍길동" },
        "content": "정말 좋은 책입니다!",
        "rating": 5,
        "created_at": "2025-03-05T12:34:56"
      }
    ],
    "pagination": {
      "page": 1,
      "totalPages": 5,
      "totalElements": 50
    }
  }
}
```

---

#### GET /api/books/{book_id}/reviews/top - Top-N 리뷰 조회 (좋아요 순)

**Query Parameters:**
- `limit`: 조회할 리뷰 수 (기본값: 10, 최대: 50)

**Response (200):**
```json
{
  "is_success": true,
  "message": "Top 리뷰 목록이 성공적으로 조회되었습니다.",
  "payload": {
    "reviews": [
      {
        "id": 1,
        "author": { "name": "홍길동" },
        "content": "정말 좋은 책입니다!",
        "rating": 5,
        "like_count": 42,
        "created_at": "2025-03-05T12:34:56"
      }
    ]
  }
}
```

---

#### PATCH /api/reviews/{review_id} - 리뷰 수정 (인증 필요, 본인만)

**Request Body:**
```json
{
  "content": "수정된 리뷰 내용",
  "rating": 4
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "리뷰가 성공적으로 수정되었습니다.",
  "payload": {
    "id": 1,
    "updated_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 403: 본인 리뷰만 수정 가능
- 404: 리뷰를 찾을 수 없음

---

#### DELETE /api/reviews/{review_id} - 리뷰 삭제 (인증 필요, 본인만)

**Response (200):**
```json
{
  "is_success": true,
  "message": "리뷰가 성공적으로 삭제되었습니다.",
  "payload": { "id": 1 }
}
```

---

#### POST /api/reviews/{review_id}/like - 리뷰 좋아요 (인증 필요)

**Response (201):**
```json
{
  "is_success": true,
  "message": "좋아요가 등록되었습니다.",
  "payload": {
    "review_id": 1,
    "created_at": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 409: 이미 좋아요 누름 (DUPLICATE_LIKE)

---

#### DELETE /api/reviews/{review_id}/like - 리뷰 좋아요 취소 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "좋아요가 취소되었습니다.",
  "payload": null
}
```

**Errors:**
- 404: 좋아요를 누르지 않은 리뷰 (LIKE_NOT_FOUND)

---

### 5. 댓글 API (Comments)

#### POST /api/books/{book_id}/comments - 댓글 작성 (인증 필요)

**Request Body:**
```json
{
  "content": "댓글 내용입니다."
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "댓글이 성공적으로 작성되었습니다.",
  "payload": {
    "id": 1,
    "created_at": "2025-03-05T12:34:56"
  }
}
```

---

#### GET /api/books/{book_id}/comments - 댓글 목록 조회

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `size`: 페이지당 댓글 수 (기본값: 10)

**Response (200):**
```json
{
  "is_success": true,
  "message": "댓글 목록이 성공적으로 조회되었습니다.",
  "payload": {
    "comments": [
      {
        "id": 1,
        "author": { "name": "홍길동" },
        "content": "댓글 내용입니다.",
        "created_at": "2025-03-05T12:34:56"
      }
    ],
    "pagination": {
      "page": 1,
      "totalPages": 5,
      "totalElements": 50
    }
  }
}
```

---

#### PATCH /api/comments/{comment_id} - 댓글 수정 (인증 필요, 본인만)

**Request Body:**
```json
{
  "content": "수정된 댓글 내용"
}
```

**Response (200):**
```json
{
  "is_success": true,
  "message": "댓글이 성공적으로 수정되었습니다.",
  "payload": {
    "id": 1,
    "updated_at": "2025-03-05T12:34:56"
  }
}
```

---

#### DELETE /api/comments/{comment_id} - 댓글 삭제 (인증 필요, 본인만)

**Response (200):**
```json
{
  "is_success": true,
  "message": "댓글이 성공적으로 삭제되었습니다.",
  "payload": { "id": 1 }
}
```

---

#### POST /api/comments/{comment_id}/like - 댓글 좋아요 (인증 필요)

**Response (201):**
```json
{
  "is_success": true,
  "message": "좋아요가 등록되었습니다.",
  "payload": {
    "comment_id": 1,
    "created_at": "2025-03-05T12:34:56"
  }
}
```

---

#### DELETE /api/comments/{comment_id}/like - 댓글 좋아요 취소 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "좋아요가 취소되었습니다.",
  "payload": null
}
```

---

### 6. 내 서재 API (Library)

#### POST /api/me/library - 서재에 도서 추가 (인증 필요)

**Request Body:**
```json
{
  "bookId": 1
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "라이브러리에 도서가 추가되었습니다.",
  "payload": {
    "bookId": 1,
    "createdAt": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 404: 도서를 찾을 수 없음
- 409: 이미 라이브러리에 추가됨 (DUPLICATE_LIBRARY_ITEM)

---

#### GET /api/me/library - 내 서재 목록 조회 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "라이브러리 목록이 성공적으로 조회되었습니다.",
  "payload": {
    "items": [
      {
        "book": {
          "id": 1,
          "title": "앵무새 죽이기",
          "author": { "name": "하퍼 리" },
          "isbn": "9780060935467"
        },
        "createdAt": "2025-03-05T12:34:56"
      }
    ]
  }
}
```

---

#### DELETE /api/me/library/{book_id} - 서재에서 도서 삭제 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "라이브러리에서 도서가 삭제되었습니다.",
  "payload": { "bookId": 1 }
}
```

**Errors:**
- 404: 라이브러리에 해당 도서 없음 (LIBRARY_ITEM_NOT_FOUND)

---

### 7. 위시리스트 API (Wishlist)

#### POST /api/me/wishlist - 위시리스트에 도서 추가 (인증 필요)

**Request Body:**
```json
{
  "bookId": 1
}
```

**Response (201):**
```json
{
  "is_success": true,
  "message": "위시리스트에 도서가 추가되었습니다.",
  "payload": {
    "bookId": 1,
    "createdAt": "2025-03-05T12:34:56"
  }
}
```

**Errors:**
- 404: 도서를 찾을 수 없음
- 409: 이미 위시리스트에 추가됨 (DUPLICATE_WISHLIST_ITEM)

---

#### GET /api/me/wishlist - 위시리스트 목록 조회 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "위시리스트 목록이 성공적으로 조회되었습니다.",
  "payload": {
    "items": [
      {
        "book": {
          "id": 1,
          "title": "앵무새 죽이기",
          "author": { "name": "하퍼 리" },
          "isbn": "9780060935467"
        },
        "createdAt": "2025-03-05T12:34:56"
      }
    ]
  }
}
```

---

#### DELETE /api/me/wishlist/{book_id} - 위시리스트에서 도서 삭제 (인증 필요)

**Response (200):**
```json
{
  "is_success": true,
  "message": "위시리스트에서 도서가 삭제되었습니다.",
  "payload": { "bookId": 1 }
}
```

**Errors:**
- 404: 위시리스트에 해당 도서 없음 (WISHLIST_ITEM_NOT_FOUND)

---

### 8. 시스템 API

#### GET /api/health - 헬스체크

**Response (200):**
```json
{
  "status": "OK"
}
```

---

## 권한 매트릭스

| 엔드포인트 | 비인증 | USER | ADMIN |
|-----------|--------|------|-------|
| GET /api/health | O | O | O |
| POST /api/auth/login | O | O | O |
| GET /api/auth/google | O | O | O |
| GET /api/auth/google/callback | O | O | O |
| POST /api/auth/firebase | O | O | O |
| POST /api/auth/refresh | O | O | O |
| POST /api/auth/logout | X | O | O |
| POST /api/users (회원가입) | O | O | O |
| GET /api/users/me | X | O | O |
| PATCH /api/users/me | X | O | X |
| DELETE /api/users/me | X | O | X |
| GET /api/users (목록) | X | X | O |
| GET /api/users/{id} | X | X | O |
| GET /api/books | O | O | O |
| GET /api/books/{id} | O | O | O |
| POST /api/books | X | X | O |
| PATCH /api/books/{id} | X | X | O |
| DELETE /api/books/{id} | X | X | O |
| GET /api/books/{id}/reviews | O | O | O |
| GET /api/books/{id}/reviews/top | O | O | O |
| POST /api/books/{id}/reviews | X | O | O |
| GET /api/books/{id}/comments | O | O | O |
| POST /api/books/{id}/comments | X | O | O |
| PATCH /api/reviews/{id} | X | O (본인) | O (본인) |
| DELETE /api/reviews/{id} | X | O (본인) | O (본인) |
| POST /api/reviews/{id}/like | X | O | O |
| DELETE /api/reviews/{id}/like | X | O | O |
| PATCH /api/comments/{id} | X | O (본인) | O (본인) |
| DELETE /api/comments/{id} | X | O (본인) | O (본인) |
| POST /api/comments/{id}/like | X | O | O |
| DELETE /api/comments/{id}/like | X | O | O |
| POST /api/me/library | X | O | O |
| GET /api/me/library | X | O | O |
| DELETE /api/me/library/{id} | X | O | O |
| POST /api/me/wishlist | X | O | O |
| GET /api/me/wishlist | X | O | O |
| DELETE /api/me/wishlist/{id} | X | O | O |

---

## API 요약

| 분류 | 엔드포인트 수 |
|------|--------------|
| Auth (인증) | 6개 (로그인, 갱신, 로그아웃, Google OAuth, Firebase) |
| Users (사용자) | 6개 |
| Books (도서) | 5개 |
| Reviews (리뷰) | 7개 |
| Comments (댓글) | 6개 |
| Library (내 서재) | 3개 |
| Wishlist (위시리스트) | 3개 |
| System (시스템) | 1개 |
| **총계** | **37개** |

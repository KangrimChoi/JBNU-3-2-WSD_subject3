# WSD HW2 - 도서 관리 RESTful API 서버

전북대학교 웹 서비스 개발(WSD) 2번째 과제 - 도서 관리 RESTful API 서버

## 개발자 정보

- **학번**: 202117643
- **이름**: 최강림

---

## 프로젝트 개요

### 문제 정의
도서 정보를 관리하고, 사용자가 리뷰/댓글을 작성하며, 개인 서재 및 위시리스트를 관리할 수 있는 RESTful API 서버 구현

### 주요 기능
- **인증**: JWT 기반 로그인/로그아웃, 토큰 갱신
- **사용자 관리**: 회원가입, 프로필 조회/수정, 회원 탈퇴
- **도서 관리**: 도서 CRUD (관리자), 목록 조회/검색 (전체)
- **리뷰 시스템**: 도서 리뷰 CRUD, 좋아요, Top-N 리뷰
- **댓글 시스템**: 도서 댓글 CRUD, 좋아요
- **내 서재**: 구매/소장 도서 관리
- **위시리스트**: 관심 도서 관리

---

## 실행 방법

### 로컬 실행

```bash
# 1. 가상환경 생성 및 활성화
python3.11 -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 실제 값으로 수정

# 4. Redis 실행 (Docker)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 5. DB 마이그레이션 및 시드 데이터 생성
alembic upgrade head
python scripts/seed.py

# 6. 서버 실행
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### 테스트 실행

```bash
pytest tests/ -v
```

---

## 환경변수 설명

`.env.example` 참고:

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `PORT_NUM` | 서버 포트 | `8080` |
| `DB_HOST` | MySQL 호스트 | `localhost` |
| `DB_PORT` | MySQL 포트 | `3306` |
| `DB_USER` | MySQL 사용자명 | `root` |
| `DB_PASSWORD` | MySQL 비밀번호 | `password` |
| `DB_NAME` | 데이터베이스명 | `wsd_db` |
| `SECRET_KEY` | JWT 서명 키 | `your-secret-key` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 만료(분) | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 만료(일) | `7` |
| `REDIS_HOST` | Redis 호스트 | `localhost` |
| `REDIS_PORT` | Redis 포트 | `6379` |
| `REDIS_DB` | Redis DB 번호 | `0` |

---

## 배포 주소

| 항목 | URL |
|------|-----|
| **Base URL** | `http://113.198.66.75:10200/` |
| **Swagger UI** | `http://113.198.66.75:10200/docs` |
| **Health Check** | `http://113.198.66.75:10200/api/health` |

---

## 인증 플로우

```
1. 회원가입: POST /api/users
   └─ 이메일, 비밀번호, 이름 입력

2. 로그인: POST /api/auth/login
   └─ Access Token + Refresh Token 발급

3. API 요청: Authorization: Bearer {access_token}
   └─ 인증 필요 API에 헤더 포함

4. 토큰 갱신: POST /api/auth/refresh
   └─ Refresh Token으로 새 Access Token 발급

5. 로그아웃: POST /api/auth/logout
   └─ Access Token 블랙리스트 등록, Refresh Token 삭제
```

### JWT 토큰 규격
- **Access Token**: 만료 60분 (설정 가능)
- **Refresh Token**: 만료 7일 (설정 가능)
- **헤더 형식**: `Authorization: Bearer {token}`

---

## 역할/권한표

| 엔드포인트 | 비인증 | USER | ADMIN |
|-----------|:------:|:----:|:-----:|
| `GET /api/health` | O | O | O |
| `POST /api/auth/login` | O | O | O |
| `POST /api/users` (회원가입) | O | O | O |
| `GET /api/books` | O | O | O |
| `GET /api/books/{id}` | O | O | O |
| `GET /api/books/{id}/reviews` | O | O | O |
| `GET /api/books/{id}/comments` | O | O | O |
| `POST /api/books` | X | X | O |
| `PATCH /api/books/{id}` | X | X | O |
| `DELETE /api/books/{id}` | X | X | O |
| `POST /api/books/{id}/reviews` | X | O | O |
| `POST /api/books/{id}/comments` | X | O | O |
| `POST /api/me/library` | X | O | O |
| `POST /api/me/wishlist` | X | O | O |
| `GET /api/users` (목록) | X | X | O |
| `GET /api/users/{id}` | X | X | O |

---

## 예제 계정

| 역할 | 이메일 | 비밀번호 | 비고 |
|------|--------|----------|------|
| 일반 사용자 | `user1@example.com` | `P@ssw0rd!` | 기본 사용자 |
| 관리자 | `admin@example.com` | `P@ssw0rd!` | 도서 CRUD, 사용자 목록 조회 가능 |

> **주의**: 관리자 계정은 API를 통한 정보 수정/삭제가 불가합니다.

---

## DB 연결 정보 (테스트용)

| 항목 | 값 |
|------|-----|
| 호스트 | `localhost` |
| 포트 | `3306` |
| DB명 | `wsd_db` |
| 계정 | `root` / (설정된 비밀번호) |
| 권한 | 모든 테이블 읽기/쓰기 |

---

## 엔드포인트 요약표

### 인증 (Auth) - 3개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/auth/login` | 로그인 |
| POST | `/api/auth/refresh` | 토큰 갱신 |
| POST | `/api/auth/logout` | 로그아웃 |

### 사용자 (Users) - 6개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/users` | 회원가입 |
| GET | `/api/users/me` | 내 정보 조회 |
| PATCH | `/api/users/me` | 내 정보 수정 |
| DELETE | `/api/users/me` | 회원 탈퇴 |
| GET | `/api/users` | 사용자 목록 (ADMIN) |
| GET | `/api/users/{id}` | 사용자 조회 (ADMIN) |

### 도서 (Books) - 5개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/books` | 도서 등록 (ADMIN) |
| GET | `/api/books` | 도서 목록 |
| GET | `/api/books/{id}` | 도서 상세 |
| PATCH | `/api/books/{id}` | 도서 수정 (ADMIN) |
| DELETE | `/api/books/{id}` | 도서 삭제 (ADMIN) |

### 리뷰 (Reviews) - 7개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/books/{id}/reviews` | 리뷰 작성 |
| GET | `/api/books/{id}/reviews` | 리뷰 목록 |
| GET | `/api/books/{id}/reviews/top` | Top-N 리뷰 |
| PATCH | `/api/reviews/{id}` | 리뷰 수정 |
| DELETE | `/api/reviews/{id}` | 리뷰 삭제 |
| POST | `/api/reviews/{id}/like` | 좋아요 |
| DELETE | `/api/reviews/{id}/like` | 좋아요 취소 |

### 댓글 (Comments) - 6개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/books/{id}/comments` | 댓글 작성 |
| GET | `/api/books/{id}/comments` | 댓글 목록 |
| PATCH | `/api/comments/{id}` | 댓글 수정 |
| DELETE | `/api/comments/{id}` | 댓글 삭제 |
| POST | `/api/comments/{id}/like` | 좋아요 |
| DELETE | `/api/comments/{id}/like` | 좋아요 취소 |

### 내 서재 (Library) - 3개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/me/library` | 서재 추가 |
| GET | `/api/me/library` | 서재 목록 |
| DELETE | `/api/me/library/{book_id}` | 서재 삭제 |

### 위시리스트 (Wishlist) - 3개
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/me/wishlist` | 위시리스트 추가 |
| GET | `/api/me/wishlist` | 위시리스트 목록 |
| DELETE | `/api/me/wishlist/{book_id}` | 위시리스트 삭제 |

### 시스템 - 1개
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/health` | 헬스체크 |

**총 34개 API**

---

## 성능/보안 고려사항

### 보안
- [o] 비밀번호 bcrypt 해싱
- [o] JWT 토큰 인증
- [o] Refresh Token Redis 저장
- [o] Access Token 블랙리스트 관리
- [o] 환경변수로 민감정보 관리
- [o] CORS 설정 (허용 도메인 명시)

### 성능
- [o] 레이트리밋 (분당 60회)
- [o] N+1 쿼리 방지 (joinedload)
- [o] 페이지네이션 적용
- [o] 인덱스 설정 (외래키)

---

## 한계와 개선 계획

### 현재 한계
1. 통계 API: 일별 통계, 인기 작성자 등 미구현
2. 장바구니/주문: 모델만 존재, API 미구현
3. 이미지 업로드: URL만 저장, 실제 업로드 미지원

### 개선 계획
1. 통계 API 구현
2. 장바구니/주문 결제 플로우 구현
3. S3 연동 이미지 업로드

---

## 기술 스택

- **Backend**: Python 3.11+, FastAPI
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy + Alembic
- **Cache**: Redis
- **Auth**: JWT (python-jose)
- **Docs**: Swagger/OpenAPI

---


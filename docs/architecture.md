# 아키텍처 문서

이 문서는 도서 관리 RESTful API 서버의 계층 구조, 의존성, 모듈 구성을 설명합니다.

---

## 시스템 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Frontend)                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Middleware Layer                       │  │
│  │  • CORS Middleware                                        │  │
│  │  • Session Middleware (OAuth state 관리)                  │  │
│  │  • Rate Limiter (slowapi)                                 │  │
│  │  • Exception Handlers                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Router Layer                           │  │
│  │  auth │ users │ books │ reviews │ comments │ library │... │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Authentication / Authorization               │  │
│  │  • JWT Token (Access/Refresh)                             │  │
│  │  • Role-based Access Control (USER/ADMIN)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Schema Layer (Pydantic)                 │  │
│  │  Request/Response Validation & Serialization              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Model Layer (SQLAlchemy)                │  │
│  │  ORM Models & Relationships                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│       MariaDB        │         │        Redis         │
│   (Primary Data)     │         │   (Token Cache)      │
│                      │         │                      │
│  • Users             │         │  • Access Blacklist  │
│  • Books             │         │  • Refresh Tokens    │
│  • Reviews           │         │  • Session Data      │
│  • Comments          │         │                      │
│  • Library/Wishlist  │         │                      │
└──────────────────────┘         └──────────────────────┘
```

---

## 계층 구조 (Layered Architecture)

### 1. Presentation Layer (표현 계층)
**위치**: `src/routers/`

HTTP 요청을 받아 처리하고 응답을 반환하는 계층입니다.

```
src/routers/
├── auth.py          # 인증 API (login, refresh, logout)
├── users.py         # 사용자 API (CRUD)
├── books.py         # 도서 API (CRUD)
├── reviews.py       # 리뷰 API (CRUD, 좋아요)
├── comments.py      # 댓글 API (CRUD, 좋아요)
├── library.py       # 내 서재 API
├── wishlist.py      # 위시리스트 API
└── health.py        # 헬스체크 API
```

**책임**:
- HTTP 요청 파싱 및 라우팅
- 요청 유효성 검사 (Query, Path, Body)
- 응답 포맷팅 (APIResponse, ErrorResponse)
- 인증/인가 의존성 주입

### 2. Schema Layer (스키마 계층)
**위치**: `src/schema/`

요청/응답 데이터의 구조와 검증 규칙을 정의합니다.

```
src/schema/
├── common.py        # 공통 응답 (APIResponse, ErrorResponse, PagedResponse)
├── auth.py          # 인증 스키마 (로그인, 토큰)
├── users.py         # 사용자 스키마
├── books.py         # 도서 스키마
├── reviews.py       # 리뷰 스키마
├── comments.py      # 댓글 스키마
├── library.py       # 서재 스키마
└── wishlist.py      # 위시리스트 스키마
```

**책임**:
- Pydantic 모델 정의
- 입력값 유효성 검사 (타입, 길이, 형식)
- 응답 직렬화 (JSON 변환)
- 타입 힌트 제공

### 3. Business Logic Layer (비즈니스 로직 계층)
**위치**: `src/auth/`, `src/routers/` (내부 로직)

핵심 비즈니스 규칙을 처리합니다.

```
src/auth/
├── jwt.py           # JWT 토큰 생성/검증, APIException 정의
├── password.py      # 비밀번호 해싱/검증 (bcrypt)
├── oauth.py         # Google OAuth 2.0 클라이언트
└── firebase_auth.py # Firebase Admin SDK 초기화 및 토큰 검증
```

**책임**:
- JWT 토큰 생성 및 검증
- 비밀번호 암호화
- 사용자 인증/인가 처리
- 소셜 로그인 처리 (Google OAuth, Firebase)
- 비즈니스 규칙 검증 (중복 체크, 권한 확인 등)

### 4. Data Access Layer (데이터 접근 계층)
**위치**: `src/models/`, `src/database.py`

데이터베이스와의 상호작용을 담당합니다.

```
src/models/
├── user.py          # 사용자 모델
├── book.py          # 도서 모델
├── author.py        # 저자 모델
├── category.py      # 카테고리 모델
├── book_author.py   # 도서-저자 연결 (N:M)
├── book_category.py # 도서-카테고리 연결 (N:M)
├── review.py        # 리뷰 모델
├── review_like.py   # 리뷰 좋아요 모델
├── comment.py       # 댓글 모델
├── comment_like.py  # 댓글 좋아요 모델
├── library_item.py  # 내 서재 모델
├── wishlist_item.py # 위시리스트 모델
├── cart_item.py     # 장바구니 모델
├── order.py         # 주문 모델
└── order_item.py    # 주문 항목 모델
```

**책임**:
- SQLAlchemy ORM 모델 정의
- 테이블 관계 설정 (1:N, N:M)
- 데이터베이스 세션 관리
- CRUD 쿼리 실행

### 5. Infrastructure Layer (인프라 계층)
**위치**: `src/config.py`, `src/database.py`, `src/redis.py`

외부 시스템과의 연결을 관리합니다.

```
src/
├── config.py        # 환경변수 설정
├── database.py      # MySQL 연결 (SQLAlchemy)
└── redis.py         # Redis 연결 (토큰 관리)
```

**책임**:
- 환경변수 로드 (.env)
- 데이터베이스 연결 풀 관리
- Redis 클라이언트 관리
- 외부 서비스 연결 설정

---

## 모듈 의존성 다이어그램

```
                    ┌─────────────┐
                    │   main.py   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ routers/ │    │ config   │    │middleware│
    └────┬─────┘    └────┬─────┘    └──────────┘
         │               │
    ┌────┴────┬──────────┴──────────┐
    │         │                      │
    ▼         ▼                      ▼
┌────────┐ ┌────────┐          ┌──────────┐
│schema/ │ │ auth/  │          │ database │
└────────┘ └───┬────┘          └────┬─────┘
               │                    │
               │         ┌──────────┤
               ▼         ▼          ▼
          ┌────────┐ ┌────────┐ ┌────────┐
          │ redis  │ │models/ │ │ Base   │
          └────────┘ └────────┘ └────────┘
```

### 의존성 흐름

| 모듈 | 의존 대상 |
|------|-----------|
| `main.py` | config, routers/*, auth/jwt, schema/common |
| `routers/*` | database, schema/*, models/*, auth/* |
| `auth/jwt` | config, database, models/user, redis |
| `auth/password` | (외부: bcrypt) |
| `models/*` | database (Base) |
| `schema/*` | (외부: pydantic) |
| `database` | config |
| `redis` | config |
| `config` | (외부: dotenv) |

---

## 데이터 흐름

### 요청 처리 흐름

```
1. HTTP Request 수신
        │
        ▼
2. CORS Middleware (도메인 검증)
        │
        ▼
3. Rate Limiter (요청 제한 검사)
        │
        ▼
4. Router 매칭 (URL → Handler)
        │
        ▼
5. 인증/인가 검사 (JWT → User)
   ├─ Access Token 검증
   ├─ 블랙리스트 확인 (Redis)
   └─ 사용자 조회 (MySQL)
        │
        ▼
6. Schema 검증 (Request Body)
        │
        ▼
7. 비즈니스 로직 실행
   ├─ 데이터 조회/생성/수정/삭제
   └─ 관계 처리 (joinedload)
        │
        ▼
8. Response 생성 (APIResponse)
        │
        ▼
9. HTTP Response 반환
```

### 인증 흐름

```
+----------------------------------------------------------------+
|                        로그인 흐름                              |
+----------------------------------------------------------------+
|  1. POST /api/auth/login (email, password)                     |
|  2. 사용자 조회 (MySQL)                                         |
|  3. 비밀번호 검증 (bcrypt)                                      |
|  4. Access Token 생성 (JWT, 60분)                              ㅣ
|  5. Refresh Token 생성 (JWT, 7일)                              ㅣ
|  6. Refresh Token 저장 (Redis)                                 ㅣ
|  7. 토큰 반환                                                   |
+----------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------+
|                       토큰 갱신 흐름                            |
+----------------------------------------------------------------+
|  1. POST /api/auth/refresh (refresh_token)                     |
|  2. Refresh Token 검증 (JWT)                                   ㅣ
|  3. Redis에서 저장된 토큰과 비교                                 |
|  4. 새 Access Token 발급                                        |
|  5. 토큰 반환                                                   |
+----------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------+
|                       로그아웃 흐름                             |
+----------------------------------------------------------------+
|  1. POST /api/auth/logout (Authorization: Bearer token)        |
|  2. Access Token 블랙리스트 등록 (Redis, TTL=만료시간)           |
|  3. Refresh Token 삭제 (Redis)                                 |
|  4. 성공 응답 반환                                              |
+----------------------------------------------------------------+
```

---

## 핵심 설계 패턴

### 1. Dependency Injection (의존성 주입)
FastAPI의 `Depends`를 활용한 의존성 주입 패턴

```python
# 데이터베이스 세션 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 현재 사용자 주입
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    ...

# 라우터에서 사용
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    ...
```

### 2. Repository Pattern (간소화)
라우터 내에서 직접 쿼리 실행 (Service 계층 생략)

```python
# 도서 조회 예시
book = db.query(Book).options(
    joinedload(Book.authors),
    joinedload(Book.categories)
).filter(Book.id == book_id).first()
```

### 3. Soft Delete
도서 삭제 시 물리적 삭제 대신 `deleted_at` 타임스탬프 설정

```python
# 삭제 처리
book.deleted_at = datetime.now()
db.commit()

# 조회 시 삭제된 항목 제외
query = db.query(Book).filter(Book.deleted_at.is_(None))
```

### 4. N+1 Query Prevention
`joinedload`를 활용한 Eager Loading

```python
# N+1 문제 방지
books = query.options(
    joinedload(Book.authors),
    joinedload(Book.categories)
).all()
```

---

## 외부 의존성

### Python 패키지

| 패키지 | 용도 |
|--------|------|
| `fastapi` | 웹 프레임워크 |
| `uvicorn` | ASGI 서버 |
| `sqlalchemy` | ORM |
| `alembic` | DB 마이그레이션 |
| `pymysql` | MySQL/MariaDB 드라이버 |
| `redis` | Redis 클라이언트 |
| `python-jose` | JWT 처리 |
| `bcrypt` | 비밀번호 해싱 |
| `pydantic` | 데이터 검증 |
| `python-dotenv` | 환경변수 로드 |
| `slowapi` | Rate Limiting |
| `authlib` | OAuth 2.0 클라이언트 (Google) |
| `itsdangerous` | 세션 관리 (OAuth state) |
| `firebase-admin` | Firebase Admin SDK |
| `httpx` | HTTP 클라이언트 (테스트용) |
| `pytest` | 테스트 프레임워크 |
| `pytest-asyncio` | 비동기 테스트 지원 |

### 외부 서비스

| 서비스 | 용도 | 포트 |
|--------|------|------|
| MariaDB 11.5 | 주 데이터 저장소 | 3306 |
| Redis 7 | 토큰 캐시/블랙리스트/세션 | 6379 |
| Google OAuth 2.0 | 소셜 로그인 | HTTPS |
| Firebase Auth | 소셜 로그인 (ID Token 검증) | HTTPS |

---

## 디렉토리 구조 전체

```
WSD_HW2/
├── src/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 환경변수 설정
│   ├── database.py          # DB 연결 설정
│   ├── redis.py             # Redis 클라이언트
│   │
│   ├── auth/                # 인증/인가
│   │   ├── jwt.py           # JWT 유틸리티, APIException
│   │   ├── password.py      # 비밀번호 해싱
│   │   ├── oauth.py         # Google OAuth 2.0 클라이언트
│   │   └── firebase_auth.py # Firebase Admin SDK
│   │
│   ├── models/              # SQLAlchemy 모델 (15개)
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── author.py
│   │   ├── category.py
│   │   ├── book_author.py
│   │   ├── book_category.py
│   │   ├── review.py
│   │   ├── review_like.py
│   │   ├── comment.py
│   │   ├── comment_like.py
│   │   ├── library_item.py
│   │   ├── wishlist_item.py
│   │   ├── cart_item.py
│   │   ├── order.py
│   │   └── order_item.py
│   │
│   ├── schema/              # Pydantic 스키마 (8개)
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── books.py
│   │   ├── reviews.py
│   │   ├── comments.py
│   │   ├── library.py
│   │   └── wishlist.py
│   │
│   └── routers/             # API 라우터 (8개)
│       ├── auth.py
│       ├── users.py
│       ├── books.py
│       ├── reviews.py
│       ├── comments.py
│       ├── library.py
│       ├── wishlist.py
│       └── health.py
│
├── alembic/                 # DB 마이그레이션
│   ├── env.py
│   └── versions/
│
├── scripts/
│   └── seed.py              # 시드 데이터 생성
│
├── tests/                   # 테스트 코드
│
├── docs/                    # 문서
│   ├── api-design.md        # API 설계 문서
│   └── architecture.md      # 아키텍처 문서 (현재 파일)
│
├── postman/                 # Postman 컬렉션
│
├── .env.example             # 환경변수 예시
├── requirements.txt         # 의존성 목록
└── alembic.ini              # Alembic 설정
```

---

## 확장 포인트

### 현재 미구현 (모델만 존재)
- 장바구니 API (`cart_items`)
- 주문 API (`orders`, `order_items`)

### 향후 개선 가능
1. **Service Layer 분리**: 비즈니스 로직을 라우터에서 분리
2. **캐싱**: Redis를 활용한 도서 목록 캐싱
3. **검색**: Elasticsearch 연동
4. **파일 업로드**: S3 연동 이미지 업로드
5. **비동기 처리**: Celery를 활용한 백그라운드 작업

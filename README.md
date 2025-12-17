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

### 헬스체크 결과
![alt text](image-1.png)

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

## DB ERD
![alt text](ERD_page-0001.jpg)

---

## API 문서

API 엔드포인트 상세 정보, 요청/응답 형식, 권한 매트릭스는 [API 설계 문서](docs/api-design.md)를 참고하세요.

- 총 **34개** API 엔드포인트 구현
- Auth(3), Users(6), Books(5), Reviews(7), Comments(6), Library(3), Wishlist(3), System(1)

---

## postman 스크립트
 | 스크립트 | 요청        | 기능                                  |
  |----------|-------------|---------------------------------------|
  | ①        | 로그인      | 토큰 저장 (bearerToken, refreshToken) |
  | ②        | 토큰 재발급 | 새 bearerToken 저장                   |
  | ③        | 도서 목록   | 응답 검증 + bookId 저장               |
  | ④        | 도서 상세   | 응답 검증                             |
  | ⑤        | 내 정보     | 인증 토큰 검증                        |
  | ⑥        | 로그아웃    | 토큰 초기화                           |

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
- **Database**: Mariadb 15.1
- **ORM**: SQLAlchemy + Alembic
- **Cache**: Redis
- **Auth**: JWT (python-jose)
- **Docs**: Swagger/OpenAPI

상세 아키텍처, 계층 구조, 의존성은 [아키텍처 문서](docs/architecture.md)를 참고하세요.


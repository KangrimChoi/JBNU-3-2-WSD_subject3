"""Google OAuth 2.0 인증 처리"""
from authlib.integrations.starlette_client import OAuth
from src.config import settings

# OAuth 클라이언트 설정
oauth = OAuth()

# Google OAuth 등록
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


def get_google_oauth_client():
    """Google OAuth 클라이언트 반환"""
    return oauth.google

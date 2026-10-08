import jwt

from django.conf import settings

from ninja_jwt.authentication import JWTAuth

from .utils import is_token_blacklisted


class CustomJWTAuth(JWTAuth):

    def authenticate(self, request, token):

        try:

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

            jti = payload.get("jti")

            if jti and is_token_blacklisted(jti):
                return None

            return super().authenticate(
                request,
                token
            )

        except jwt.ExpiredSignatureError:
            return None

        except jwt.InvalidTokenError:
            return None

        except Exception:
            return None
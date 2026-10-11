import os
import jwt
import typing as typ
from flask import request
from functools import wraps, lru_cache
from datetime import datetime, timedelta, timezone

ISSUER = "realworld"
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
OVERRIDE_TOKEN_EXPIRATION = os.getenv("OVERRIDE_TOKEN_EXPIRATION", "FALSE").upper()


def generate_jwt(
    user_id: str,
):
    payload = {
        "iss": ISSUER,
        "user_id": user_id,
        "iat": datetime.now(tz=timezone.utc),
    }
    if OVERRIDE_TOKEN_EXPIRATION == "TRUE":
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(minutes=15)

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@lru_cache()
def _decode_jwt(token: str) -> typ.Tuple[bool, typ.Union[dict, str]]:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True, decoded
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        jwt.InvalidSignatureError,
    ) as e:
        return False, str(e)
    except Exception:
        return False, "Unknown token error."


def _get_token_from_request() -> typ.Optional[str]:
    encoded_token = request.headers.get("Authorization")
    if not encoded_token:
        return None

    # Authorization: Token <token>
    return encoded_token.split(" ")[1]


def validate_token(func):
    @wraps(func)
    def wrapper(*args, **kwds):

        encoded_token = _get_token_from_request()
        if not encoded_token:
            return {"error": "No token provided."}, 401

        is_valid, decoded = _decode_jwt(encoded_token)
        if not is_valid:
            return {"error": decoded}, 401

        return func(*args, **kwds)

    return wrapper


def get_user_id_from_token() -> typ.Optional[str]:
    is_valid, decoded = _decode_jwt(_get_token_from_request())
    if is_valid:
        return decoded.get("user_id")
    return None

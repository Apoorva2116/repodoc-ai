from flask import Blueprint, request
from realworld.api.core.db import get_db_connection
from realworld.api.core.auth import generate_jwt, validate_token, get_user_id_from_token
from realworld.api.routes.v1.users import handler as users_handler
from realworld.api.routes.v1.users.models import (
    RegisterUserRequest,
    UpdateUserRequest,
    LoginUserRequest,
    UserDataResponse,
    AuthUser,
    AuthUserResponse,
)


users_blueprint = Blueprint(
    "users_endpoints",
    __name__,
)


@users_blueprint.route("/users", methods=["POST"])
def create_user() -> dict:
    data = RegisterUserRequest.model_validate(request.json)
    with get_db_connection() as db_conn:
        if not (user := users_handler.create_user(db_conn, data.user)):
            return {"error": "A user with this username already exists."}, 409

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    ).model_dump()


@users_blueprint.route("/users/login", methods=["POST"])
def authenticate_user() -> dict:
    data = LoginUserRequest.model_validate(request.json)
    with get_db_connection() as db_conn:
        if not (
            user := users_handler.validate_user_creds(
                db_conn, email=data.user.email, password=data.user.password
            )
        ):
            return {"error": "User does not exist."}, 404

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    ).model_dump()


@validate_token
@users_blueprint.route("/user", methods=["GET"])
def get_current_user() -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"error": "Invalid token."}, 401

    with get_db_connection() as db_conn:
        if user := users_handler.get_user(db_conn, user_id):
            return UserDataResponse(user=user).model_dump()

    return {"error": "User does not exist."}, 404


@validate_token
@users_blueprint.route("/user", methods=["PUT"])
def update_user() -> dict:
    data = UpdateUserRequest.model_validate(request.json)
    with get_db_connection() as db_conn:
        if not (
            user := users_handler.update_user(
                db_conn, get_user_id_from_token(), data.user
            )
        ):
            return {"error": "User does not exist."}, 404

    return UserDataResponse(user=user).model_dump()

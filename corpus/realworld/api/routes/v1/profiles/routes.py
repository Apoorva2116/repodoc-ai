from flask import Blueprint
from realworld.api.core.db import get_db_connection
from realworld.api.core.auth import validate_token, get_user_id_from_token
from realworld.api.routes.v1.profiles.models import ProfileDataResponse, ProfileData
import realworld.api.routes.v1.profiles.handler as profiles_handler

profiles_blueprint = Blueprint("profiles_endpoints", __name__, url_prefix="/profiles")


@profiles_blueprint.route("/<string:username>", methods=["GET"])
def get_profile(username) -> dict:

    with get_db_connection() as db_conn:
        if not (
            profile := profiles_handler.get_profile(
                db_conn, username, get_user_id_from_token()
            )
        ):
            return {"error": "Profile not found."}, 404

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    ).model_dump()


@validate_token
@profiles_blueprint.route("/<string:username>/follow", methods=["POST"])
def follow_profile(username):

    with get_db_connection() as db_conn:
        if not (
            profile := profiles_handler.follow_profile(
                db_conn, username, get_user_id_from_token()
            )
        ):
            return {"error": "Profile not found."}, 404

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    ).model_dump()


@validate_token
@profiles_blueprint.route("/<string:username>/follow", methods=["DELETE"])
def unfollow_profile(username):

    with get_db_connection() as db_conn:
        if not (
            profile := profiles_handler.unfollow_profile(
                db_conn, username, get_user_id_from_token()
            )
        ):
            return {"error": "Profile not found."}, 404

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    ).model_dump()

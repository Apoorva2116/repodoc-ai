import typing as typ
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text as satext
from realworld.api.routes.v1.profiles.models import ProfileData


def get_profile(
    db_conn: Connection, username: str, curr_user_id: typ.Optional[str] = None
) -> typ.Optional[ProfileData]:

    result = db_conn.execute(
        satext(
            """
            SELECT
                username,
                bio,
                image_url,
                CASE
                    WHEN uf.following_user_id IS NOT NULL THEN TRUE ELSE FALSE
                END AS following
            FROM users u
            LEFT JOIN (
                SELECT following_user_id
                FROM user_follows
                WHERE user_id = :curr_user_id
            ) uf ON u.id = uf.following_user_id
            WHERE username = :username
            """
        ).bindparams(username=username, curr_user_id=curr_user_id)
    ).fetchone()

    if not result:
        return None

    return ProfileData(
        username=result.username,
        bio=result.bio,
        image=result.image_url,
        following=result.following,
    )


def follow_profile(
    db_conn: Connection, username: str, curr_user_id: typ.Optional[str] = None
) -> typ.Optional[ProfileData]:
    db_conn.execute(
        satext(
            """
            INSERT INTO user_follows (user_id, following_user_id)
            SELECT :curr_user_id, u.id
            FROM users u
            WHERE u.username = :username
            ON CONFLICT (user_id, following_user_id) DO NOTHING
           """
        ).bindparams(username=username, curr_user_id=curr_user_id)
    )

    return get_profile(db_conn, username, curr_user_id)


def unfollow_profile(
    db_conn: Connection, username: str, curr_user_id: typ.Optional[str] = None
) -> typ.Optional[ProfileData]:
    db_conn.execute(
        satext(
            """
            DELETE FROM user_follows
            WHERE user_id = :curr_user_id
            AND following_user_id = (SELECT id FROM users WHERE username = :username)
            """
        ).bindparams(username=username, curr_user_id=curr_user_id)
    )

    return get_profile(db_conn, username, curr_user_id)

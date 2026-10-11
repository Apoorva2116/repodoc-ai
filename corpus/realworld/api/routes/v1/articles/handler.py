import re
import typing as typ
from uuid import uuid4
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text as satext
from realworld.api.core.models import Article, Profile, Comment

from realworld.api.routes.v1.articles.models import (
    CreateArticleData,
    UpdateArticleData,
    CreateCommentData,
)

#
# Helpers
#


# return a URL-friendly article slug that likely unique
def generate_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9-_]", "", title.lower().replace(" ", "-"))
    return f"{slug}-{uuid4().hex[:8]}"


def _get_curr_profile_by_id(db_conn: Connection, user_id: str) -> Profile:
    result = db_conn.execute(
        satext(
            """
            SELECT username, bio, image_url
            FROM users
            WHERE id = :user_id
            """
        ).bindparams(user_id=user_id)
    ).fetchone()

    return Profile(
        username=result.username,
        bio=result.bio,
        image=result.image_url,
        following=False,  # unable to follow yourself
    )


def _base_get_articles_query(
    *,
    article_id: typ.Optional[int] = None,
    slug: typ.Optional[str] = None,
    curr_user_id: typ.Optional[str] = None,
    filter_tag: typ.Optional[str] = None,
    author_username_filter: typ.Optional[str] = None,
    favorited_by_username_filter: typ.Optional[str] = None,
    curr_user_feed: typ.Optional[bool] = False,
    limit: typ.Optional[int] = 20,
    offset: typ.Optional[int] = 0,
):

    joins = []
    where_clauses = []
    params = {
        "limit": limit,
        "offset": offset,
        "curr_user_id": curr_user_id,
    }

    if article_id:
        params["article_id"] = article_id
        where_clauses.append("a.id = :article_id")

    if slug:
        params["slug"] = slug
        where_clauses.append("a.slug = :slug")

    if filter_tag:
        params["tag_filter"] = filter_tag
        where_clauses.append("t.name = :tag_filter")
        joins.append("JOIN article_tags at ON a.id = at.article_id")
        joins.append("JOIN tags t ON at.tag_id = t.id")

    if author_username_filter:
        params["author_username"] = author_username_filter
        where_clauses.append("u.username = :author_username")

    if favorited_by_username_filter:
        params["favorited_by_username"] = favorited_by_username_filter
        joins.append("JOIN article_favorites uff ON a.id = uff.article_id")
        joins.append("JOIN users uu ON uu.id = uff.user_id")
        where_clauses.append("uu.username = :favorited_by_username")

    if curr_user_feed and curr_user_id:
        params["curr_user_id"] = curr_user_id
        joins.append("JOIN user_follows uf ON a.author_user_id = uf.following_user_id")
        where_clauses.append("uf.user_id = :curr_user_id")

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    return satext(
        f"""
            SELECT
                a.id,
                a.slug,
                a.title,
                a.description,
                a.body,
                a.created_date,
                a.updated_date,
                u.username AS author_username,
                u.bio AS author_bio,
                u.image_url AS author_image,
                (
                    SELECT COUNT(*)
                    FROM article_favorites f
                    WHERE f.article_id = a.id
                ) AS favorites_count,
                (
                    SELECT COUNT(*)
                    FROM article_favorites f
                    WHERE f.article_id = a.id AND f.user_id = :curr_user_id
                ) AS favorited_by_curr_user,
                (
                    SELECT COUNT(*)
                    FROM user_follows uf
                    WHERE uf.user_id = :curr_user_id
                    AND uf.following_user_id = u.id
                ) > 0 AS is_curr_user_following,
                (
                    SELECT ARRAY_AGG(t.name)
                    FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    WHERE at.article_id = a.id
                ) AS tag_list
            FROM articles a
            JOIN users u ON a.author_user_id = u.id
            {" ".join(joins)}
            {where_clause}
            ORDER BY a.created_date DESC
            LIMIT :limit
            OFFSET :offset
        """
    ).bindparams(**params)


#
# Handlers
#


def get_articles(
    db_conn: Connection,
    *,
    curr_user_id: typ.Optional[str] = None,
    filter_tag: typ.Optional[str] = None,
    author_username_filter: typ.Optional[str] = None,
    favorited_by_username_filter: typ.Optional[str] = None,
    limit: typ.Optional[int] = 20,
    offset: typ.Optional[int] = 0,
) -> typ.List[Article]:
    articles = db_conn.execute(
        _base_get_articles_query(
            curr_user_id=curr_user_id,
            filter_tag=filter_tag,
            author_username_filter=author_username_filter,
            favorited_by_username_filter=favorited_by_username_filter,
            limit=limit,
            offset=offset,
        )
    ).fetchall()

    return [
        Article(
            id=article.id,
            slug=article.slug,
            title=article.title,
            description=article.description,
            body=article.body,
            tag_list=article.tag_list if article.tag_list else [],
            created_at=article.created_date,
            updated_at=article.updated_date,
            favorited=bool(article.favorited_by_curr_user),
            favorites_count=article.favorites_count,
            author=Profile(
                bio=article.author_bio,
                username=article.author_username,
                following=bool(article.is_curr_user_following),
                image=article.author_image,
            ),
        )
        for article in articles
    ]


def get_feed_articles(
    db_conn: Connection,
    curr_user_id: str,
    limit: typ.Optional[int] = 20,
    offset: typ.Optional[int] = 0,
) -> typ.List[Article]:
    articles = db_conn.execute(
        _base_get_articles_query(
            curr_user_id=curr_user_id,
            curr_user_feed=True,
            limit=limit,
            offset=offset,
        )
    ).fetchall()

    return [
        Article(
            id=article.id,
            slug=article.slug,
            title=article.title,
            description=article.description,
            body=article.body,
            tag_list=article.tag_list if article.tag_list else [],
            created_at=article.created_date,
            updated_at=article.updated_date,
            favorited=bool(article.favorited_by_curr_user),
            favorites_count=article.favorites_count,
            author=Profile(
                bio=article.author_bio,
                username=article.author_username,
                following=bool(article.is_curr_user_following),
                image=article.author_image,
            ),
        )
        for article in articles
    ]


def get_article_by_slug(
    db_conn: Connection, slug: str, curr_user_id: typ.Optional[str]
) -> typ.Optional[Article]:
    article = db_conn.execute(
        _base_get_articles_query(slug=slug, curr_user_id=curr_user_id)
    ).fetchone()

    if not article:
        return None

    return Article(
        id=article.id,
        slug=article.slug,
        title=article.title,
        description=article.description,
        body=article.body,
        tag_list=article.tag_list if article.tag_list else [],
        created_at=article.created_date,
        updated_at=article.updated_date,
        favorited=bool(article.favorited_by_curr_user),
        favorites_count=article.favorites_count,
        author=Profile(
            bio=article.author_bio,
            username=article.author_username,
            following=bool(article.is_curr_user_following),
            image=article.author_image,
        ),
    )


def create_article(
    db_conn: Connection, curr_user_id: str, data: CreateArticleData
) -> Article:
    article = db_conn.execute(
        satext(
            """
            INSERT INTO articles (author_user_id, slug, title, description, body)
            VALUES (:author_user_id, :slug, :title, :description, :body)
            RETURNING id, slug
            """
        ).bindparams(
            author_user_id=curr_user_id,
            slug=generate_slug(data.title),
            title=data.title,
            description=data.description,
            body=data.body,
        )
    ).fetchone()

    if data.tag_list:
        db_conn.execute(
            satext(
                """
                WITH upserted_tags AS (
                    INSERT INTO tags (name)
                    VALUES (:name)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                )
                INSERT INTO article_tags (article_id, tag_id)
                SELECT :article_id, id
                FROM upserted_tags
                """
            ),
            [{"name": tag, "article_id": article.id} for tag in data.tag_list],
        )

    return get_article_by_slug(db_conn, article.slug, curr_user_id)


def update_article(
    db_conn: Connection, curr_slug: str, curr_user_id: str, data: UpdateArticleData
) -> Article:

    update_str = ""
    params = {}
    new_slug = None
    for key in ("title", "description", "body"):
        if value := getattr(data, key):

            if key == "title":
                update_str += "slug = :new_slug, "
                new_slug = generate_slug(value)
                params["new_slug"] = new_slug

            update_str += f"{key} = :{key}, "
            params[key] = value

    db_conn.execute(
        satext(
            f"""
            UPDATE articles
            SET {update_str}
                updated_date = CURRENT_TIMESTAMP
            WHERE slug = :slug
            AND author_user_id = :curr_user_id
            """
        ).bindparams(
            slug=curr_slug,
            curr_user_id=curr_user_id,
            **params,
        )
    )

    slug = new_slug if new_slug else curr_slug
    return get_article_by_slug(db_conn, slug, curr_user_id)


def delete_article(db_conn: Connection, slug: str, curr_user_id: str) -> bool:
    result = db_conn.execute(
        satext(
            """
            DELETE FROM articles
            WHERE slug = :slug
            AND author_user_id = :curr_user_id
            """
        ).bindparams(slug=slug, curr_user_id=curr_user_id)
    )
    return bool(result.rowcount)


def create_article_comment(
    db_conn: Connection, slug: str, curr_user_id: str, data: CreateCommentData
) -> typ.Tuple[bool, Comment]:
    result = db_conn.execute(
        satext(
            """
            INSERT INTO article_comments (article_id, commenter_user_id, body)
            VALUES (
                (SELECT id FROM articles WHERE slug = :slug),
                :curr_user_id,
                :body
            )
            RETURNING id, created_date, body
            """
        ).bindparams(slug=slug, curr_user_id=curr_user_id, body=data.body)
    ).fetchone()

    if not result:
        return False, None

    return True, Comment(
        id=str(result.id),
        created_at=result.created_date,
        updated_at=result.created_date,
        body=result.body,
        author=_get_curr_profile_by_id(db_conn, curr_user_id),
    )


def get_article_comments(
    db_conn: Connection, slug: str, curr_user_id: typ.Optional[str]
) -> typ.List[Comment]:
    result = db_conn.execute(
        satext(
            """
            SELECT
                ac.id,
                ac.body,
                ac.created_date,
                ac.updated_date,
                u.username,
                u.bio,
                u.image_url,
                (
                    SELECT COUNT(*)
                    FROM user_follows uf
                    WHERE uf.user_id = :curr_user_id
                    AND uf.following_user_id = u.id
                ) > 0 AS is_following
            FROM article_comments ac
            JOIN users u ON ac.commenter_user_id = u.id
            JOIN articles a ON ac.article_id = a.id
            WHERE a.slug = :slug
            """
        ).bindparams(slug=slug, curr_user_id=curr_user_id)
    ).fetchall()

    if not result:
        return []

    comments = []
    for row in result:
        comments.append(
            Comment(
                id=str(row.id),
                body=row.body,
                created_at=row.created_date,
                updated_at=row.updated_date,
                author=Profile(
                    username=row.username,
                    bio=row.bio,
                    image=row.image_url,
                    following=bool(row.is_following),
                ),
            )
        )

    return comments


def delete_article_comment(
    db_conn: Connection, slug: str, comment_id: int, curr_user_id: str
) -> bool:
    db_conn.execute(
        satext(
            """
            DELETE FROM article_comments
            WHERE id = :comment_id
            AND article_id = (SELECT id FROM articles WHERE slug = :slug)
            AND commenter_user_id = :curr_user_id
            """
        ).bindparams(slug=slug, comment_id=comment_id, curr_user_id=curr_user_id)
    )
    return True


def add_article_favorite(
    db_conn: Connection, slug: str, curr_user_id: str
) -> typ.Optional[Article]:
    db_conn.execute(
        satext(
            """
            INSERT INTO article_favorites (article_id, user_id)
            SELECT a.id, :user_id
            FROM articles a
            WHERE a.slug = :slug 
            ON CONFLICT DO NOTHING
            """
        ).bindparams(slug=slug, user_id=curr_user_id)
    )
    return get_article_by_slug(db_conn, slug, curr_user_id)


def delete_article_favorite(
    db_conn: Connection, slug: str, curr_user_id: str
) -> typ.Optional[Article]:
    db_conn.execute(
        satext(
            """
            DELETE FROM article_favorites
            WHERE article_id = (
                SELECT id
                FROM articles
                WHERE slug = :slug
            )
            AND user_id = :user_id
            """
        ).bindparams(slug=slug, user_id=curr_user_id)
    )
    return get_article_by_slug(db_conn, slug, curr_user_id)


def get_all_tags(db_conn: Connection) -> typ.List[str]:
    result = db_conn.execute(satext("SELECT * from tags")).fetchall()
    return [tag.name for tag in result]

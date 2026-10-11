from flask import Blueprint, request
from realworld.api.core.db import get_db_connection
import realworld.api.routes.v1.articles.handler as articles_handler
from realworld.api.core.auth import validate_token, get_user_id_from_token
from realworld.api.routes.v1.articles.models import (
    # GetArticlesQueryParams,
    # GetFeedQueryParams,
    GetTagsResponse,
    CreateArticleRequest,
    UpdateArticleRequest,
    CreateCommentRequest,
    CreateCommentResponse,
    SingleArticleResponse,
    MultipleArticlesResponse,
    MultipleCommentsResponse,
)


articles_blueprint = Blueprint("articles_endpoints", __name__)
tags_blueprint = Blueprint("tags_endpoints", __name__, url_prefix="/tags")


@articles_blueprint.route("/articles", methods=["GET"])
def get_articles() -> dict:
    """
    Returns most recent articles globally by default, provide tag, author or favorited query parameter to filter results
    """
    user_id = get_user_id_from_token()
    with get_db_connection() as db_conn:
        articles = articles_handler.get_articles(
            db_conn,
            curr_user_id=user_id,
            filter_tag=request.args.get("tag"),
            author_username_filter=request.args.get("author"),
            favorited_by_username_filter=request.args.get("favorited"),
            limit=int(request.args.get("limit", 20)),
            offset=int(request.args.get("offset", 0)),
        )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    ).model_dump()


@validate_token
@articles_blueprint.route("/articles/feed", methods=["GET"])
def get_feed() -> dict:
    """
    Returns articles created by followed users, ordered by most recent first.
    """
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    with get_db_connection() as db_conn:
        articles = articles_handler.get_feed_articles(
            db_conn,
            user_id,
            limit=int(request.args.get("limit", 20)),
            offset=int(request.args.get("offset", 0)),
        )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    ).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["GET"])
def get_article(slug: str) -> dict:
    with get_db_connection() as db_conn:
        article = articles_handler.get_article_by_slug(
            db_conn, slug, curr_user_id=get_user_id_from_token()
        )
        if not article:
            return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles", methods=["POST"])
def create_article() -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = CreateArticleRequest.model_validate(request.json)
    with get_db_connection() as db_conn:
        article = articles_handler.create_article(db_conn, user_id, data.article)

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["PUT"])
def update_article(slug) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = UpdateArticleRequest.model_validate(request.json)
    with get_db_connection() as db_conn:
        article = articles_handler.update_article(db_conn, slug, user_id, data.article)
        if not article:
            return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["DELETE"])
def delete_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    with get_db_connection() as db_conn:
        if not articles_handler.delete_article(db_conn, slug, user_id):
            return {"message": "Article not found"}, 404

    return {"message": "Article deleted"}


#
# Comments
#
@articles_blueprint.route("/articles/<string:slug>/comments", methods=["POST"])
def create_comment(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = CreateCommentRequest.model_validate(request.json)

    with get_db_connection() as db_conn:
        does_article_exist, comment = articles_handler.create_article_comment(
            db_conn, slug, user_id, data.comment
        )
        if not does_article_exist:
            return {"message": "Article not found"}, 404

    return CreateCommentResponse(comment=comment).model_dump()


@articles_blueprint.route("/articles/<string:slug>/comments", methods=["GET"])
def get_comments(slug: str) -> dict:
    with get_db_connection() as db_conn:
        comments = articles_handler.get_article_comments(
            db_conn, slug, curr_user_id=get_user_id_from_token()
        )

    return MultipleCommentsResponse(comments=comments).model_dump()


@articles_blueprint.route(
    "/articles/<string:slug>/comments/<string:comment_id>", methods=["DELETE"]
)
def delete_comment(slug: str, comment_id: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    with get_db_connection() as db_conn:
        articles_handler.delete_article_comment(db_conn, slug, comment_id, user_id)

    return {"message": "Comment deleted"}


#
# Favorites
#
@articles_blueprint.route("/articles/<string:slug>/favorite", methods=["POST"])
def favorite_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    with get_db_connection() as db_conn:
        article = articles_handler.add_article_favorite(db_conn, slug, user_id)
        if not article:
            return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>/favorite", methods=["DELETE"])
def unfavorite_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    with get_db_connection() as db_conn:
        article = articles_handler.delete_article_favorite(db_conn, slug, user_id)
        if not article:
            return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


#
# Tags
#
@tags_blueprint.route("", methods=["GET"])
def get_tags() -> dict:
    with get_db_connection() as db_conn:
        tags = articles_handler.get_all_tags(db_conn)

    return GetTagsResponse(tags=tags).model_dump()

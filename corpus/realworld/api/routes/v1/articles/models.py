import typing as typ
from realworld.api.core.models import BaseCamelModel, Article, Comment


# GET /api/articles
# GET /api/articles/feed


# POST /api/articles
class CreateArticleData(BaseCamelModel):
    title: str
    description: str
    body: str
    tag_list: typ.Optional[typ.List[str]] = None


class CreateArticleRequest(BaseCamelModel):
    article: CreateArticleData


# PUT /api/articles/:slug
class UpdateArticleData(BaseCamelModel):
    title: typ.Optional[str] = None
    description: typ.Optional[str] = None
    body: typ.Optional[str] = None


class UpdateArticleRequest(BaseCamelModel):
    article: UpdateArticleData


# POST /api/articles/:slug/comments
class CreateCommentData(BaseCamelModel):
    body: str


class CreateCommentRequest(BaseCamelModel):
    comment: CreateCommentData


class CreateCommentResponse(BaseCamelModel):
    comment: Comment


#
# Shared Response Models
#
class SingleArticleResponse(BaseCamelModel):
    article: Article


class MultipleArticlesResponse(BaseCamelModel):
    articles: typ.List[Article]
    articles_count: int


class MultipleCommentsResponse(BaseCamelModel):
    comments: typ.List[Comment]


# GET /api/tags
class GetTagsResponse(BaseCamelModel):
    tags: list[str]

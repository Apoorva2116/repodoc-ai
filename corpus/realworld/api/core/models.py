import humps
import typing as typ
from datetime import datetime
from pydantic import BaseModel, field_serializer


#
# Base Models
#


class BaseCamelModel(BaseModel):
    class Config:
        alias_generator = humps.camelize
        populate_by_name = True
        extra = "ignore"

    def model_dump(self, *args, **kwargs) -> dict:
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(*args, **kwargs)


#
# Pagination Models
#


class PaginationParams(BaseCamelModel):
    limit: typ.Optional[int] = None
    offset: typ.Optional[int] = None


#
# Core Models
#


class Profile(BaseCamelModel):
    username: str
    following: bool
    bio: typ.Optional[str] = None
    image: typ.Optional[str] = None


class Comment(BaseCamelModel):
    id: str
    created_at: datetime
    updated_at: datetime
    body: str
    author: Profile

    @field_serializer("created_at", "updated_at", when_used="unless-none")
    def serialize_datetime(self, value: datetime, info):
        return value.isoformat()


class DBUser(BaseCamelModel):
    user_id: str
    username: str
    email: str
    bio: typ.Optional[str]
    image: typ.Optional[str]
    created_date: typ.Optional[datetime] = None
    updated_date: typ.Optional[datetime] = None


class Article(BaseCamelModel):
    slug: str
    title: str
    description: str
    body: str
    tag_list: list[str]
    created_at: datetime
    updated_at: datetime
    favorited: bool
    favorites_count: int
    author: Profile

    @field_serializer("created_at", "updated_at", when_used="unless-none")
    def serialize_datetime(self, value: datetime, info):
        return value.isoformat()

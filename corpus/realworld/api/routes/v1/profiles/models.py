import typing as typ
from realworld.api.core.models import BaseCamelModel


class ProfileData(BaseCamelModel):
    username: str
    following: bool
    bio: typ.Optional[str] = None
    image: typ.Optional[str] = None


class ProfileDataResponse(BaseCamelModel):
    profile: ProfileData

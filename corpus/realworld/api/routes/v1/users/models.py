import typing as typ
from realworld.api.core.models import BaseCamelModel


# POST /api/users/login
class LoginUserData(BaseCamelModel):
    email: str
    password: str


class LoginUserRequest(BaseCamelModel):
    user: LoginUserData


# POST /api/users
class RegisterUserData(BaseCamelModel):
    username: str
    email: str
    password: str


class RegisterUserRequest(BaseCamelModel):
    user: RegisterUserData


# PUT /api/user
class UpdateUserData(BaseCamelModel):
    email: str
    bio: typ.Optional[str] = None
    image: typ.Optional[str] = None


class UpdateUserRequest(BaseCamelModel):
    user: UpdateUserData


#
# Response Models
#


# PUT /api/user
# POST /api/users
class UserData(BaseCamelModel):
    email: str
    username: str
    bio: typ.Optional[str] = None
    image: typ.Optional[str] = None


class UserDataResponse(BaseCamelModel):
    user: UserData


# GET /api/user
# POST /api/users/login
class AuthUser(BaseCamelModel):
    email: str
    token: str
    username: str
    bio: typ.Optional[str] = None
    image: typ.Optional[str] = None


class AuthUserResponse(BaseCamelModel):
    user: AuthUser

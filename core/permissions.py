"""业务认证 / 授权依赖（无状态 JWT 主体，不依赖任何业务/身份表）

统一入口：
- get_current_sso_user / get_current_user：验 JWT 后返回 CurrentUser 主体（由 token 载荷推导，不查库）
- get_current_active_user / require_admin|teacher|student：授权链

设计说明（重要）：
本脚手架**不假定数据库中存在任何用户/身份表**（如 sso_user）。认证完全基于
JWT 载荷（sub / username / user_type / status / permissions），因此无论你的 DDL
是否包含用户表，本层都能正常工作。这样即使业务脚本里根本没有 sso_user 这类表，
生成的工程也能正常 import 与运行。

若你需要「查库校验用户状态 / 读取更多资料」等强一致逻辑，可在此文件自行扩展，
不影响骨架其余部分。
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.auth import jwt_authenticator
from utils.custom_exceptions import AuthenticationException, AuthorizationException
from utils.logger import log_security_event

security = HTTPBearer()

USER_TYPE_NAMES = {1: "学生", 2: "教师", 3: "管理员"}


@dataclass
class CurrentUser:
    """无状态 JWT 主体（由 token 载荷推导，不绑定数据库表）。"""

    user_id: str
    user_type: int = 1
    status: int = 1
    username: str = ""
    permissions: list = None  # type: ignore[assignment]

    @property
    def is_active(self) -> bool:
        return self.status == 1

    @property
    def user_type_name(self) -> str:
        return USER_TYPE_NAMES.get(self.user_type, "未知")

    def has_permission(self, perm: str) -> bool:
        return bool(self.permissions and perm in self.permissions)


class PermissionChecker:
    """权限检查器（业务规则，基于 CurrentUser 主体）。"""

    @staticmethod
    def check_user_access_to_resource(
        current_user: CurrentUser,
        resource_owner_id: str,
        resource_type: str = "general",
    ) -> bool:
        if current_user.user_type == 3:
            return True
        if current_user.user_id == resource_owner_id:
            return True
        log_security_event(
            "UNAUTHORIZED_RESOURCE_ACCESS",
            user_id=current_user.user_id,
            details={
                "resource_owner": resource_owner_id,
                "resource_type": resource_type,
                "user_type": current_user.user_type_name,
            },
        )
        return False

    @staticmethod
    def check_admin_permission(current_user: CurrentUser) -> bool:
        if current_user.user_type != 3:
            log_security_event(
                "ADMIN_PERMISSION_DENIED",
                user_id=current_user.user_id,
                details={"user_type": current_user.user_type_name},
            )
            return False
        return True

    @staticmethod
    def check_teacher_permission(current_user: CurrentUser) -> bool:
        if current_user.user_type not in (2, 3):
            log_security_event(
                "TEACHER_PERMISSION_DENIED",
                user_id=current_user.user_id,
                details={"user_type": current_user.user_type_name},
            )
            return False
        return True


def _build_current_user(payload: dict) -> CurrentUser:
    """从 JWT 载荷构造无状态主体（不查库）。"""
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("令牌中缺少用户信息")
    raw_type = payload.get("user_type")
    raw_status = payload.get("status")
    return CurrentUser(
        user_id=str(user_id),
        user_type=int(raw_type) if raw_type is not None else 1,
        status=int(raw_status) if raw_status is not None else 1,
        username=str(payload.get("username", "") or ""),
        permissions=list(payload.get("permissions", []) or []),
    )


async def get_current_sso_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """从 Bearer Token 推导无状态 CurrentUser 主体（不查询数据库）。"""
    try:
        payload = jwt_authenticator.verify_token(credentials.credentials)
        user = _build_current_user(payload)
        if not user.is_active:
            log_security_event(
                "INACTIVE_USER_ACCESS",
                user_id=user.user_id,
                details={"status": user.status},
            )
            raise AuthenticationException("用户账号已被禁用")
        return user
    except AuthenticationException:
        raise
    except Exception as exc:
        log_security_event("AUTHENTICATION_ERROR", details={"error": str(exc)})
        raise AuthenticationException("身份验证失败") from exc


# 统一别名：业务路由请依赖本符号，勿再用 core.security.get_current_user
get_current_user = get_current_sso_user


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_sso_user),
) -> CurrentUser:
    if not current_user.is_active:
        raise AuthenticationException("用户账号已被禁用")
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if not PermissionChecker.check_admin_permission(current_user):
        raise AuthorizationException("需要管理员权限")
    return current_user


async def require_teacher(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if not PermissionChecker.check_teacher_permission(current_user):
        raise AuthorizationException("需要教师权限")
    return current_user


async def require_student(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if current_user.user_type not in (1, 3):
        log_security_event(
            "STUDENT_PERMISSION_DENIED",
            user_id=current_user.user_id,
            details={"user_type": current_user.user_type_name},
        )
        raise AuthorizationException("需要学生权限")
    return current_user


def check_resource_ownership(resource_owner_id: str, resource_type: str = "general"):
    """返回校验资源归属的 Depends 可调用对象。"""

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        if not PermissionChecker.check_user_access_to_resource(
            current_user, resource_owner_id, resource_type
        ):
            raise AuthorizationException("您无权访问此资源")
        return current_user

    return _dependency

"""Minimal account roles for CampusPulse permissions."""

from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


USER_ROLE_VALUES = tuple(member.value for member in UserRole)
DEFAULT_USER_ROLE = UserRole.STUDENT.value

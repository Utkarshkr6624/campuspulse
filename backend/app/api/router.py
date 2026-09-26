from fastapi import APIRouter

from app.api.routes import (
    academic,
    analytics,
    assignments,
    attendance,
    auth,
    courses,
    documents,
    enrollments,
    exams,
    health,
    marks,
    students,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(courses.router)
api_router.include_router(enrollments.router)
api_router.include_router(marks.router)
api_router.include_router(attendance.router)
api_router.include_router(academic.router)
api_router.include_router(exams.router)
api_router.include_router(assignments.router)
api_router.include_router(analytics.router)
api_router.include_router(documents.router)

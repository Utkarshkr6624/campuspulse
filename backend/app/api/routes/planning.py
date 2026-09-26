from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.planning import (
    AcademicTargetRead,
    AcademicTargetWrite,
    ScenarioCompareRead,
    ScenarioCompareRequest,
    ScenarioPreviewRequest,
    ScenarioProjection,
    ScenarioRead,
    ScenarioUpdate,
    ScenarioWrite,
    TargetType,
)
from app.services import planning_service

router = APIRouter(tags=["academic planning"])


@router.get("/targets", response_model=list[AcademicTargetRead])
def list_targets(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
) -> list[AcademicTargetRead]:
    return planning_service.list_targets(db, student.id)


@router.put("/targets/{target_type}", response_model=AcademicTargetRead)
def put_target(
    target_type: TargetType,
    data: AcademicTargetWrite,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AcademicTargetRead:
    return planning_service.put_target(db, student.id, target_type, data.target_value)


@router.delete("/targets/{target_type}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_type: TargetType,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    planning_service.delete_target(db, student.id, target_type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scenarios/preview", response_model=ScenarioProjection)
def preview_scenario(
    data: ScenarioPreviewRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ScenarioProjection:
    return planning_service.preview_scenario(db, student.id, data.assessments)


@router.post("/scenarios/compare", response_model=ScenarioCompareRead)
def compare_scenarios(
    data: ScenarioCompareRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ScenarioCompareRead:
    return ScenarioCompareRead(
        scenarios=planning_service.compare_scenarios(db, student.id, data.scenario_ids)
    )


@router.get("/scenarios", response_model=list[ScenarioRead])
def list_scenarios(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
) -> list[ScenarioRead]:
    return planning_service.list_scenarios(db, student.id)


@router.post("/scenarios", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def create_scenario(
    data: ScenarioWrite,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ScenarioRead:
    return planning_service.create_scenario(db, student.id, data)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ScenarioRead:
    return planning_service.get_scenario_read(db, student.id, scenario_id)


@router.patch("/scenarios/{scenario_id}", response_model=ScenarioRead)
def update_scenario(
    scenario_id: int,
    data: ScenarioUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ScenarioRead:
    return planning_service.update_scenario(db, student.id, scenario_id, data)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    planning_service.delete_scenario(db, student.id, scenario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

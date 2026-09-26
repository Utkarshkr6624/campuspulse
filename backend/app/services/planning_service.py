from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.db.session import commit_or_conflict
from app.models.course_mark import CourseMark
from app.models.planning import AcademicTarget, WhatIfScenario
from app.models.semester import Semester
from app.schemas.academic import GpaRead
from app.schemas.planning import (
    AcademicTargetRead,
    AssessmentScenarioInput,
    ScenarioProjection,
    ScenarioRead,
    ScenarioWrite,
    ScenarioUpdate,
    ScenarioCourseResult,
    TargetType,
)
from app.services import academic_service, course_service, grading_scheme_service
from app.services.academic import (
    GradeBandRule,
    GradedCourseInput,
    WeightedAssessmentInput,
    compute_course_score,
    compute_gpa,
    compute_grade,
)
from app.services.analytics_service import project_cgpa_from_semester_scenario


def list_targets(db: Session, student_id: int) -> list[AcademicTargetRead]:
    targets = db.scalars(
        select(AcademicTarget).where(AcademicTarget.student_id == student_id).order_by(AcademicTarget.target_type)
    ).all()
    return [_target_read(db, student_id, target) for target in targets]


def put_target(db: Session, student_id: int, target_type: TargetType, value: float) -> AcademicTargetRead:
    target = db.scalar(select(AcademicTarget).where(
        AcademicTarget.student_id == student_id,
        AcademicTarget.target_type == target_type,
    ))
    if target is None:
        target = AcademicTarget(student_id=student_id, target_type=target_type, target_value=value)
        db.add(target)
    else:
        target.target_value = value
    commit_or_conflict(db, "Could not save this academic target.")
    db.refresh(target)
    return _target_read(db, student_id, target)


def delete_target(db: Session, student_id: int, target_type: TargetType) -> None:
    target = db.scalar(select(AcademicTarget).where(
        AcademicTarget.student_id == student_id,
        AcademicTarget.target_type == target_type,
    ))
    if target is None:
        raise NotFoundError("Academic target not found.")
    db.delete(target)
    commit_or_conflict(db, "Could not delete this academic target.")


def _target_read(db: Session, student_id: int, target: AcademicTarget) -> AcademicTargetRead:
    current = (
        academic_service.get_semester_gpa(db, student_id)
        if target.target_type == "SGPA"
        else academic_service.get_cgpa(db, student_id)
    )
    value = current.value
    return AcademicTargetRead(
        id=target.id,
        target_type=target.target_type,
        target_value=target.target_value,
        current_value=value,
        status="INSUFFICIENT_DATA" if value is None else "REACHED" if value >= target.target_value else "IN_PROGRESS",
        remaining=None if value is None else round(max(0, target.target_value - value), 2),
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


def preview_scenario(
    db: Session, student_id: int, assessments: list[AssessmentScenarioInput]
) -> ScenarioProjection:
    current_semester_id = db.scalar(select(Semester.id).where(
        Semester.student_id == student_id,
        Semester.is_current.is_(True),
    ))
    performances = academic_service.list_course_performance(
        db, student_id, semester_id=current_semester_id
    )
    by_course = {item.course.id: item for item in performances}
    if not by_course:
        raise BadRequestError("Enroll in courses for the current semester before running a mark scenario.")

    overrides: dict[int, dict[str, AssessmentScenarioInput]] = {}
    for item in assessments:
        if item.course_id not in by_course:
            course_service.get_course(db, item.course_id, student_id)
            raise BadRequestError("Choose an enrolled course in the current semester for each scenario mark.")
        overrides.setdefault(item.course_id, {})[item.assessment_type] = item

    course_ids = list(overrides)
    marks = db.scalars(select(CourseMark).where(
        CourseMark.student_id == student_id,
        CourseMark.course_id.in_(course_ids),
    )).all()
    marks_by_course: dict[int, dict[str, tuple[float, float]]] = {course_id: {} for course_id in course_ids}
    for mark in marks:
        marks_by_course[mark.course_id][mark.assessment_type] = (mark.marks_obtained, mark.maximum_marks)

    projected_inputs: list[GradedCourseInput] = []
    results: list[ScenarioCourseResult] = []
    for performance in performances:
        simulated = performance.course.id in overrides
        if not simulated:
            projected_inputs.append(GradedCourseInput(
                course_id=performance.course.id,
                credits=performance.credits,
                grade_point=performance.grade_point or 0.0,
                status=performance.status,
            ))
            continue

        actual_score = performance.final_score
        actual_grade = performance.grade
        course = course_service.get_course(db, performance.course.id, student_id)
        scheme = grading_scheme_service.resolve_scheme_for_course(db, course.grading_scheme_id)
        weights = {weight.assessment_type: weight.weight_percent for weight in scheme.weights}
        merged = dict(marks_by_course[course.id])
        for assessment_type, item in overrides[course.id].items():
            merged[assessment_type] = (item.marks_obtained, item.maximum_marks)
        score = compute_course_score(
            [
                WeightedAssessmentInput(
                    assessment_type=assessment_type,
                    marks_obtained=obtained,
                    maximum_marks=maximum,
                    weight_percent=weights.get(assessment_type, 0.0),
                )
                for assessment_type, (obtained, maximum) in merged.items()
            ],
            weights,
        )
        projected_grade = None
        grade_point = 0.0
        if score.status == "complete" and score.final_score is not None:
            bands = [GradeBandRule(b.letter, b.min_score, b.max_score, b.grade_point) for b in scheme.grade_bands]
            grade = compute_grade(score.final_score, bands)
            projected_grade = grade.letter
            grade_point = grade.grade_point
        projected_inputs.append(GradedCourseInput(
            course_id=course.id,
            credits=performance.credits,
            grade_point=grade_point,
            status=score.status,
        ))
        results.append(ScenarioCourseResult(
            course=performance.course,
            current_score=actual_score,
            projected_score=score.final_score,
            current_grade=actual_grade,
            projected_grade=projected_grade,
            source="SCENARIO",
        ))

    current_sgpa = academic_service.get_semester_gpa(db, student_id)
    current_cgpa = academic_service.get_cgpa(db, student_id)
    projected_result = compute_gpa(projected_inputs)
    projected_sgpa = GpaRead(
        status=projected_result.status,
        value=projected_result.value,
        credited_courses=projected_result.credited_courses,
        total_credits=projected_result.total_credits,
        semester=current_sgpa.semester,
        message=projected_result.message,
    )
    projected_cgpa = project_cgpa_from_semester_scenario(db, student_id, projected_sgpa)
    return ScenarioProjection(
        current_sgpa=current_sgpa,
        projected_sgpa=projected_sgpa,
        current_cgpa=current_cgpa,
        projected_cgpa=projected_cgpa,
        courses=results,
        note="Hypothetical marks use the configured weights and grade bands. Saved scenarios contain inputs only; actual marks are unchanged.",
    )


def list_scenarios(db: Session, student_id: int) -> list[ScenarioRead]:
    rows = db.scalars(select(WhatIfScenario).where(
        WhatIfScenario.student_id == student_id
    ).order_by(WhatIfScenario.updated_at.desc())).all()
    return [_scenario_read(db, student_id, row) for row in rows]


def get_scenario(db: Session, student_id: int, scenario_id: int) -> WhatIfScenario:
    row = db.scalar(select(WhatIfScenario).where(
        WhatIfScenario.id == scenario_id,
        WhatIfScenario.student_id == student_id,
    ))
    if row is None:
        raise NotFoundError("Scenario not found.")
    return row


def get_scenario_read(db: Session, student_id: int, scenario_id: int) -> ScenarioRead:
    return _scenario_read(db, student_id, get_scenario(db, student_id, scenario_id))


def create_scenario(db: Session, student_id: int, data: ScenarioWrite) -> ScenarioRead:
    preview_scenario(db, student_id, data.assessments)
    row = WhatIfScenario(
        student_id=student_id,
        title=data.title,
        assessments=[item.model_dump() for item in data.assessments],
        notes=data.notes,
    )
    db.add(row)
    commit_or_conflict(db, "Could not save this scenario.")
    db.refresh(row)
    return _scenario_read(db, student_id, row)


def update_scenario(db: Session, student_id: int, scenario_id: int, data: ScenarioUpdate) -> ScenarioRead:
    row = get_scenario(db, student_id, scenario_id)
    changes = data.model_dump(exclude_unset=True)
    if "assessments" in changes and changes["assessments"] is not None:
        changes["assessments"] = [item.model_dump() for item in data.assessments or []]
        preview_scenario(db, student_id, data.assessments or [])
    for field, value in changes.items():
        setattr(row, field, value)
    commit_or_conflict(db, "Could not update this scenario.")
    db.refresh(row)
    return _scenario_read(db, student_id, row)


def delete_scenario(db: Session, student_id: int, scenario_id: int) -> None:
    row = get_scenario(db, student_id, scenario_id)
    db.delete(row)
    commit_or_conflict(db, "Could not delete this scenario.")


def compare_scenarios(db: Session, student_id: int, scenario_ids: list[int]) -> list[ScenarioRead]:
    rows = [get_scenario(db, student_id, scenario_id) for scenario_id in scenario_ids]
    return [_scenario_read(db, student_id, row) for row in rows]


def _scenario_read(db: Session, student_id: int, row: WhatIfScenario) -> ScenarioRead:
    assessments = [AssessmentScenarioInput.model_validate(item) for item in row.assessments]
    return ScenarioRead(
        id=row.id,
        title=row.title,
        assessments=assessments,
        notes=row.notes,
        projection=preview_scenario(db, student_id, assessments),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.errors import APIError
from app.models.rfp_project import RFPProject, RFPStatus
from app.models.rfp_question import RFPQuestion
from app.api.schemas.rfp import RFPProjectResponse, RFPQuestionResponse
from app.services.storage import StorageService
from app.workers.rfp_tasks import process_rfp_task

router = APIRouter(prefix="/api/rfps", tags=["rfps"])

@router.post("/")
async def upload_rfp(
    file: UploadFile = File(...),
    rfp_name: str = Form(...),
    db: Session = Depends(get_db)
):
    file_content = await file.read()
    file_url = StorageService.upload_file(file_content, file.filename, bucket="rfps")
    
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    rfp_project = RFPProject(
        user_id=user_id,
        rfp_name=rfp_name,
        rfp_file_url=file_url,
        status=RFPStatus.PENDING
    )
    
    db.add(rfp_project)
    db.commit()
    db.refresh(rfp_project)
    
    process_rfp_task.delay(str(rfp_project.id))
    
    return {
        "success": True,
        "message": "RFP processing started",
        "job_id": f"rfp_{rfp_project.id}"
    }

@router.get("/", response_model=List[RFPProjectResponse])
def get_rfps(db: Session = Depends(get_db)):
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    rfps = db.query(RFPProject).filter(RFPProject.user_id == user_id).all()
    return rfps

@router.get("/{rfp_id}", response_model=dict)
def get_rfp_with_questions(rfp_id: str, db: Session = Depends(get_db)):
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    rfp = db.query(RFPProject).filter(
        RFPProject.id == rfp_id,
        RFPProject.user_id == user_id
    ).first()
    
    if not rfp:
        raise APIError(status_code=404, message="RFP not found")
    
    questions = db.query(RFPQuestion).filter(
        RFPQuestion.project_id == rfp_id
    ).all()
    
    return {
        "rfp": RFPProjectResponse.from_orm(rfp),
        "questions": [RFPQuestionResponse.from_orm(q) for q in questions]
    }

@router.delete("/{rfp_id}")
def delete_rfp(rfp_id: str, db: Session = Depends(get_db)):
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    rfp = db.query(RFPProject).filter(
        RFPProject.id == rfp_id,
        RFPProject.user_id == user_id
    ).first()
    
    if not rfp:
        raise APIError(status_code=404, message="RFP not found")
    
    db.query(RFPQuestion).filter(RFPQuestion.project_id == rfp_id).delete()
    StorageService.delete_file(rfp.rfp_file_url, bucket="rfps")
    db.delete(rfp)
    db.commit()
    
    return {"success": True, "message": "RFP deleted"}
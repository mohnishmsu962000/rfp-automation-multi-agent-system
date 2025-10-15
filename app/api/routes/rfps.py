from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.errors import APIError
from app.models.rfp_project import RFPProject, RFPStatus
from app.models.rfp_question import RFPQuestion
from app.api.schemas.rfp import RFPProjectResponse, RFPQuestionResponse
from app.services.storage import StorageService
from app.workers.rfp_tasks import process_rfp_task
from app.api.schemas.rfp import QuestionUpdate
from datetime import datetime
from uuid import UUID
from app.services.llm_factory import LLMFactory
from app.prompts.answer_generator import REPHRASE_ANSWER_SYSTEM, REPHRASE_ANSWER_USER
from langchain_core.messages import SystemMessage, HumanMessage
from app.api.schemas.rfp import RephraseRequest
from fastapi.responses import StreamingResponse
from app.services.export_service import ExportService
import io
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/rfps", tags=["rfps"])

@router.post("/", response_model=dict)
async def upload_rfp(
    file: UploadFile = File(...),
    rfp_name: str = Form(...),
    db: Session = Depends(get_db)
):
    HARDCODED_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    allowed, used, remaining = RateLimiter.check_rfp_quota(HARDCODED_USER_ID, db)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly RFP limit reached. You have created {used}/20 RFPs this month."
        )
    
    file_content = await file.read()
    file_url = StorageService.upload_file(file_content, file.filename, bucket="rfps")
    
    rfp = RFPProject(
        user_id=HARDCODED_USER_ID,
        rfp_name=rfp_name,
        rfp_file_url=file_url,
        status=RFPStatus.PENDING
    )
    
    db.add(rfp)
    db.commit()
    db.refresh(rfp)
    
    process_rfp_task.delay(str(rfp.id))
    
    return {
        "success": True,
        "message": f"RFP processing started. {remaining - 1} RFPs remaining this month.",
        "job_id": f"rfp_{rfp.id}"
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


@router.patch("/{rfp_id}/questions/{question_id}", response_model=dict)
def update_question_answer(
    rfp_id: UUID,
    question_id: UUID,
    data: QuestionUpdate,
    db: Session = Depends(get_db)
):
    HARDCODED_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    rfp = db.query(RFPProject).filter(
        RFPProject.id == rfp_id,
        RFPProject.user_id == HARDCODED_USER_ID
    ).first()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    question = db.query(RFPQuestion).filter(
        RFPQuestion.id == question_id,
        RFPQuestion.project_id == rfp_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.answer_text = data.answer_text
    question.user_edited = True
    question.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(question)
    
    return {
        "success": True,
        "message": "Answer updated successfully",
        "question_id": str(question.id)
    }
    


@router.post("/{rfp_id}/questions/{question_id}/rephrase", response_model=dict)
def rephrase_answer(
    rfp_id: UUID,
    question_id: UUID,
    data: RephraseRequest,
    db: Session = Depends(get_db)
):
    HARDCODED_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    rfp = db.query(RFPProject).filter(
        RFPProject.id == rfp_id,
        RFPProject.user_id == HARDCODED_USER_ID
    ).first()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    question = db.query(RFPQuestion).filter(
        RFPQuestion.id == question_id,
        RFPQuestion.project_id == rfp_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    sources_text = "No specific sources available for this answer."
    if question.source_ids and len(question.source_ids) > 0:
        sources_text = "\n".join([f"- Source {i+1}" for i in range(len(question.source_ids))])
    
    prompt = REPHRASE_ANSWER_USER.format(
        question=question.question_text,
        current_answer=question.answer_text,
        sources=sources_text,
        instruction=data.instruction
    )
    
    llm = LLMFactory.get_llm("gemini-flash")
    
    response = llm.invoke([
        SystemMessage(content=REPHRASE_ANSWER_SYSTEM),
        HumanMessage(content=prompt)
    ])
    
    return {
        "success": True,
        "original_answer": question.answer_text,
        "rephrased_answer": response.content,
        "instruction": data.instruction,
        "note": "This is a preview. Use PATCH endpoint to save if you want to keep it."
    }
    
    

@router.get("/{rfp_id}/export")
def export_rfp(
    rfp_id: UUID,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    HARDCODED_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    rfp = db.query(RFPProject).filter(
        RFPProject.id == rfp_id,
        RFPProject.user_id == HARDCODED_USER_ID
    ).first()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    questions = db.query(RFPQuestion).filter(
        RFPQuestion.project_id == rfp_id
    ).order_by(RFPQuestion.created_at).all()
    
    if not questions:
        raise HTTPException(status_code=400, detail="No questions found for this RFP")
    
    if format == "xlsx":
        content = ExportService.export_to_excel(rfp, questions)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{rfp.rfp_name.replace(' ', '_')}.xlsx"
    elif format == "docx":
        content = ExportService.export_to_docx(rfp, questions)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{rfp.rfp_name.replace(' ', '_')}.docx"
    elif format == "pdf":
        content = ExportService.export_to_pdf(rfp, questions)
        media_type = "application/pdf"
        filename = f"{rfp.rfp_name.replace(' ', '_')}.pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use xlsx, docx, or pdf")
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
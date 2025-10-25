from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.rfp_project import RFPProject, RFPStatus
from app.models.rfp_question import RFPQuestion
from app.services.rfp_parser import RFPParser
from app.agents.answer_generator import generate_answer_for_question
import httpx
import tempfile
import os
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_rfp")
def process_rfp_task(rfp_id: str):
    db = SessionLocal()
    rfp = None 
    
    try:
        rfp = db.query(RFPProject).filter(RFPProject.id == rfp_id).first()
        if not rfp:
            return {"error": "RFP not found"}
        
        rfp.status = RFPStatus.PROCESSING
        db.commit()
        
        response = httpx.get(rfp.rfp_file_url)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(rfp.rfp_name)[1]) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        filename = rfp.rfp_file_url.split('/')[-1]
        questions = RFPParser.extract_questions(tmp_path, filename)
        os.unlink(tmp_path)
        
        logger.info(f"Processing {len(questions)} questions sequentially")
        
        for i, question_text in enumerate(questions):
            try:
                logger.info(f"Processing question {i+1}/{len(questions)}: {question_text[:100]}")
                
                answer_result = generate_answer_for_question(
                    question_text, 
                    db, 
                    str(rfp.user_id), 
                    UUID(str(rfp.company_id))
                )
                
                rfp_question = RFPQuestion(
                    project_id=rfp.id,
                    question_text=question_text,
                    answer_text=answer_result["answer"],
                    trust_score=float(answer_result["trust_score"]),
                    source_type=answer_result.get("source_type", "rag"),
                    user_edited=False
                )
                db.add(rfp_question)
                db.commit()
                
                logger.info(f"Question {i+1} processed successfully")
                
            except Exception as e:
                logger.error(f"Error processing question {i+1}: {str(e)}")
                rfp_question = RFPQuestion(
                    project_id=rfp.id,
                    question_text=question_text,
                    answer_text=f"Error generating answer: {str(e)}",
                    trust_score=0.0,
                    source_type="error",
                    user_edited=False
                )
                db.add(rfp_question)
                db.commit()
        
        rfp.status = RFPStatus.COMPLETED
        db.commit()
        
        return {"status": "completed", "rfp_id": str(rfp_id), "questions_count": len(questions)}
    
    except Exception as e:
        logger.error(f"RFP processing failed: {str(e)}")
        if rfp:
            rfp.status = RFPStatus.FAILED
            db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()
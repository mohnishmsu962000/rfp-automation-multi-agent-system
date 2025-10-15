from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.rfp_project import RFPProject, RFPStatus
from app.models.rfp_question import RFPQuestion
from app.services.rfp_parser import RFPParser
from app.agents.answer_generator import generate_answer_for_question
import httpx
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID

def process_single_question(question_text: str, rfp_id: str, user_id: str):
    db = SessionLocal()
    try:
        answer_result = generate_answer_for_question(question_text, db, UUID(user_id))
        return {
            "question": question_text,
            "answer": answer_result["answer"],
            "trust_score": float(answer_result["trust_score"]),
            "source_type": answer_result.get("source_type", "rag")
        }
    finally:
        db.close()

@celery_app.task(name="process_rfp")
def process_rfp_task(rfp_id: str):
    db = SessionLocal()
    
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
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_single_question, q, str(rfp.id), str(rfp.user_id)): q for q in questions}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    question = futures[future]
                    results.append({
                        "question": question,
                        "answer": f"Error generating answer: {str(e)}",
                        "trust_score": 0.0,
                        "source_type": "error"
                    })
        
        for result in results:
            rfp_question = RFPQuestion(
                project_id=rfp.id,
                question_text=result["question"],
                answer_text=result["answer"],
                trust_score=result["trust_score"],
                source_type=result.get("source_type", "rag"),
                user_edited=False
            )
            db.add(rfp_question)
        
        rfp.status = RFPStatus.COMPLETED
        db.commit()
        
        return {"status": "completed", "rfp_id": str(rfp_id), "questions_count": len(questions)}
    
    except Exception as e:
        rfp.status = RFPStatus.FAILED
        db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()
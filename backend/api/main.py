"""
FastAPI Application
REST API for ApplyWise
Handles file uploads, processing, and output delivery
"""

import logging
import io
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)


# ===== Pydantic Models =====

class ApplicationRequest(BaseModel):
    """Request model for job application processing"""
    job_description: str
    applicant_name: str
    applicant_email: str


class ExecutionSummary(BaseModel):
    """Summary of execution"""
    status: str
    job_id: str
    quality_score: float
    ready_for_submission: bool
    documents_generated: list


# ===== FastAPI Setup =====

def create_app(orchestrator, resume_parser, storage_service, document_service):
    """
    Factory function to create and configure FastAPI app
    
    Args:
        orchestrator: SupervisorOrchestrator instance
        resume_parser: ResumeParser instance
        storage_service: StorageService instance
        document_service: DocumentService instance
    
    Returns:
        Configured FastAPI application
    """
    
    app = FastAPI(
        title="ApplyWise",
        description="From Job Post to Polished Application",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ===== ROUTES =====
    
    def api_info():
        return {
            "name": "ApplyWise",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                "POST /api/process - Process job application",
                "GET /api/results/{job_id} - Get application results",
                "GET /api/download/{job_id}/{file_type} - Download documents",
                "GET /health - Health check"
            ]
        }

    @app.get("/api/info")
    async def root():
        """API information endpoint"""
        return api_info()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "ApplyWise"
        }
    
    @app.post("/api/process")
    async def process_application(
        job_description: str = Form(...),
        applicant_name: str = Form(...),
        applicant_email: str = Form(...),
        resume_file: UploadFile = File(...)
    ):
        """
        Process a job application
        
        Args:
            job_description: Job posting text
            applicant_name: Applicant's full name
            applicant_email: Applicant's email
            resume_file: Uploaded resume (PDF or DOCX)
        
        Returns:
            Job ID and processing status
        """
        try:
            logger.info(f" New application request from {applicant_name}")
            
            # Generate job ID
            job_id = storage_service.generate_job_id()
            
            # Read and save resume file
            resume_content = await resume_file.read()
            upload_path = storage_service.save_upload(
                resume_content,
                resume_file.filename,
                job_id
            )
            logger.info(f"✓ Resume saved: {upload_path}")
            
            # Parse resume
            parsed_resume = resume_parser.parse_file(upload_path)
            resume_text = parsed_resume['raw_text']
            logger.info(f"✓ Resume parsed: {parsed_resume['word_count']} words")
            
            # Process through orchestrator
            logger.info(f" Processing application {job_id}")
            application_package = await orchestrator.process_application(
                job_description=job_description,
                resume_data=resume_text,
                applicant_name=applicant_name,
                applicant_email=applicant_email,
                job_id=job_id
            )
            
            # Prepare response
            response = {
                'job_id': job_id,
                'status': application_package['status'],
                'message': 'Application processed successfully' if application_package['status'] == 'completed' else 'Processing failed'
            }
            
            if application_package['status'] == 'completed':
                response['quality_score'] = application_package['quality_metrics']['overall_score']
                response['ready_for_submission'] = application_package['quality_metrics']['ready_for_submission']
                response['component_scores'] = application_package['quality_metrics'].get('component_scores', {})
                response['job_title'] = application_package.get('job_info', {}).get('job_title', 'Unknown Position')
                response['company'] = application_package.get('job_info', {}).get('company_name', 'Unknown Company')
                response['agent_outputs'] = application_package.get('agent_outputs', {})
                response['execution_log'] = application_package.get('execution_log', [])
                response['improvements'] = (
                    application_package
                    .get('agent_outputs', {})
                    .get('critic', {})
                    .get('output', {})
                    .get('improvements', [])
                )
                response['documents'] = {
                    'resume': application_package['documents']['resume'].replace('\\', '/').split('/')[-1],
                    'cover_letter': application_package['documents']['cover_letter'].replace('\\', '/').split('/')[-1]
                }
            else:
                response['error'] = application_package.get('error', 'Unknown error')
            
            logger.info(f" Application {job_id} processed: {response['status']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/results/{job_id}")
    async def get_results(job_id: str):
        """
        Get results for a specific job application
        
        Args:
            job_id: Job application identifier
        
        Returns:
            Complete application results and quality metrics
        """
        try:
            logger.info(f"📋 Fetching results for {job_id}")
            
            # List output files
            outputs = storage_service.list_job_outputs(job_id)
            
            if not outputs:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
            # Get file info
            files_info = []
            for output_path in outputs:
                info = storage_service.get_file_info(output_path)
                files_info.append({
                    'name': info['name'],
                    'size_kb': round(info['size'] / 1024, 2),
                    'modified': info.get('modified')
                })
            
            return {
                'job_id': job_id,
                'files': files_info,
                'ready_for_download': len(files_info) > 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching results: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/download/{job_id}/{file_type}")
    async def download_document(job_id: str, file_type: str):
        """
        Download generated documents
        
        Args:
            job_id: Job application identifier
            file_type: 'resume' or 'cover_letter'
        
        Returns:
            File download
        """
        try:
            logger.info(f"📥 Download request: {job_id}/{file_type}")
            
            # Determine filename pattern
            if file_type == 'resume':
                pattern = 'Resume_'
                media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_type == 'cover_letter':
                pattern = 'CoverLetter_'
                media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                raise HTTPException(status_code=400, detail="Invalid file type")
            
            # List and find matching file
            outputs = storage_service.list_job_outputs(job_id)
            matching_files = [f for f in outputs if pattern in f.replace('\\', '/').split('/')[-1]]
            
            if not matching_files:
                raise HTTPException(status_code=404, detail=f"File not found for job {job_id}")
            
            file_path = matching_files[0]
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=file_path.replace('\\', '/').split('/')[-1]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Download error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/cleanup/{job_id}")
    async def cleanup_job(job_id: str):
        """
        Clean up files for a job (delete after download)
        
        Args:
            job_id: Job identifier
        
        Returns:
            Cleanup status
        """
        try:
            logger.info(f"🧹 Cleaning up job {job_id}")
            storage_service.cleanup_job(job_id)
            return {
                'job_id': job_id,
                'message': 'Cleanup complete'
            }
        except Exception as e:
            logger.error(f"❌ Cleanup error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== Error Handlers =====
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions"""
        logger.error(f"HTTP Exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

    # Serve the production React build from the same FastAPI backend.
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    frontend_index = frontend_dist / "index.html"

    if frontend_index.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/")
        async def serve_frontend_root():
            return FileResponse(str(frontend_index))

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            requested_path = frontend_dist / full_path
            if requested_path.is_file():
                return FileResponse(str(requested_path))
            return FileResponse(str(frontend_index))
    else:
        @app.get("/")
        async def root_without_frontend():
            return api_info()
    
    return app


if __name__ == "__main__":
    """Run the API"""
    import uvicorn
    
    print("\n🚀 Starting API server...")
    print("⚠️  Note: This requires all dependencies to be initialized")
    print("Use main.py to start the complete application\n")

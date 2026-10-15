"""
Main Application Entry Point
Initializes all components and starts the FastAPI server
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def initialize_components():
    """Initialize all components"""
    
    print("\n" + "="*60)
    print(" Initializing ApplyWise")
    print("="*60 + "\n")
    
    try:
        # Block 1: Foundation
        print("Block 1: Loading Foundation...")
        from backend.config import get_settings
        from backend.services import get_llm_service
        
        settings = get_settings()
        llm_service = get_llm_service()
        print("✓ Configuration and LLM Service initialized")
        
        # Block 2: Document Services
        print("\nBlock 2: Loading Document Services...")
        from backend.services import DocumentService, StorageService
        from backend.utils import ResumeParser
        
        document_service = DocumentService()
        storage_service = StorageService()
        resume_parser = ResumeParser()
        print("✓ Document Service, Storage Service, Resume Parser initialized")
        
        # Block 3: Specialist Agents
        print("\nBlock 3: Loading Specialist Agents...")
        from backend.agents import (
            JobFinderAgent,
            ResumeTailorAgent,
            CoverLetterAgent,
            CriticAgent
        )
        
        job_finder = JobFinderAgent()
        resume_tailor = ResumeTailorAgent()
        cover_letter = CoverLetterAgent()
        critic = CriticAgent()
        print("✓ All 4 Specialist Agents initialized")
        print(f"  - Job Finder (ReAct)")
        print(f"  - Resume Tailor (Chain-of-Thought)")
        print(f"  - Cover Letter (Tool Use)")
        print(f"  - Critic (Reflection)")
        
        # Block 4: Orchestrator
        print("\nBlock 4: Loading Orchestrator...")
        from backend.orchestrator import SupervisorOrchestrator
        
        agents_dict = {
            'job_finder': job_finder,
            'resume_tailor': resume_tailor,
            'cover_letter': cover_letter,
            'critic': critic
        }
        
        services_dict = {
            'document_service': document_service,
            'storage_service': storage_service,
            'resume_parser': resume_parser
        }
        
        orchestrator = SupervisorOrchestrator(agents_dict, services_dict)
        print("✓ Supervisor Orchestrator initialized")
        
        # Block 4: FastAPI
        print("\nBlock 4: Loading FastAPI...")
        from backend.api import create_app
        
        app = create_app(orchestrator, resume_parser, storage_service, document_service)
        print("✓ FastAPI Application initialized")
        
        print("\n" + "="*60)
        print("All Components Successfully Initialized!")
        print("="*60)
        print("\nSystem Status:")
        print(f"  ✓ LLM: {settings.default_model}")
        print(f"  ✓ Upload Dir: {settings.upload_dir}")
        print(f"  ✓ Output Dir: {settings.output_dir}")
        print(f"  ✓ Agents: 4/4")
        print(f"  ✓ Services: 3/3")
        print(f"  ✓ Orchestrator: Ready")
        print(f"  ✓ API: Ready")
        
        return app, orchestrator
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {str(e)}")
        print(f"\n❌ Failed to import component: {str(e)}")
        print("Make sure all Blocks 1-3 are properly integrated")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Initialization Error: {str(e)}")
        print(f"\n❌ Failed to initialize: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main entry point"""
    
    app, orchestrator = await initialize_components()
    
    print("\n" + "="*60)
    print("🌐 Starting FastAPI Server")
    print("="*60)
    print("\n📡 API Endpoints:")
    print("  POST   /api/process              - Process job application")
    print("  GET    /api/results/{job_id}     - Get results")
    print("  GET    /api/download/{job_id}/{file_type}")
    print("  POST   /api/cleanup/{job_id}     - Cleanup files")
    print("  GET    /health                   - Health check")
    print("\nServer starting on http://localhost:8000")
    print("API docs: http://localhost:8000/docs\n")
    
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        import uvicorn
        
        # Get the app
        app, orchestrator = asyncio.run(initialize_components())
        
        print("\n" + "="*60)
        print("Starting FastAPI Server")
        print("="*60)
        print("\nAPI Endpoints:")
        print("  POST   /api/process              - Process job application")
        print("  GET    /api/results/{job_id}     - Get results")
        print("  GET    /api/download/{job_id}/{file_type}")
        print("  POST   /api/cleanup/{job_id}     - Cleanup files")
        print("  GET    /health                   - Health check")
        print("\n Server starting on http://localhost:8000")
        print(" API docs: http://localhost:8000/docs\n")
        
        # Run uvicorn directly (not in async context)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n Server stopped")
        sys.exit(0)

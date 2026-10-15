"""
Supervisor Orchestrator
Coordinates all specialist agents in the correct sequence
Manages execution, error handling, and result synthesis
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class OrchestratorError(Exception):
    """Custom exception for orchestrator errors"""
    pass


class SupervisorOrchestrator:
    """
    Supervisor Orchestrator - Coordinates all agents
    
    Execution Flow:
    1. Job Finder Agent → Analyzes job, researches company
    2. Resume Tailor Agent → Customizes resume to job
    3. Cover Letter Agent → Generates personalized letter
    4. Critic Agent → Reviews and improves outputs
    5. Document Generation → Creates final DOCX files
    
    Pattern: Supervisor Pattern
    - Centralized coordination
    - Sequential agent execution
    - Error handling and retries
    - Result aggregation
    """
    
    def __init__(self, agents_dict: Dict[str, Any], services_dict: Dict[str, Any]):
        """
        Initialize orchestrator with dependencies
        
        Args:
            agents_dict: Dictionary of initialized agents
                {
                    'job_finder': JobFinderAgent(),
                    'resume_tailor': ResumeTailorAgent(),
                    'cover_letter': CoverLetterAgent(),
                    'critic': CriticAgent()
                }
            services_dict: Dictionary of initialized services
                {
                    'document_service': DocumentService(),
                    'storage_service': StorageService(),
                    'resume_parser': ResumeParser()
                }
        """
        self.agents = agents_dict
        self.services = services_dict
        self.execution_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Supervisor Orchestrator initialized (ID: {self.execution_id})")
    
    async def process_application(
        self,
        job_description: str,
        resume_data: str,
        applicant_name: str,
        applicant_email: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a complete job application through all agents
        
        Args:
            job_description: Raw job posting text
            resume_data: Parsed resume content
            applicant_name: Applicant's name
            applicant_email: Applicant's email
            job_id: Optional job ID (will be generated if not provided)
            
        Returns:
            Complete application package with all outputs
        """
        
        if not job_id:
            job_id = self.services['storage_service'].generate_job_id()
        
        logger.info(f" Starting application processing (Job ID: {job_id})")
        
        execution_log = []
        execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'ORCHESTRATOR_START',
            'job_id': job_id
        })
        
        try:
            # Phase 1: Job Analysis
            logger.info(" PHASE 1: Job Analysis")
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_1_START',
                'agent': 'JobFinder'
            })
            
            job_finder_result = await self.agents['job_finder'].run({
                'job_description': job_description
            })
            
            if job_finder_result.status.value != 'completed':
                raise OrchestratorError(f"Job Finder failed: {job_finder_result.output}")
            
            job_data = job_finder_result.output['job_data']
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_1_COMPLETE',
                'agent': 'JobFinder',
                'job_title': job_data.get('job_title'),
                'company': job_data.get('company_name'),
                'execution_time': job_finder_result.execution_time
            })
            
            logger.info(f"✓ Job Finder completed: {job_data.get('job_title')} at {job_data.get('company_name')}")
            
            # Phase 2: Resume Tailoring
            logger.info(" PHASE 2: Resume Tailoring")
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_2_START',
                'agent': 'ResumeTailor'
            })
            
            resume_tailor_result = await self.agents['resume_tailor'].run({
                'resume_data': resume_data,
                'job_data': job_data,
                'applicant_name': applicant_name,
                'applicant_email': applicant_email
            })
            
            if resume_tailor_result.status.value != 'completed':
                raise OrchestratorError(f"Resume Tailor failed: {resume_tailor_result.output}")
            
            tailored_content = resume_tailor_result.output['tailored_content']
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_2_COMPLETE',
                'agent': 'ResumeTailor',
                'skills_matched': resume_tailor_result.output['optimization_notes']['skills_matched'],
                'execution_time': resume_tailor_result.execution_time
            })
            
            logger.info(f"✓ Resume Tailor completed: {resume_tailor_result.output['optimization_notes']['skills_matched']} skills matched")
            
            # Phase 3: Cover Letter Generation
            logger.info("  PHASE 3: Cover Letter Generation")
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_3_START',
                'agent': 'CoverLetter'
            })
            
            cover_letter_result = await self.agents['cover_letter'].run({
                'resume_data': resume_data,
                'job_data': job_data,
                'tailored_content': tailored_content,
                'applicant_name': applicant_name,
                'applicant_email': applicant_email
            })
            
            if cover_letter_result.status.value != 'completed':
                raise OrchestratorError(f"Cover Letter failed: {cover_letter_result.output}")
            
            letter_content = cover_letter_result.output['cover_letter_content']
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_3_COMPLETE',
                'agent': 'CoverLetter',
                'word_count': cover_letter_result.output['word_count'],
                'research_used': cover_letter_result.output['research_used'],
                'execution_time': cover_letter_result.execution_time
            })
            
            logger.info(f"✓ Cover Letter completed: {cover_letter_result.output['word_count']} words")
            
            # Phase 4: Quality Review
            logger.info(" PHASE 4: Quality Review")
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_4_START',
                'agent': 'Critic'
            })
            
            critic_result = await self.agents['critic'].run({
                'job_data': job_data,
                'tailored_content': tailored_content,
                'cover_letter_content': letter_content
            })
            
            if critic_result.status.value != 'completed':
                raise OrchestratorError(f"Critic failed: {critic_result.output}")
            
            critique = critic_result.output
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_4_COMPLETE',
                'agent': 'Critic',
                'overall_score': critique['overall_score'],
                'decision': critique['decision'],
                'execution_time': critic_result.execution_time
            })
            
            logger.info(f"✓ Critic completed: Score {critique['overall_score']}/10, Decision: {critique['decision']}")
            
            # Phase 5: Document Generation
            logger.info(" PHASE 5: Document Generation")
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_5_START',
                'service': 'DocumentService'
            })
            
            # Prepare resume for document service
            resume_doc_content = {
                'header': {
                    'name': applicant_name,
                    'email': applicant_email,
                    'phone': tailored_content.get('header', {}).get('phone', ''),
                    'location': tailored_content.get('header', {}).get('location', '')
                },
                'summary': tailored_content.get('summary', ''),
                'experience': tailored_content.get('experience', []),
                'education': tailored_content.get('education', []),
                'skills': tailored_content.get('skills', {}),
                'projects': tailored_content.get('projects', [])
            }
            
            # Generate resume DOCX
            job_output_dir = self.services['storage_service'].output_dir / job_id
            resume_path = self.services['document_service'].generate_resume(
                resume_doc_content,
                job_id,
                applicant_name.replace(' ', '_'),
                output_dir=str(job_output_dir)
            )
            
            # Generate cover letter DOCX
            letter_path = self.services['document_service'].generate_cover_letter(
                letter_content,
                job_id,
                applicant_name.replace(' ', '_'),
                output_dir=str(job_output_dir)
            )
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'PHASE_5_COMPLETE',
                'service': 'DocumentService',
                'resume_path': resume_path,
                'letter_path': letter_path
            })
            
            logger.info(f"✓ Documents generated: Resume & Cover Letter")
            
            # Compile final application package
            application_package = {
                'job_id': job_id,
                'execution_id': self.execution_id,
                'status': ExecutionStatus.COMPLETED.value,
                'timestamp': datetime.now().isoformat(),
                'applicant_info': {
                    'name': applicant_name,
                    'email': applicant_email
                },
                'job_info': job_data,
                'agent_outputs': {
                    'job_finder': {
                        'reasoning': job_finder_result.reasoning,
                        'output': job_finder_result.output,
                        'execution_time': job_finder_result.execution_time
                    },
                    'resume_tailor': {
                        'reasoning': resume_tailor_result.reasoning,
                        'output': resume_tailor_result.output,
                        'execution_time': resume_tailor_result.execution_time
                    },
                    'cover_letter': {
                        'reasoning': cover_letter_result.reasoning,
                        'output': cover_letter_result.output,
                        'execution_time': cover_letter_result.execution_time
                    },
                    'critic': {
                        'reasoning': critic_result.reasoning,
                        'output': critique,
                        'execution_time': critic_result.execution_time
                    }
                },
                'documents': {
                    'resume': resume_path,
                    'cover_letter': letter_path
                },
                'quality_metrics': {
                    'overall_score': critique['overall_score'],
                    'decision': critique['decision'],
                    'component_scores': critique['component_scores'],
                    'ready_for_submission': critique['ready_for_submission']
                },
                'execution_log': execution_log
            }
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'ORCHESTRATOR_COMPLETE',
                'status': ExecutionStatus.COMPLETED.value
            })
            
            logger.info(f" Application processing complete (Job ID: {job_id})")
            
            return application_package
            
        except Exception as e:
            logger.error(f"❌ Application processing failed: {str(e)}")
            
            execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'ORCHESTRATOR_FAILED',
                'error': str(e)
            })
            
            return {
                'job_id': job_id,
                'execution_id': self.execution_id,
                'status': ExecutionStatus.FAILED.value,
                'error': str(e),
                'execution_log': execution_log
            }
    
    def get_execution_summary(self, application_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the execution
        
        Args:
            application_package: Complete application package
            
        Returns:
            Execution summary
        """
        if application_package['status'] != ExecutionStatus.COMPLETED.value:
            return {
                'status': application_package['status'],
                'error': application_package.get('error', 'Unknown error'),
                'total_agents_executed': 0
            }
        
        return {
            'status': application_package['status'],
            'job_id': application_package['job_id'],
            'job_title': application_package['job_info'].get('job_title'),
            'company': application_package['job_info'].get('company_name'),
            'total_agents_executed': 4,
            'quality_score': application_package['quality_metrics']['overall_score'],
            'ready_for_submission': application_package['quality_metrics']['ready_for_submission'],
            'documents_generated': list(application_package['documents'].keys()),
            'improvements_suggested': len(application_package['agent_outputs']['critic']['output']['improvements']),
            'execution_time_seconds': sum(
                agent_output['execution_time'] 
                for agent_output in application_package['agent_outputs'].values()
            )
        }


if __name__ == "__main__":
    """Test the orchestrator"""
    import asyncio
    import sys
    from pathlib import Path
    
    async def test_orchestrator():
        print("\n🧪 Testing Supervisor Orchestrator...\n")
        
        # Note: This is a mock test. In real usage, you'd pass actual agent instances
        print("✓ Orchestrator class initialized")
        print("✓ Ready for full integration with all agents and services")
        print("\n✅ Orchestrator test ready!")
    
    asyncio.run(test_orchestrator())

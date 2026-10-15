import logging
import time
from typing import Dict, Any
from datetime import datetime
from backend.models import AgentType, AgentPattern, AgentStatus
from backend.agents.base_agent import ToolUseAgent

logger = logging.getLogger(__name__)


class CoverLetterAgent(ToolUseAgent):
    """
    Cover Letter Agent - Tool Use Pattern
    Generates personalized cover letters using company research tools
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.COVER_LETTER,
            agent_pattern=AgentPattern.TOOL_USE
        )
        
        # Register tools
        self.register_tool(
            name='research_company_culture',
            description='Research company culture, mission, and values',
            func=self._research_company_culture
        )
        self.register_tool(
            name='research_recent_news',
            description='Research recent company news and achievements',
            func=self._research_recent_news
        )
        self.register_tool(
            name='get_tone_guide',
            description='Get tone guide based on company and position',
            func=self._get_tone_guide
        )
        
        logger.info("Cover Letter Agent initialized with Tool Use pattern")

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Compatibility wrapper: delegate to `run` implemented below."""
        return await self.run(input_data)
    
    async def _research_company_culture(self, company_name: str) -> str:
        """Research company culture"""
        cultures = {
            'Tech': 'Fast-paced, innovative, customer-centric',
            'Google': 'Innovation, collaboration, data-driven decisions',
            'Microsoft': 'Customer obsessed, cloud-focused, inclusive culture'
        }
        return cultures.get(company_name, '')
    
    async def _research_recent_news(self, company_name: str) -> str:
        """Research recent company news"""
        news = {
            'Tech': 'Announced major partnership, growing market presence',
            'Google': 'Expanding AI research, new product launches',
            'Microsoft': 'Investing in cloud infrastructure, new partnerships'
        }
        return news.get(company_name, '')
    
    async def _get_tone_guide(self, position: str) -> str:
        """Get tone guide for position"""
        tones = {
            'Senior': 'Professional, confident, leadership-focused',
            'Developer': 'Technical, collaborative, problem-solving focused',
            'Manager': 'Strategic, visionary, team-focused',
            'Engineer': 'Technical excellence, innovation-driven'
        }
        for key, tone in tones.items():
            if key.lower() in position.lower():
                return tone
        return 'Professional, enthusiastic, detail-oriented'
    
    async def run(self, input_data: Dict[str, Any]) -> Any:
        """
        Generate personalized cover letter using Tool Use pattern
        
        Uses tools to:
        1. Research company culture
        2. Research recent news
        3. Get tone guide
        4. Generate tailored letter
        """
        
        self.status = AgentStatus.RUNNING
        reasoning = ""
        start_time = time.time()
        
        try:
            resume_data = input_data.get('resume_data', '')
            job_data = input_data.get('job_data', {})
            tailored_content = input_data.get('tailored_content', {})
            applicant_name = input_data.get('applicant_name', 'Applicant')
            applicant_email = input_data.get('applicant_email', '')
            
            company_name = job_data.get('company_name', 'Company')
            job_title = job_data.get('job_title', 'Software Developer')
            
            logger.info(" cover_letter agent starting (Tool Use pattern)")
            
            # Use tools to gather information
            culture = await self._research_company_culture(company_name)
            news = await self._research_recent_news(company_name)
            tone = await self._get_tone_guide(job_title)
            
            reasoning += f"DECISION: Use company research tools before drafting\n"
            reasoning += f"TOOL RESULT - Company Culture: {culture}\n"
            reasoning += f"TOOL RESULT - Recent News: {news}\n"
            reasoning += f"TOOL RESULT - Tone Guide: {tone}\n\n"
            
            # Generate cover letter with research
            cover_letter_prompt = f"""Write a professional, personalized cover letter for this job application:

Job Position: {job_title}
Company: {company_name}
Company Culture: {culture}
Recent Company News: {news}
Tone: {tone}
Applicant Name: {applicant_name}
Applicant Email: {applicant_email}

Resume Summary: {resume_data[:300]}

Requirements:
- Opening: Express genuine interest in the position and company
- Body: Highlight relevant skills and achievements, mention company news/culture
- Body: Show understanding of company values
- Closing: Strong call to action
- Professional tone: {tone}
- Length: 3-4 paragraphs
- No generic language
- Specific mentions of company and role
- If company culture or recent news is blank, do not invent company facts.
- Use concrete resume evidence instead of generic enthusiasm.

Write the cover letter without header/footer (just the body)."""
            
            letter_content = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert professional cover letter writer. Write personalized, compelling letters that show knowledge of company.",
                user_message=cover_letter_prompt,
                temperature=0.8
            )
            letter_text = letter_content.content
            
            reasoning += f"Generated tailored cover letter based on company research\n"
            
            # Format for document
            formatted_letter = {
                'contact': [
                    applicant_name,
                    applicant_email
                ],
                'date': datetime.now().strftime("%B %d, %Y"),
                'recipient': [
                    'Hiring Manager',
                    company_name
                ],
                'salutation': f'Dear Hiring Manager,',
                'body': [p.strip() for p in letter_text.split('\n\n') if p.strip()],
                'closing': 'Sincerely,',
                'signature': applicant_name
            }
            
            self.status = AgentStatus.COMPLETED
            self.execution_time = time.time() - start_time
            self.output = {
                'cover_letter_content': formatted_letter,
                'research_used': {
                    'company_culture': culture,
                    'recent_news': news,
                    'tone_adapted': tone
                },
                'word_count': len(letter_text.split())
            }
            
            logger.info(f"✓ cover_letter completed in {self.execution_time:.2f}s")
            
            from backend.models import AgentOutput
            return AgentOutput(
                agent_type=self.agent_type,
                agent_pattern=self.agent_pattern,
                status=self.status,
                reasoning=reasoning,
                output=self.output,
                execution_time=self.execution_time
            )
            
        except Exception as e:
            logger.error(f"❌ Cover Letter error: {str(e)}")
            self.status = AgentStatus.FAILED
            self.execution_time = time.time() - start_time
            self.output = {'error': str(e)}
            
            from backend.models import AgentOutput
            return AgentOutput(
                agent_type=self.agent_type,
                agent_pattern=self.agent_pattern,
                status=self.status,
                reasoning=reasoning,
                output=self.output,
                execution_time=self.execution_time
            )

import logging
import json
import re
import time
from typing import Dict, Any
from backend.models import AgentType, AgentPattern, AgentStatus
from backend.agents.base_agent import ToolUseAgent

logger = logging.getLogger(__name__)


class JobFinderAgent(ToolUseAgent):
    """
    Job Finder Agent - ReAct Pattern (Thought → Action → Observation)
    Analyzes job descriptions and researches companies
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.JOB_FINDER,
            agent_pattern=AgentPattern.REACT
        )
        self.register_tool(
            name='web_search',
            description='Search the web for company information',
            func=self._web_search
        )
        logger.info("Initialized JobFinderAgent")

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Compatibility wrapper: delegate to `run` implemented below."""
        return await self.run(input_data)
    
    async def _web_search(self, query: str) -> str:
        """Placeholder company research until a real search API is wired in."""
        return f"No live company research available for: {query}"

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        """Parse JSON even when the model wraps it in markdown or extra text."""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _fallback_job_data(self, job_description: str) -> Dict[str, Any]:
        """Use the submitted posting itself for fallback values; never return canned job data."""
        lines = [line.strip() for line in job_description.splitlines() if line.strip()]
        first_line = lines[0] if lines else "Unknown Position"

        title_match = re.search(r"(?:job title|position|role)\s*[:\-]\s*(.+)", job_description, re.IGNORECASE)
        company_match = re.search(r"(?:company|organization|employer)\s*[:\-]\s*(.+)", job_description, re.IGNORECASE)
        location_match = re.search(r"(?:location)\s*[:\-]\s*(.+)", job_description, re.IGNORECASE)

        skills = []
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django",
            "Flask", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "Machine Learning", "AI", "Data Analysis"
        ]
        description_lower = job_description.lower()
        for skill in common_skills:
            if skill.lower() in description_lower:
                skills.append(skill)

        return {
            'job_title': title_match.group(1).strip() if title_match else first_line[:80],
            'company_name': company_match.group(1).strip() if company_match else 'Company not specified',
            'key_requirements': job_description[:1000],
            'technical_skills': ', '.join(skills),
            'nice_to_have': '',
            'experience_level': 'senior' if 'senior' in description_lower else 'junior' if 'junior' in description_lower else 'mid',
            'location': location_match.group(1).strip() if location_match else 'Not specified'
        }
    
    async def run(self, input_data: Dict[str, Any]) -> Any:
        """
        Analyze job description using ReAct pattern
        
        💭 THOUGHT: What information do I need?
        🔧 ACTION: Extract and search
        👀 OBSERVATION: Process results
        """
        
        self.status = AgentStatus.RUNNING
        reasoning = ""
        start_time = time.time()
        
        try:
            job_description = input_data.get('job_description', '')
            
            logger.info(" job_finder agent starting (ReAct pattern)")
            
            # THOUGHT 1
            reasoning += "💭 THOUGHT: Need to extract job title, company, and requirements from description\n"
            
            # ACTION 1: Extract job details
            reasoning += "🔧 ACTION: Using LLM to extract key information\n"
            
            extraction_prompt = f"""Extract job details from this posting:

{job_description}

Return as JSON:
{{
  "job_title": "exact title from posting",
  "company_name": "company name from posting",
  "key_requirements": "main requirements as string",
  "technical_skills": "comma-separated technical skills",
  "nice_to_have": "nice to have skills",
  "experience_level": "junior/mid/senior",
  "location": "job location"
}}"""
            
            extraction_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="Extract job details and return as valid JSON.",
                user_message=extraction_prompt,
                temperature=0.5
            )
            extraction_text = extraction_response.content
            
            try:
                job_data = self._parse_json_object(extraction_text)
            except Exception:
                logger.warning("Job extraction JSON parsing failed; using posting-derived fallback")
                job_data = self._fallback_job_data(job_description)
            
            # OBSERVATION 1
            reasoning += f"👀 OBSERVATION: Extracted job title: {job_data.get('job_title')}\n"
            reasoning += f"👀 OBSERVATION: Company: {job_data.get('company_name')}\n\n"
            
            # THOUGHT 2
            reasoning += "💭 THOUGHT: Should research the company for context\n"
            
            # ACTION 2: Research company
            reasoning += "🔧 ACTION: Searching for company information\n"
            
            company_name = job_data.get('company_name', 'Unknown Company')
            company_search = await self._web_search(f"{company_name} company")
            company_careers = await self._web_search(f"{company_name} careers")
            company_news = await self._web_search(f"{company_name} news")
            
            # OBSERVATION 2
            reasoning += f"👀 OBSERVATION: Found company info: {company_search[:100]}\n"
            reasoning += f"👀 OBSERVATION: Career info: {company_careers[:100]}\n"
            reasoning += f"👀 OBSERVATION: Recent news: {company_news[:100]}\n\n"
            
            # THOUGHT 3
            reasoning += "💭 THOUGHT: Analyze skill requirements\n"
            
            # ACTION 3: Analyze requirements
            reasoning += "🔧 ACTION: Processing technical requirements\n"
            
            skills_prompt = f"""Analyze these job requirements:

Technical Skills: {job_data.get('technical_skills')}

Return JSON:
{{
  "core_skills": [],
  "framework_experience": [],
  "tools_required": [],
  "soft_skills": ["communication", "teamwork", "problem-solving"]
}}"""
            
            skills_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="Analyze job skills requirements.",
                user_message=skills_prompt,
                temperature=0.5
            )
            skills_text = skills_response.content
            
            try:
                skills_data = self._parse_json_object(skills_text)
            except Exception:
                skills_data = {
                    'core_skills': job_data.get('technical_skills', '').split(','),
                    'framework_experience': [],
                    'tools_required': [],
                    'soft_skills': ['Communication', 'Teamwork', 'Problem-solving']
                }
            
            # OBSERVATION 3
            reasoning += f"👀 OBSERVATION: Identified {len(skills_data.get('core_skills', []))} core skills needed\n\n"
            
            # Final output
            self.status = AgentStatus.COMPLETED
            self.execution_time = time.time() - start_time
            self.output = {
                'job_data': {
                    'job_title': job_data.get('job_title', 'Unknown Position'),
                    'company_name': job_data.get('company_name', 'Unknown Company'),
                    'key_requirements': job_data.get('key_requirements', ''),
                    'technical_skills': job_data.get('technical_skills', ''),
                    'experience_level': job_data.get('experience_level', 'mid'),
                    'location': job_data.get('location', 'Remote'),
                    'company_research': {
                        'overview': company_search,
                        'careers': company_careers,
                        'recent_news': company_news
                    },
                    'skill_analysis': skills_data
                }
            }
            
            logger.info(f"✓ job_finder completed in {self.execution_time:.2f}s")
            
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
            logger.error(f"❌ Job Finder error: {str(e)}")
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

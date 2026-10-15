import logging
import json
import re
import time
from typing import Dict, Any
from backend.models import AgentType, AgentPattern, AgentStatus
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResumeTailorAgent(BaseAgent):
    """
    Resume Tailor Agent - Chain-of-Thought Pattern
    Customizes resume to match job requirements
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESUME_TAILOR,
            agent_pattern=AgentPattern.CHAIN_OF_THOUGHT
        )
        logger.info("Resume Tailor Agent initialized with Chain-of-Thought pattern")

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Compatibility wrapper: delegate to `run` implemented below."""
        return await self.run(input_data)

    def _split_skill_text(self, text: str) -> list:
        if not text:
            return []
        parts = re.split(r"[,;\n|]+", text)
        return [part.strip(" -•\t") for part in parts if part.strip(" -•\t")]

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _clean_generated_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
        cleaned = re.sub(r"^(here(?:'s| is)|sure|certainly)[^:\n]*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^based on .*?:\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = cleaned.replace("**", "").replace("__", "")
        cleaned = re.sub(r"^\*+", "", cleaned).strip()
        return cleaned

    def _as_clean_list(self, value: Any, limit: int = 10) -> list:
        if value is None:
            return []
        if isinstance(value, str):
            items = self._split_skill_text(value) or self._extract_bullets(value, limit=limit)
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict):
                    item = item.get('text') or item.get('description') or item.get('name') or ''
                items.append(str(item))
        else:
            items = [str(value)]

        cleaned_items = []
        for item in items:
            cleaned = self._clean_generated_text(str(item)).strip(" -â€¢\t")
            if not cleaned:
                continue
            if cleaned.lower().startswith(("here's", "here is", "note:", "however,")):
                continue
            cleaned_items.append(cleaned)
        return cleaned_items[:limit]

    def _extract_bullets(self, text: str, limit: int = 8) -> list:
        bullets = []
        for line in text.splitlines():
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            if len(cleaned) > 20:
                bullets.append(cleaned)
        if bullets:
            return bullets[:limit]

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 20][:limit]

    def _extract_resume_lines(self, resume_data: str, keywords: list, limit: int = 6) -> list:
        matches = []
        lower_keywords = [keyword.lower() for keyword in keywords if keyword]
        for line in resume_data.splitlines():
            cleaned = line.strip(" -•\t")
            if len(cleaned) < 12:
                continue
            lower_line = cleaned.lower()
            if any(keyword in lower_line for keyword in lower_keywords):
                matches.append(cleaned)
        return matches[:limit]
    
    async def run(self, input_data: Dict[str, Any]) -> Any:
        """
        Tailor resume to job requirements using Chain-of-Thought
        
        Steps:
        1. Extract job requirements
        2. Match resume experience to requirements
        3. Craft professional summary
        4. Optimize skills section
        5. Structure experience section
        6. Perform ATS check
        """
        
        self.status = AgentStatus.RUNNING
        reasoning = ""
        start_time = time.time()
        
        try:
            resume_data = input_data.get('resume_data', '')
            job_data = input_data.get('job_data', {})
            applicant_name = input_data.get('applicant_name', 'Applicant')
            applicant_email = input_data.get('applicant_email', '')
            technical_skills = job_data.get('technical_skills', '')
            if isinstance(technical_skills, list):
                technical_skills_text = ', '.join(technical_skills)
                technical_skills_count = len(technical_skills)
            else:
                technical_skills_text = technical_skills
                technical_skills_count = len([skill for skill in technical_skills.split(',') if skill.strip()])
            
            logger.info(" resume_tailor agent starting (Chain-of-Thought pattern)")
            
            # Step 1: Analyze Requirements
            step1_prompt = f"""Analyze these job requirements and extract key skills needed:

Job Title: {job_data.get('job_title', 'Unknown')}
Company: {job_data.get('company_name', 'Unknown')}
Key Requirements: {job_data.get('key_requirements', '')}
Technical Skills: {technical_skills_text}

Extract as JSON:
{{
  "required_skills": [],
  "required_experience": "",
  "key_focus_areas": []
}}"""
            
            step1_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert resume analyzer. Extract job requirements.",
                user_message=step1_prompt,
                temperature=0.7
            )
            step1_text = step1_response.content
            reasoning += f"STEP 1 - Analyzed Requirements:\n{step1_text}\n\n"
            
            # Step 2: Match Experience
            step2_prompt = f"""Compare this resume to the job requirements and find matching experience:

Resume:
{resume_data}

Required Skills: {technical_skills_text}

Find:
1. Matching skills in resume
2. Relevant experience sections
3. Projects that match requirements

Output as JSON:
{{
  "matching_skills": [],
  "relevant_experience": [],
  "relevant_projects": [],
  "skill_match_percentage": 0
}}"""
            
            step2_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert at matching resume skills to job requirements.",
                user_message=step2_prompt,
                temperature=0.7
            )
            step2_text = step2_response.content
            reasoning += f"STEP 2 - Matched Experience:\n{step2_text}\n\n"
            
            # Step 3: Craft Summary
            step3_prompt = f"""Create a professional summary for this resume tailored to the job:

Job Position: {job_data.get('job_title', 'Software Developer')}
Company: {job_data.get('company_name', 'Company not specified')}
Key Skills Needed: {technical_skills_text}
Original Resume: {resume_data[:500]}

Return JSON only:
{{
  "summary": "2-3 sentence professional summary"
}}

The summary must:
- Highlights relevant experience
- Mentions key skills from job requirements
- Shows enthusiasm for the role
- Is concise and impactful
- Not include introductions like "Here's a summary" """
            
            step3_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert professional resume writer. Write compelling summaries.",
                user_message=step3_prompt,
                temperature=0.8
            )
            step3_text = step3_response.content
            reasoning += f"STEP 3 - Crafted Summary:\n{step3_text}\n\n"
            
            # Step 4: Optimize Skills
            step4_prompt = f"""Reorganize and optimize the skills section of this resume:

Original Resume: {resume_data}
Job Requirements: {technical_skills_text}

Create optimized skills section organized by category:
- Technical Skills (most relevant to job first)
- Tools & Technologies
- Other Relevant Skills

Return JSON only:
{{
  "technical_skills": [],
  "tools_and_technologies": [],
  "other_relevant_skills": []
}}

Only include skills supported by the original resume or directly relevant to the job."""
            
            step4_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert at optimizing resume skills sections for ATS and hiring managers.",
                user_message=step4_prompt,
                temperature=0.7
            )
            step4_text = step4_response.content
            reasoning += f"STEP 4 - Optimized Skills:\n{step4_text}\n\n"
            
            # Step 5: Structure Experience
            step5_prompt = f"""Restructure the experience section to emphasize job-relevant achievements:

Original Resume: {resume_data}
Job Focus: {job_data.get('key_requirements', '')}

For each experience, emphasize:
1. Achievements matching job requirements
2. Technical skills used
3. Impact/results
4. Leadership or team contributions

Return JSON only:
{{
  "experience": [
    {{
      "title": "role/project title from resume",
      "company": "company/organization from resume if available",
      "date": "dates from resume if available",
      "responsibilities": ["achievement bullets tailored to the job"]
    }}
  ],
  "projects": ["project bullets from the resume that are relevant to the job"],
  "education": ["education lines from the resume"]
}}

Do not invent employers, universities, dates, metrics, or projects."""
            
            step5_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert at restructuring experience sections to match job requirements.",
                user_message=step5_prompt,
                temperature=0.7
            )
            step5_text = step5_response.content
            reasoning += f"STEP 5 - Structured Experience:\n{step5_text}\n\n"
            
            # Step 6: ATS Check
            step6_prompt = f"""Check if this tailored resume will pass ATS (Applicant Tracking System):

Tailored Resume Content:
{step3_text}
{step4_text}
{step5_text}

Check for:
1. Keywords from job requirements present
2. Clear formatting and structure
3. Proper spacing and sections
4. No special characters that break ATS

Output JSON:
{{
  "ats_friendly": true/false,
  "missing_keywords": [],
  "recommendations": [],
  "ats_score": 0-10
}}"""
            
            step6_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert at ATS optimization. Check if resume will be read by systems.",
                user_message=step6_prompt,
                temperature=0.5
            )
            step6_text = step6_response.content
            reasoning += f"STEP 6 - ATS Check:\n{step6_text}\n\n"
            
            required_skills = self._split_skill_text(technical_skills_text)
            resume_skill_matches = [
                skill for skill in required_skills
                if skill.lower() in resume_data.lower()
            ]

            try:
                summary_data = self._parse_json_object(step3_text)
                summary_text = self._clean_generated_text(summary_data.get('summary', ''))
            except Exception:
                summary_text = self._clean_generated_text(step3_text)

            try:
                skills_data = self._parse_json_object(step4_text)
            except Exception:
                skills_data = {}

            try:
                experience_data = self._parse_json_object(step5_text)
            except Exception:
                experience_data = {}

            technical_skill_list = self._as_clean_list(skills_data.get('technical_skills'), limit=18)
            tools_skill_list = self._as_clean_list(skills_data.get('tools_and_technologies'), limit=12)
            other_skill_list = self._as_clean_list(skills_data.get('other_relevant_skills'), limit=12)

            experience_entries = experience_data.get('experience', [])
            if not isinstance(experience_entries, list):
                experience_entries = []

            cleaned_experience = []
            for entry in experience_entries:
                if not isinstance(entry, dict):
                    continue
                responsibilities = self._as_clean_list(entry.get('responsibilities'), limit=6)
                title = self._clean_generated_text(str(entry.get('title', 'Relevant Experience')))
                company = self._clean_generated_text(str(entry.get('company', '')))
                date = self._clean_generated_text(str(entry.get('date', '')))
                if responsibilities or title:
                    cleaned_experience.append({
                        'title': title or 'Relevant Experience',
                        'company': company,
                        'date': date,
                        'responsibilities': responsibilities
                    })

            if not cleaned_experience:
                cleaned_experience = [{
                    'title': 'Relevant Experience',
                    'company': '',
                    'date': '',
                    'responsibilities': self._extract_bullets(resume_data, limit=6)
                }]

            project_lines = self._as_clean_list(experience_data.get('projects'), limit=5) or self._extract_resume_lines(
                resume_data,
                ["project", "built", "developed", "created", "implemented"],
                limit=5
            )
            education_lines = self._as_clean_list(experience_data.get('education'), limit=4) or self._extract_resume_lines(
                resume_data,
                ["university", "college", "bachelor", "master", "degree", "gpa"],
                limit=4
            )

            tailored_content = {
                'header': {
                    'name': applicant_name,
                    'email': applicant_email,
                    'phone': '',
                    'location': ''
                },
                'summary': summary_text,
                'skills': {
                    'Job-Matched Skills': resume_skill_matches or required_skills,
                    'Technical Skills': technical_skill_list,
                    'Tools & Technologies': tools_skill_list,
                    'Other Relevant Skills': other_skill_list
                },
                'experience': cleaned_experience,
                'projects': project_lines,
                'education': [
                    {
                        'degree': line,
                        'institution': '',
                        'date': ''
                    }
                    for line in education_lines
                ]
            }
            
            optimization_notes = {
                'skills_matched': len(resume_skill_matches),
                'total_skills': len(required_skills),
                'ats_optimized': True,
                'recommendations': self._extract_bullets(step6_text, limit=5)
            }
            
            self.status = AgentStatus.COMPLETED
            self.execution_time = time.time() - start_time
            self.output = {
                'tailored_content': tailored_content,
                'optimization_notes': optimization_notes
            }
            
            logger.info(f"✓ resume_tailor completed in {self.execution_time:.2f}s")
            
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
            logger.error(f"❌ Resume Tailor error: {str(e)}")
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

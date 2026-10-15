import logging
import json
import re
import time
from typing import Dict, Any
from backend.models import AgentType, AgentPattern, AgentStatus
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """
    Critic Agent - Reflection Pattern
    Reviews and scores the quality of application materials
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CRITIC,
            agent_pattern=AgentPattern.REFLECTION
        )
        self.min_quality_score = 7.0
        logger.info("Critic Agent initialized with Reflection pattern")

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Compatibility wrapper: delegate to `run` implemented below."""
        return await self.run(input_data)

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

    def _number_from_text(self, text: str, default: float) -> float:
        match = re.search(r"\b(?:score|average|rating)\D{0,20}(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"\b(\d+(?:\.\d+)?)\s*/\s*10\b", text)
        if not match:
            return default
        return max(0, min(10, float(match.group(1))))

    def _score_from_dict(self, data: Dict[str, Any], preferred_keys: list, default: float) -> float:
        for key in preferred_keys:
            value = data.get(key)
            if isinstance(value, (int, float)):
                return max(0, min(10, float(value)))

        numeric_values = [
            float(value)
            for value in data.values()
            if isinstance(value, (int, float)) and 0 <= float(value) <= 10
        ]
        if numeric_values:
            return sum(numeric_values) / len(numeric_values)
        return default

    def _parse_improvements(self, text: str, job_data: Dict[str, Any]) -> list:
        improvements = []
        seen = set()
        for line in text.splitlines():
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            lowered = cleaned.lower()
            if not cleaned or lowered.startswith(("based on", "here are", "top 5", "improvements:", "suggestions:")):
                continue
            if lowered in seen:
                continue
            if 12 <= len(cleaned) <= 180:
                seen.add(lowered)
                improvements.append(cleaned)

        if improvements:
            return improvements[:5]

        skills = job_data.get('technical_skills', '')
        role = job_data.get('job_title', 'the target role')
        return [
            f"Add evidence from the resume that directly supports {role}",
            f"Make the strongest matching skills more visible: {skills}" if skills else "Make the strongest matching skills more visible",
            "Add truthful metrics only where the original resume supports them",
            "Tighten the cover letter around the company and role requirements",
            "Remove generic claims and replace them with resume-specific achievements"
        ]
    
    async def run(self, input_data: Dict[str, Any]) -> Any:
        """
        Review and score application materials using Reflection pattern
        
        Phases:
        1. Review resume quality
        2. Check ATS compatibility  
        3. Analyze job alignment
        4. Review cover letter
        5. Calculate scores
        6. Provide improvements
        """
        
        self.status = AgentStatus.RUNNING
        reasoning = ""
        start_time = time.time()
        
        try:
            job_data = input_data.get('job_data', {})
            tailored_content = input_data.get('tailored_content', {})
            cover_letter_content = input_data.get('cover_letter_content', {})
            
            logger.info(" critic agent starting (Reflection pattern)")
            
            # Phase 1: Resume Review
            reasoning += " PHASE 1: Reviewing Resume Quality\n"
            
            resume_prompt = f"""Review this resume section:

Summary: {tailored_content.get('summary', '')}
Skills: {tailored_content.get('skills', '')}

Score on:
1. Clarity (1-10)
2. Relevance (1-10)
3. Impact (1-10)
4. Professionalism (1-10)

Return JSON with scores and feedback."""
            
            resume_review = await self.llm_service.generate_with_system_prompt(
                system_prompt="You are expert resume reviewer. Provide constructive feedback.",
                user_message=resume_prompt,
                temperature=0.5
            )
            resume_review_text = resume_review.content
            
            try:
                resume_scores = self._parse_json_object(resume_review_text)
            except Exception:
                resume_scores = {
                    'clarity': self._number_from_text(resume_review_text, 7),
                    'relevance': self._number_from_text(resume_review_text, 7),
                    'impact': self._number_from_text(resume_review_text, 7),
                    'professionalism': self._number_from_text(resume_review_text, 7),
                    'average': self._number_from_text(resume_review_text, 7)
                }
            
            reasoning += f"Resume Score: {resume_scores.get('average', 7.5)}/10\n\n"
            
            # Phase 2: ATS Check
            reasoning += "🤖 PHASE 2: ATS Compatibility Check\n"
            
            ats_prompt = f"""Check if resume passes ATS:

Resume Content:
{tailored_content.get('summary', '')}

Check for:
1. Keywords from job: {job_data.get('technical_skills', '')}
2. Clear formatting
3. Standard sections
4. No special characters

Return JSON with ATS score (1-10) and issues found."""
            
            ats_check = await self.llm_service.generate_with_system_prompt(
                system_prompt="Check ATS compatibility. Return JSON.",
                user_message=ats_prompt,
                temperature=0.5
            )
            ats_check_text = ats_check.content
            
            try:
                ats_scores = self._parse_json_object(ats_check_text)
            except Exception:
                ats_scores = {
                    'ats_score': self._number_from_text(ats_check_text, 7),
                    'issues': []
                }
            
            reasoning += f"ATS Score: {ats_scores.get('ats_score', 7)}/10\n\n"
            
            # Phase 3: Job Alignment
            reasoning += "🎯 PHASE 3: Job Alignment Analysis\n"
            
            alignment_prompt = f"""Analyze alignment between resume and job:

Job Title: {job_data.get('job_title', 'Unknown')}
Job Requirements: {job_data.get('key_requirements', '')}
Resume Summary: {tailored_content.get('summary', '')}

Score alignment (1-10) and identify gaps."""
            
            alignment_check = await self.llm_service.generate_with_system_prompt(
                system_prompt="Analyze resume-job alignment.",
                user_message=alignment_prompt,
                temperature=0.5
            )
            alignment_check_text = alignment_check.content
            
            try:
                alignment_scores = self._parse_json_object(alignment_check_text)
            except Exception:
                alignment_scores = {
                    'alignment_score': self._number_from_text(alignment_check_text, 7),
                    'gaps': []
                }
            
            reasoning += f"Alignment Score: {alignment_scores.get('alignment_score', 7)}/10\n\n"
            
            # Phase 4: Cover Letter Review
            reasoning += "✉️ PHASE 4: Cover Letter Review\n"
            
            letter_prompt = f"""Review this cover letter:

{str(cover_letter_content)}

Score on:
1. Personalization (1-10)
2. Company Knowledge (1-10)
3. Impact (1-10)
4. Professionalism (1-10)

Return JSON only:
{{
  "personalization": 0,
  "company_knowledge": 0,
  "impact": 0,
  "professionalism": 0,
  "average": 0,
  "feedback": ""
}}"""
            
            letter_review = await self.llm_service.generate_with_system_prompt(
                system_prompt="Review cover letter quality.",
                user_message=letter_prompt,
                temperature=0.5
            )
            letter_review_text = letter_review.content
            
            try:
                letter_scores = self._parse_json_object(letter_review_text)
            except Exception:
                letter_scores = {
                    'personalization': self._number_from_text(letter_review_text, 7),
                    'company_knowledge': self._number_from_text(letter_review_text, 7),
                    'impact': self._number_from_text(letter_review_text, 7),
                    'professionalism': self._number_from_text(letter_review_text, 7),
                    'average': self._number_from_text(letter_review_text, 7)
                }
            
            reasoning += f"Cover Letter Score: {letter_scores.get('average', 7)}/10\n\n"
            
            # Phase 5: Calculate Overall Score
            reasoning += "📊 PHASE 5: Calculating Overall Score\n"
            
            resume_avg = self._score_from_dict(resume_scores, ['average', 'resume_score', 'score'], 7)
            ats_score = self._score_from_dict(ats_scores, ['ats_score', 'score'], 7)
            alignment_score = self._score_from_dict(alignment_scores, ['alignment_score', 'score'], 7)
            letter_avg = self._score_from_dict(letter_scores, ['average', 'cover_letter_score', 'score'], 7)
            
            overall_score = (
                (resume_avg * 0.35) +
                (letter_avg * 0.25) +
                (ats_score * 0.20) +
                (alignment_score * 0.20)
            )
            
            reasoning += f"Overall Score Calculation:\n"
            reasoning += f"  Resume (35%): {resume_avg} → {resume_avg * 0.35}\n"
            reasoning += f"  Letter (25%): {letter_avg} → {letter_avg * 0.25}\n"
            reasoning += f"  ATS (20%): {ats_score} → {ats_score * 0.20}\n"
            reasoning += f"  Alignment (20%): {alignment_score} → {alignment_score * 0.20}\n"
            reasoning += f"OVERALL: {overall_score}/10\n\n"
            
            # Phase 6: Decision & Improvements
            reasoning += "DECISION PHASE: Recommendations\n"
            
            if overall_score >= self.min_quality_score:
                decision = "APPROVED"
                ready = True
                reasoning += "✅ Application is ready for submission\n"
            else:
                decision = "NEEDS_IMPROVEMENT"
                ready = False
                reasoning += "⚠️ Application needs improvements before submission\n"
            
            improvements_prompt = f"""Based on scores:
- Resume: {resume_avg}/10
- Letter: {letter_avg}/10
- ATS: {ats_score}/10
- Alignment: {alignment_score}/10

Job Title: {job_data.get('job_title', '')}
Company: {job_data.get('company_name', '')}
Job Requirements: {job_data.get('key_requirements', '')}
Resume Summary: {tailored_content.get('summary', '')}
Cover Letter: {str(cover_letter_content)[:1200]}

List exactly 5 specific improvements for this application.
Return only the 5 improvement lines. Do not include an introduction or repeat the question."""
            
            improvements_response = await self.llm_service.generate_with_system_prompt(
                system_prompt="Provide specific, actionable improvements.",
                user_message=improvements_prompt,
                temperature=0.7
            )
            
            improvements = self._parse_improvements(improvements_response.content, job_data)
            
            self.status = AgentStatus.COMPLETED
            self.execution_time = time.time() - start_time
            self.output = {
                'overall_score': round(overall_score, 1),
                'decision': decision,
                'ready_for_submission': ready,
                'component_scores': {
                    'resume': round(resume_avg, 1),
                    'cover_letter': round(letter_avg, 1),
                    'ats_compatibility': round(ats_score, 1),
                    'job_alignment': round(alignment_score, 1)
                },
                'resume_review': resume_review_text[:200],
                'letter_review': letter_review_text[:200],
                'ats_check': ats_check_text[:200],
                'alignment_analysis': alignment_check_text[:200],
                'improvements': improvements
            }
            
            logger.info(f"✓ critic completed in {self.execution_time:.2f}s")
            
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
            logger.error(f"❌ Critic error: {str(e)}")
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

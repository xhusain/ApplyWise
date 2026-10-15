"""Agents package - Specialist AI Agents"""

# From Block 1
from .base_agent import BaseAgent, ToolUseAgent

# From Block 3
from .job_finder import JobFinderAgent
from .resume_tailor import ResumeTailorAgent
from .cover_letter import CoverLetterAgent
from .critic import CriticAgent

__all__ = [
    # Block 1
    "BaseAgent",
    "ToolUseAgent",
    # Block 3
    "JobFinderAgent",
    "ResumeTailorAgent",
    "CoverLetterAgent",
    "CriticAgent",
]
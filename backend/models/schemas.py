"""
Pydantic Models for Type Safety and Validation
Defines all data structures used across the application
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of specialist agents"""
    JOB_FINDER = "job_finder"
    RESUME_TAILOR = "resume_tailor"
    COVER_LETTER = "cover_letter"
    CRITIC = "critic"


class AgentPattern(str, Enum):
    """Design patterns implemented by agents"""
    REACT = "ReAct"
    CHAIN_OF_THOUGHT = "Chain-of-Thought"
    TOOL_USE = "Tool Use"
    REFLECTION = "Reflection"


class AgentStatus(str, Enum):
    """Processing status of agents"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentOutput(BaseModel):
    """Output from a specialist agent"""
    agent_type: AgentType
    agent_pattern: AgentPattern
    status: AgentStatus
    reasoning: str = Field(description="Agent's thought process")
    output: Dict[str, Any] = Field(description="Structured output")
    execution_time: float = Field(description="Time taken in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)


class JobDescription(BaseModel):
    """Structured job description"""
    raw_text: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    requirements: List[str] = []
    responsibilities: List[str] = []
    skills_required: List[str] = []
    experience_level: Optional[str] = None


class ResumeData(BaseModel):
    """Parsed resume data"""
    raw_text: str
    file_name: str
    file_type: str  # 'pdf' or 'docx'
    extracted_sections: Dict[str, str] = {}


class ApplicationPackage(BaseModel):
    """Final application package output"""
    job_id: str = Field(description="Unique identifier for this job application")
    job_description: JobDescription
    agent_outputs: List[AgentOutput] = []
    tailored_resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    status: str = "processing"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class JobApplicationRequest(BaseModel):
    """Request model for job application endpoint"""
    job_description: str = Field(min_length=50, description="Job posting text")
    # resume file will be uploaded separately


class LLMMessage(BaseModel):
    """Message format for LLM communication"""
    role: str = Field(description="user, assistant, or system")
    content: str


class LLMResponse(BaseModel):
    """Structured LLM response"""
    content: str
    model: str
    usage: Dict[str, int]
    reasoning_tokens: Optional[int] = None

"""
Document Service
Generates professional DOCX documents for resumes and cover letters
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Custom exception for document generation errors"""
    pass


class DocumentService:
    """
    Generates professional Word documents
    Handles resume and cover letter formatting
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Document Service initialized: {self.output_dir}")

    def _has_content(self, value: Any) -> bool:
        """Return True when a value has meaningful printable content."""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set)):
            return any(self._has_content(item) for item in value)
        if isinstance(value, dict):
            return any(self._has_content(item) for item in value.values())
        return True
    
    def generate_resume(
        self,
        content: Dict[str, Any],
        job_id: str,
        applicant_name: str = "Applicant",
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate a tailored resume DOCX file
        
        Args:
            content: Resume content dictionary with sections
            job_id: Unique identifier for this job application
            applicant_name: Name for the filename
            
        Returns:
            Path to the generated DOCX file
        """
        try:
            logger.info(f"Generating resume for job_id: {job_id}")
            
            doc = Document()
            
            # Set document margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.75)
                section.right_margin = Inches(0.75)
            
            # Header: Name and Contact
            if 'header' in content:
                self._add_resume_header(doc, content['header'])
            
            # Professional Summary
            if self._has_content(content.get('summary')):
                self._add_section(doc, "PROFESSIONAL SUMMARY", content['summary'])
            
            # Experience
            if self._has_content(content.get('experience')):
                self._add_experience_section(doc, content['experience'])
            
            # Education
            if self._has_content(content.get('education')):
                self._add_education_section(doc, content['education'])
            
            # Skills
            if self._has_content(content.get('skills')):
                self._add_skills_section(doc, content['skills'])
            
            # Projects
            if self._has_content(content.get('projects')):
                self._add_projects_section(doc, content['projects'])
            
            # Certifications
            if self._has_content(content.get('certifications')):
                self._add_section(doc, "CERTIFICATIONS", content['certifications'])
            
            # Save document
            filename = f"Resume_{applicant_name.replace(' ', '_')}_{job_id}.docx"
            target_dir = Path(output_dir) if output_dir else self.output_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            filepath = target_dir / filename
            doc.save(str(filepath))
            
            logger.info(f"✓ Resume generated: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Resume generation failed: {str(e)}")
            raise DocumentServiceError(f"Failed to generate resume: {str(e)}")
    
    def generate_cover_letter(
        self,
        content: Dict[str, Any],
        job_id: str,
        applicant_name: str = "Applicant",
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate a professional cover letter DOCX file
        
        Args:
            content: Cover letter content dictionary
            job_id: Unique identifier for this job application
            applicant_name: Name for the filename
            
        Returns:
            Path to the generated DOCX file
        """
        try:
            logger.info(f"Generating cover letter for job_id: {job_id}")
            
            doc = Document()
            
            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
            
            # Contact information
            if 'contact' in content:
                contact_lines = content['contact'].values() if isinstance(content['contact'], dict) else content['contact']
                for line in contact_lines:
                    if not self._has_content(line):
                        continue
                    p = doc.add_paragraph(line)
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                doc.add_paragraph()  # Blank line
            
            # Date
            date_str = content.get('date', datetime.now().strftime("%B %d, %Y"))
            doc.add_paragraph(date_str)
            doc.add_paragraph()  # Blank line
            
            # Recipient information
            if 'recipient' in content:
                recipient_lines = content['recipient'].values() if isinstance(content['recipient'], dict) else content['recipient']
                for line in recipient_lines:
                    if not self._has_content(line):
                        continue
                    doc.add_paragraph(line)
                doc.add_paragraph()  # Blank line
            
            # Salutation
            salutation = content.get('salutation', "Dear Hiring Manager,")
            p = doc.add_paragraph(salutation)
            p.runs[0].bold = True
            doc.add_paragraph()  # Blank line
            
            # Body paragraphs
            if 'body' in content:
                if isinstance(content['body'], list):
                    for paragraph_text in content['body']:
                        if not self._has_content(paragraph_text):
                            continue
                        doc.add_paragraph(paragraph_text)
                        doc.add_paragraph()  # Blank line between paragraphs
                else:
                    doc.add_paragraph(content['body'])
                    doc.add_paragraph()
            
            # Closing
            closing = content.get('closing', "Sincerely,")
            doc.add_paragraph(closing)
            doc.add_paragraph()
            
            # Signature
            signature = content.get('signature', applicant_name)
            p = doc.add_paragraph(signature)
            p.runs[0].bold = True
            
            # Save document
            filename = f"CoverLetter_{applicant_name.replace(' ', '_')}_{job_id}.docx"
            target_dir = Path(output_dir) if output_dir else self.output_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            filepath = target_dir / filename
            doc.save(str(filepath))
            
            logger.info(f"✓ Cover letter generated: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Cover letter generation failed: {str(e)}")
            raise DocumentServiceError(f"Failed to generate cover letter: {str(e)}")
    
    def _add_resume_header(self, doc: Document, header: Dict[str, Any]):
        """Add formatted header with name and contact info"""
        # Name (centered, large, bold)
        name = header.get('name', 'Name Not Provided')
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(name)
        run.bold = True
        run.font.size = Pt(18)
        
        # Contact info (centered, smaller)
        contact_parts = []
        if self._has_content(header.get('email')):
            contact_parts.append(header['email'])
        if self._has_content(header.get('phone')):
            contact_parts.append(header['phone'])
        if self._has_content(header.get('location')):
            contact_parts.append(header['location'])
        if self._has_content(header.get('linkedin')):
            contact_parts.append(header['linkedin'])
        
        if contact_parts:
            p = doc.add_paragraph(' | '.join(contact_parts))
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(10)
        
        doc.add_paragraph()  # Blank line
    
    def _add_section(self, doc: Document, title: str, content: str):
        """Add a simple text section"""
        if not self._has_content(content):
            return
        # Section title
        p = doc.add_paragraph(title)
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = RGBColor(0, 51, 102)
        
        # Add bottom border to title
        p.paragraph_format.space_after = Pt(6)
        
        # Content
        doc.add_paragraph(content)
        doc.add_paragraph()  # Blank line
    
    def _add_experience_section(self, doc: Document, experiences: List[Dict[str, Any]]):
        """Add work experience section with structured entries"""
        if isinstance(experiences, str):
            self._add_section(doc, "EXPERIENCE", experiences)
            return
        # Section title
        p = doc.add_paragraph("EXPERIENCE")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = RGBColor(0, 51, 102)
        p.paragraph_format.space_after = Pt(6)
        
        # Add each experience
        for exp in experiences:
            if not self._has_content(exp):
                continue
            # Job title and company
            p = doc.add_paragraph()
            title_run = p.add_run(exp.get('title', 'Position'))
            title_run.bold = True
            
            if self._has_content(exp.get('company')):
                p.add_run(f" | {exp['company']}")
            
            # Date and location
            if 'date' in exp or 'location' in exp:
                date_parts = []
                if self._has_content(exp.get('date')):
                    date_parts.append(exp['date'])
                if self._has_content(exp.get('location')):
                    date_parts.append(exp['location'])
                if date_parts:
                    p2 = doc.add_paragraph(' | '.join(date_parts))
                    if p2.runs:
                        p2.runs[0].italic = True
                        p2.runs[0].font.size = Pt(10)
            
            # Responsibilities/achievements
            if self._has_content(exp.get('responsibilities')):
                for resp in exp['responsibilities']:
                    if not self._has_content(resp):
                        continue
                    doc.add_paragraph(resp, style='List Bullet')
            
            doc.add_paragraph()  # Blank line between entries
    
    def _add_education_section(self, doc: Document, education: List[Dict[str, Any]]):
        """Add education section"""
        # Section title
        p = doc.add_paragraph("EDUCATION")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = RGBColor(0, 51, 102)
        p.paragraph_format.space_after = Pt(6)
        
        for edu in education:
            if not self._has_content(edu):
                continue
            # Degree and institution
            p = doc.add_paragraph()
            degree_run = p.add_run(edu.get('degree', 'Degree'))
            degree_run.bold = True
            
            if self._has_content(edu.get('institution')):
                p.add_run(f" | {edu['institution']}")
            
            # Date and GPA
            if 'date' in edu or 'gpa' in edu:
                detail_parts = []
                if self._has_content(edu.get('date')):
                    detail_parts.append(edu['date'])
                if self._has_content(edu.get('gpa')):
                    detail_parts.append(f"GPA: {edu['gpa']}")
                if detail_parts:
                    p2 = doc.add_paragraph(' | '.join(detail_parts))
                    if p2.runs:
                        p2.runs[0].italic = True
                        p2.runs[0].font.size = Pt(10)
            
            doc.add_paragraph()  # Blank line
    
    def _add_skills_section(self, doc: Document, skills: Dict[str, List[str]]):
        """Add skills section with categories"""
        if isinstance(skills, str):
            self._add_section(doc, "SKILLS", skills)
            return
        # Section title
        p = doc.add_paragraph("SKILLS")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = RGBColor(0, 51, 102)
        p.paragraph_format.space_after = Pt(6)
        
        for category, skill_list in skills.items():
            if not self._has_content(skill_list):
                continue
            p = doc.add_paragraph()
            category_run = p.add_run(f"{category}: ")
            category_run.bold = True
            if isinstance(skill_list, str):
                p.add_run(skill_list)
            else:
                p.add_run(', '.join(skill_list))
        
        doc.add_paragraph()  # Blank line
    
    def _add_projects_section(self, doc: Document, projects: List[Dict[str, Any]]):
        """Add projects section"""
        if isinstance(projects, str):
            self._add_section(doc, "PROJECTS", projects)
            return
        # Section title
        p = doc.add_paragraph("PROJECTS")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = RGBColor(0, 51, 102)
        p.paragraph_format.space_after = Pt(6)
        
        for project in projects:
            if not self._has_content(project):
                continue
            if isinstance(project, str):
                doc.add_paragraph(project, style='List Bullet')
                continue
            # Project name
            p = doc.add_paragraph()
            name_run = p.add_run(project.get('name', 'Project'))
            name_run.bold = True
            
            if self._has_content(project.get('date')):
                p.add_run(f" | {project['date']}")
            
            # Description
            if self._has_content(project.get('description')):
                doc.add_paragraph(project['description'])
            
            # Technologies
            if self._has_content(project.get('technologies')):
                p2 = doc.add_paragraph(f"Technologies: {', '.join(project['technologies'])}")
                if p2.runs:
                    p2.runs[0].italic = True
                    p2.runs[0].font.size = Pt(10)
            
            doc.add_paragraph()  # Blank line


if __name__ == "__main__":
    """Test document generation"""
    print("\n🧪 Testing Document Service...\n")
    
    service = DocumentService(output_dir="./test_outputs")
    
    # Test resume generation
    resume_content = {
        'header': {
            'name': 'John Doe',
            'email': 'john.doe@email.com',
            'phone': '(123) 456-7890',
            'location': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/johndoe'
        },
        'summary': 'Experienced software engineer with 5+ years in full-stack development.',
        'experience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'date': 'Jan 2020 - Present',
                'location': 'San Francisco, CA',
                'responsibilities': [
                    'Led development of microservices architecture',
                    'Mentored junior developers',
                    'Improved system performance by 40%'
                ]
            }
        ],
        'education': [
            {
                'degree': 'B.S. Computer Science',
                'institution': 'University of California',
                'date': '2015 - 2019',
                'gpa': '3.8'
            }
        ],
        'skills': {
            'Programming': ['Python', 'JavaScript', 'Go'],
            'Frameworks': ['React', 'FastAPI', 'Node.js'],
            'Tools': ['Docker', 'AWS', 'Git']
        }
    }
    
    resume_path = service.generate_resume(resume_content, 'test_001', 'John_Doe')
    print(f"✓ Resume generated: {resume_path}")
    
    # Test cover letter generation
    cover_letter_content = {
        'contact': [
            'John Doe',
            'john.doe@email.com',
            '(123) 456-7890',
            'San Francisco, CA'
        ],
        'recipient': [
            'Hiring Manager',
            'Tech Company Inc.',
            '123 Tech Street',
            'San Francisco, CA 94105'
        ],
        'salutation': 'Dear Hiring Manager,',
        'body': [
            'I am writing to express my strong interest in the Senior Software Engineer position at Tech Company Inc.',
            'With over 5 years of experience in full-stack development, I believe I would be an excellent fit for your team.',
            'I look forward to discussing how my skills and experience can contribute to your organization.'
        ],
        'closing': 'Sincerely,',
        'signature': 'John Doe'
    }
    
    cover_letter_path = service.generate_cover_letter(cover_letter_content, 'test_001', 'John_Doe')
    print(f"✓ Cover letter generated: {cover_letter_path}")
    
    print("\n✅ Document Service test completed!")

"""
Resume Parser
Extracts text content from PDF and DOCX resume files
"""

import PyPDF2
from docx import Document
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ResumeParserError(Exception):
    """Custom exception for resume parsing errors"""
    pass


class ResumeParser:
    """
    Parses resume files (PDF, DOCX) and extracts text content
    Handles multiple file formats and provides structured output
    """
    
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc']
    
    def __init__(self):
        logger.info("Resume Parser initialized")
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a resume file and extract all text content
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing:
                - raw_text: Full extracted text
                - file_name: Name of the file
                - file_type: Extension (pdf/docx)
                - word_count: Number of words
                - char_count: Number of characters
                
        Raises:
            ResumeParserError: If parsing fails
        """
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise ResumeParserError(f"File not found: {file_path}")
        
        # Validate file extension
        file_ext = file_path.suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ResumeParserError(
                f"Unsupported file format: {file_ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"Parsing resume: {file_path.name}")
        
        # Parse based on file type
        try:
            if file_ext == '.pdf':
                text = self._parse_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                text = self._parse_docx(file_path)
            else:
                raise ResumeParserError(f"Unsupported format: {file_ext}")
            
            # Validate extracted text
            if not text or len(text.strip()) < 50:
                raise ResumeParserError(
                    "Extracted text is too short. File may be corrupted or empty."
                )
            
            # Build result
            result = {
                'raw_text': text.strip(),
                'file_name': file_path.name,
                'file_type': file_ext[1:],  # Remove the dot
                'word_count': len(text.split()),
                'char_count': len(text),
                'sections': self._extract_sections(text)
            }
            
            logger.info(
                f"✓ Parsed {file_path.name}: "
                f"{result['word_count']} words, "
                f"{result['char_count']} characters"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path.name}: {str(e)}")
            raise ResumeParserError(f"Parsing failed: {str(e)}")
    
    def _parse_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            text_parts = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    logger.debug(f"Extracted page {page_num + 1}")
            
            full_text = '\n\n'.join(text_parts)
            return full_text
            
        except Exception as e:
            raise ResumeParserError(f"PDF parsing error: {str(e)}")
    
    def _parse_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            
            # Extract text from paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            
            # Extract text from tables
            table_texts = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        table_texts.append(row_text)
            
            # Combine all text
            all_text = '\n'.join(paragraphs)
            if table_texts:
                all_text += '\n\nTables:\n' + '\n'.join(table_texts)
            
            return all_text
            
        except Exception as e:
            raise ResumeParserError(f"DOCX parsing error: {str(e)}")
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to identify common resume sections
        
        Args:
            text: Full resume text
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        
        # Common section headers
        section_keywords = {
            'education': ['education', 'academic', 'university', 'degree'],
            'experience': ['experience', 'employment', 'work history', 'professional'],
            'skills': ['skills', 'technical skills', 'competencies'],
            'projects': ['projects', 'portfolio'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'summary': ['summary', 'objective', 'profile'],
        }
        
        text_lower = text.lower()
        lines = text.split('\n')
        
        # Simple keyword-based section detection
        for section_name, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    sections[section_name] = f"Contains '{keyword}' section"
                    break
        
        return sections
    
    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract contact information from resume text
        (Basic implementation - can be enhanced with regex)
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary with email, phone, linkedin, etc.
        """
        import re
        
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group(0)
        
        # Phone pattern (simple)
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group(0)
        
        # LinkedIn
        if 'linkedin.com' in text.lower():
            linkedin_pattern = r'linkedin\.com/in/[\w-]+'
            linkedin_match = re.search(linkedin_pattern, text.lower())
            if linkedin_match:
                contact_info['linkedin'] = linkedin_match.group(0)
        
        # GitHub
        if 'github.com' in text.lower():
            github_pattern = r'github\.com/[\w-]+'
            github_match = re.search(github_pattern, text.lower())
            if github_match:
                contact_info['github'] = github_match.group(0)
        
        return contact_info


if __name__ == "__main__":
    """Test the resume parser"""
    import sys
    
    print("\n🧪 Testing Resume Parser...\n")
    
    parser = ResumeParser()
    
    # Test with a sample file if provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            result = parser.parse_file(file_path)
            print(f"✓ File: {result['file_name']}")
            print(f"✓ Type: {result['file_type']}")
            print(f"✓ Words: {result['word_count']}")
            print(f"✓ Characters: {result['char_count']}")
            print(f"✓ Sections found: {', '.join(result['sections'].keys())}")
            print(f"\n✓ Preview (first 200 chars):")
            print(result['raw_text'][:200] + "...")
            
            # Test contact extraction
            contact = parser.extract_contact_info(result['raw_text'])
            print(f"\n✓ Contact Info:")
            for key, value in contact.items():
                if value:
                    print(f"  - {key}: {value}")
            
        except ResumeParserError as e:
            print(f"✗ Error: {e}")
    else:
        print("Usage: python resume_parser.py <path_to_resume.pdf|docx>")
        print("\n✓ Resume Parser module ready!")

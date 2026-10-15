"""
Storage Service
Manages file uploads, temporary storage, and output files
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageServiceError(Exception):
    """Custom exception for storage service errors"""
    pass


class StorageService:
    """
    Handles file storage operations
    Manages uploads, outputs, and temporary files
    """
    
    def __init__(self, upload_dir: str = "./uploads", output_dir: str = "./outputs"):
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storage Service initialized")
        logger.info(f"  Upload dir: {self.upload_dir}")
        logger.info(f"  Output dir: {self.output_dir}")
    
    def generate_job_id(self) -> str:
        """
        Generate unique job application ID
        
        Returns:
            Unique identifier (timestamp + short UUID)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        job_id = f"{timestamp}_{short_uuid}"
        logger.info(f"Generated job_id: {job_id}")
        return job_id
    
    def save_upload(self, file_data: bytes, original_filename: str, job_id: str) -> str:
        """
        Save uploaded file to upload directory
        
        Args:
            file_data: Binary file content
            original_filename: Original name of the file
            job_id: Unique job application identifier
            
        Returns:
            Path to saved file
        """
        try:
            # Create job-specific subdirectory
            job_upload_dir = self.upload_dir / job_id
            job_upload_dir.mkdir(exist_ok=True)
            
            # Sanitize filename
            safe_filename = self._sanitize_filename(original_filename)
            
            # Save file
            file_path = job_upload_dir / safe_filename
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"✓ Saved upload: {safe_filename} ({len(file_data)} bytes)")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save upload: {str(e)}")
            raise StorageServiceError(f"Upload save failed: {str(e)}")
    
    def get_output_path(self, job_id: str, filename: str) -> str:
        """
        Get path for an output file
        
        Args:
            job_id: Job application identifier
            filename: Name of output file
            
        Returns:
            Full path for the output file
        """
        # Create job-specific output subdirectory
        job_output_dir = self.output_dir / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        safe_filename = self._sanitize_filename(filename)
        return str(job_output_dir / safe_filename)
    
    def list_job_outputs(self, job_id: str) -> List[str]:
        """
        List all output files for a specific job
        
        Args:
            job_id: Job application identifier
            
        Returns:
            List of file paths
        """
        job_output_dir = self.output_dir / job_id
        
        if not job_output_dir.exists():
            return []
        
        files = [
            str(f) for f in job_output_dir.iterdir() 
            if f.is_file()
        ]
        
        return files
    
    def cleanup_job(self, job_id: str) -> None:
        """
        Remove all files associated with a job
        
        Args:
            job_id: Job application identifier
        """
        try:
            # Remove upload directory
            job_upload_dir = self.upload_dir / job_id
            if job_upload_dir.exists():
                shutil.rmtree(job_upload_dir)
                logger.info(f"Cleaned up uploads for job {job_id}")
            
            # Remove output directory
            job_output_dir = self.output_dir / job_id
            if job_output_dir.exists():
                shutil.rmtree(job_output_dir)
                logger.info(f"Cleaned up outputs for job {job_id}")
                
        except Exception as e:
            logger.warning(f"Cleanup failed for job {job_id}: {str(e)}")
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise StorageServiceError(f"File not found: {file_path}")
        
        stat = path.stat()
        
        return {
            'name': path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': path.suffix,
            'absolute_path': str(path.absolute())
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove potentially dangerous characters from filename
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace spaces and special characters
        filename = filename.replace(' ', '_')
        
        # Remove any remaining problematic characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        filename = ''.join(c if c in safe_chars else '_' for c in filename)
        
        return filename
    
    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✓ All storage directories ensured")


if __name__ == "__main__":
    """Test storage service"""
    print("\n🧪 Testing Storage Service...\n")
    
    service = StorageService(upload_dir="./test_uploads", output_dir="./test_outputs")
    
    # Test 1: Generate job ID
    job_id = service.generate_job_id()
    print(f"✓ Generated job_id: {job_id}")
    
    # Test 2: Save a test file
    test_data = b"This is test resume content"
    upload_path = service.save_upload(test_data, "test_resume.pdf", job_id)
    print(f"✓ Saved test upload: {upload_path}")
    
    # Test 3: Get file info
    info = service.get_file_info(upload_path)
    print(f"✓ File info: {info['name']} ({info['size']} bytes)")
    
    # Test 4: Get output path
    output_path = service.get_output_path(job_id, "tailored_resume.docx")
    print(f"✓ Output path: {output_path}")
    
    # Test 5: List outputs
    outputs = service.list_job_outputs(job_id)
    print(f"✓ Outputs found: {len(outputs)}")
    
    # Test 6: Cleanup
    service.cleanup_job(job_id)
    print(f"✓ Cleaned up job {job_id}")
    
    print("\n✅ Storage Service test completed!")

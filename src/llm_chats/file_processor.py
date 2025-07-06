"""File processing module for extracting content from PDF and image files."""
import logging
import os
import tempfile
import mimetypes
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import base64
import hashlib

# File processing imports
try:
    import PyPDF2
    from PIL import Image
    import pytesseract
    import magic
    import pdfplumber
except ImportError as e:
    logging.error(f"Missing required dependency: {e}")
    raise

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass


class FileProcessor:
    """Handles file processing for PDF and image content extraction."""
    
    # Supported file types
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp'
    }
    
    # These will be overridden by config values
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_PDF_PAGES = 100
    MAX_IMAGE_SIZE = (4096, 4096)  # Max image dimensions
    
    def __init__(self):
        """Initialize file processor with configuration."""
        from .config import get_file_processing_config
        self.config = get_file_processing_config()
        self.temp_dir = tempfile.mkdtemp(prefix="llm_chats_")
        logger.info(f"File processor initialized with temp dir: {self.temp_dir}")
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file before processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dict containing file metadata
            
        Raises:
            FileProcessingError: If file validation fails
        """
        try:
            if not os.path.exists(file_path):
                raise FileProcessingError(f"File not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                raise FileProcessingError(f"File too large: {file_size} bytes (max: {self.config.max_file_size})")
            
            # Detect MIME type
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type not in self.SUPPORTED_MIME_TYPES:
                raise FileProcessingError(f"Unsupported file type: {mime_type}")
            
            # Get file hash for deduplication
            file_hash = self._get_file_hash(file_path)
            
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': file_size,
                'mime_type': mime_type,
                'hash': file_hash
            }
            
            logger.info(f"File validation passed: {file_info['name']} ({file_info['mime_type']})")
            return file_info
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            raise FileProcessingError(f"File validation failed: {str(e)}")
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process file and extract content.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dict containing extracted content and metadata
        """
        try:
            # Validate file first
            file_info = self.validate_file(file_path)
            
            # Extract content based on file type
            if file_info['mime_type'] == 'application/pdf':
                content = self._extract_pdf_content(file_path)
            elif file_info['mime_type'].startswith('image/'):
                content = self._extract_image_content(file_path)
            else:
                raise FileProcessingError(f"Unsupported file type: {file_info['mime_type']}")
            
            # Create result
            result = {
                'file_info': file_info,
                'content': content,
                'word_count': len(content.split()) if content else 0,
                'processing_status': 'success'
            }
            
            logger.info(f"File processed successfully: {file_info['name']} ({result['word_count']} words)")
            return result
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            return {
                'file_info': file_info if 'file_info' in locals() else {'name': os.path.basename(file_path)},
                'content': '',
                'word_count': 0,
                'processing_status': 'failed',
                'error': str(e)
            }
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            content_parts = []
            
            # First try with pdfplumber (better for complex layouts)
            try:
                with pdfplumber.open(file_path) as pdf:
                    if len(pdf.pages) > self.config.max_pdf_pages:
                        logger.warning(f"PDF has {len(pdf.pages)} pages, processing only first {self.config.max_pdf_pages}")
                        pages_to_process = pdf.pages[:self.config.max_pdf_pages]
                    else:
                        pages_to_process = pdf.pages
                    
                    for page_num, page in enumerate(pages_to_process, 1):
                        try:
                            text = page.extract_text()
                            if text:
                                content_parts.append(f"=== Page {page_num} ===\n{text}\n")
                        except Exception as e:
                            logger.warning(f"Failed to extract text from page {page_num}: {e}")
                            continue
                
                if content_parts:
                    return '\n'.join(content_parts)
                    
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
            
            # Fallback to PyPDF2
            content_parts = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) > self.MAX_PDF_PAGES:
                    logger.warning(f"PDF has {len(pdf_reader.pages)} pages, processing only first {self.MAX_PDF_PAGES}")
                    pages_to_process = pdf_reader.pages[:self.MAX_PDF_PAGES]
                else:
                    pages_to_process = pdf_reader.pages
                
                for page_num, page in enumerate(pages_to_process, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            content_parts.append(f"=== Page {page_num} ===\n{text}\n")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            if not content_parts:
                raise FileProcessingError("No text content could be extracted from PDF")
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            logger.error(f"PDF content extraction failed: {e}")
            raise FileProcessingError(f"PDF processing failed: {str(e)}")
    
    def _extract_image_content(self, file_path: str) -> str:
        """Extract text content from image using OCR."""
        try:
            # Open and validate image
            with Image.open(file_path) as img:
                # Check image size
                max_size = (self.config.max_image_width, self.config.max_image_height)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    logger.info(f"Resizing large image: {img.size} -> {max_size}")
                    img = img.resize(max_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Perform OCR
                try:
                    # Try different OCR configurations
                    ocr_configs = [
                        '--oem 3 --psm 6',  # Default config
                        '--oem 3 --psm 3',  # Fully automatic page segmentation
                        '--oem 3 --psm 1',  # Automatic page segmentation with OSD
                    ]
                    
                    extracted_text = ""
                    for config in ocr_configs:
                        try:
                            text = pytesseract.image_to_string(img, config=config).strip()
                            if text and len(text) > len(extracted_text):
                                extracted_text = text
                        except Exception as e:
                            logger.warning(f"OCR config '{config}' failed: {e}")
                            continue
                    
                    if not extracted_text:
                        raise FileProcessingError("No text could be extracted from image")
                    
                    return extracted_text
                    
                except Exception as e:
                    logger.error(f"OCR processing failed: {e}")
                    raise FileProcessingError(f"OCR failed: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise FileProcessingError(f"Image processing failed: {str(e)}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of file for deduplication."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Hash generation failed: {e}")
            return ""
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup()


# Global file processor instance
_file_processor = None


def get_file_processor() -> FileProcessor:
    """Get global file processor instance."""
    global _file_processor
    if _file_processor is None:
        _file_processor = FileProcessor()
    return _file_processor


def process_uploaded_file(file_path: str) -> Dict[str, Any]:
    """
    Process an uploaded file and return extracted content.
    
    Args:
        file_path: Path to the uploaded file
        
    Returns:
        Dict containing file info, extracted content, and processing status
    """
    processor = get_file_processor()
    return processor.process_file(file_path)


def format_file_content_for_context(processed_file: Dict[str, Any]) -> str:
    """
    Format processed file content for use in conversation context.
    
    Args:
        processed_file: Result from process_uploaded_file
        
    Returns:
        Formatted string for inclusion in conversation context
    """
    if processed_file['processing_status'] != 'success':
        return f"[文件处理失败: {processed_file.get('error', '未知错误')}]"
    
    file_info = processed_file['file_info']
    content = processed_file['content']
    word_count = processed_file['word_count']
    
    # Create formatted content
    formatted_content = f"""
=== 附件内容 ===
文件名: {file_info['name']}
文件类型: {file_info['mime_type']}
文件大小: {file_info['size']} 字节
提取字数: {word_count}

--- 文件内容 ---
{content}
--- 内容结束 ---
"""
    
    return formatted_content.strip() 
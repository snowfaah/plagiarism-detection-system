"""
routes.py - Flask API route definitions.
"""
import os
import uuid
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'html', 'htm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_analysis_pipeline(text: str, filename: str = "text_input", 
                           pages: int = 1, pages_detail: list = None) -> dict:
    """Core analysis pipeline used by both endpoints."""
    from models.multilingual_similarity import analyze_document_similarity, get_page_level_scores
    from models.ai_detector import analyze_ai_probability, highlight_ai_sections
    from models.source_finder import find_sources, get_citations
    from models.xai_explainer import generate_xai_report, generate_graph_data
    from models.document_processor import detect_language, split_into_chunks
    
    start_time = time.time()
    
    # Detect language
    language = detect_language(text)
    
    # Split into chunks for analysis
    chunks = split_into_chunks(text)
    
    # Run similarity analysis
    similarity_result = analyze_document_similarity(text)
    similarity_score = similarity_result['similarity_score']
    
    # Run AI detection
    ai_result = analyze_ai_probability(text)
    ai_probability = ai_result['ai_probability']
    
    # Find sources
    sources = find_sources(text, similarity_score)
    
    # Get citations
    citations = {
        "APA": get_citations(sources[:5], "APA"),
        "MLA": get_citations(sources[:5], "MLA"),
        "Chicago": get_citations(sources[:5], "Chicago")
    }
    
    # Page-level analysis
    page_scores = []
    if pages_detail:
        page_scores = get_page_level_scores(pages_detail)
    
    # Generate XAI report
    xai_report = generate_xai_report(
        text, similarity_score, ai_probability, sources, language
    )
    
    # Generate graph data
    graph_data = generate_graph_data(similarity_score, ai_probability, page_scores)
    
    # Determine plagiarism level
    if similarity_score >= 70:
        plagiarism_level = "CRITICAL"
    elif similarity_score >= 40:
        plagiarism_level = "HIGH"
    elif similarity_score >= 20:
        plagiarism_level = "MEDIUM"
    else:
        plagiarism_level = "LOW"
    
    processing_time = round(time.time() - start_time, 2)
    
    return {
        "filename": filename,
        "pages": pages,
        "word_count": len(text.split()),
        "char_count": len(text),
        "language": language,
        "chunk_count": len(chunks),
        "similarity_score": similarity_score,
        "plagiarism_level": plagiarism_level,
        "ai_probability": ai_probability,
        "ai_confidence": ai_result.get('confidence', 'medium'),
        "sources": sources[:10],
        "citations": citations,
        "xai_report": xai_report,
        "graph_data": graph_data,
        "page_scores": page_scores,
        "processing_time_seconds": processing_time,
        "status": "success"
    }


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Academic Plagiarism Detector",
        "version": "2.0.0",
        "endpoints": [
            "POST /api/analyze",
            "POST /api/analyze-document",
            "GET /api/health"
        ]
    })


@api_bp.route('/analyze', methods=['POST'])
def analyze_text():
    """
    Analyze plain text for plagiarism.
    
    Body (JSON):
    {
        "text": "Your text to analyze...",
        "language": "auto"  (optional)
    }
    """
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({"error": "Request body must be JSON", "status": "error"}), 400
        
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Field 'text' is required and cannot be empty", "status": "error"}), 400
        
        if len(text.split()) < 10:
            return jsonify({"error": "Text must contain at least 10 words for analysis", "status": "error"}), 400
        
        if len(text) > 500000:
            return jsonify({"error": "Text too large. Maximum 500,000 characters.", "status": "error"}), 400
        
        result = run_analysis_pipeline(text, filename="text_input.txt", pages=1)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in /analyze: {e}", exc_info=True)
        return jsonify({"error": f"Analysis failed: {str(e)}", "status": "error"}), 500


@api_bp.route('/analyze-document', methods=['POST'])
def analyze_document():
    """
    Analyze uploaded document (PDF, DOCX, TXT) for plagiarism.
    
    Form Data:
    - file: document file (max 10MB)
    - language: "auto" (optional)
    
    Supported: PDF, DOCX, DOC, TXT, HTML
    """
    try:
        from models.document_processor import extract_text, validate_file
        
        # Check file in request
        if 'file' not in request.files:
            return jsonify({
                "error": "No file uploaded. Use form-data with key 'file'",
                "status": "error",
                "hint": "POST /api/analyze-document with form-data: file=<your_document>"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected", "status": "error"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "error": f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS).upper()}",
                "status": "error"
            }), 400
        
        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return jsonify({
                "error": f"File too large: {size_mb:.1f}MB. Maximum: 10MB",
                "status": "error"
            }), 413
        
        if file_size == 0:
            return jsonify({"error": "File is empty", "status": "error"}), 400
        
        # Save temporarily
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        safe_name = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"{unique_id}_{safe_name}"
        temp_filepath = os.path.join(upload_folder, temp_filename)
        
        file.save(temp_filepath)
        
        try:
            # Validate
            validation = validate_file(temp_filepath)
            if not validation['valid']:
                return jsonify({"error": validation['error'], "status": "error"}), 400
            
            # Extract text
            extraction = extract_text(temp_filepath)
            
            if 'error' in extraction:
                return jsonify({"error": extraction['error'], "status": "error"}), 422
            
            text = extraction.get('text', '')
            
            if not text or len(text.split()) < 10:
                return jsonify({
                    "error": "Document contains insufficient text (minimum 10 words required)",
                    "status": "error",
                    "extracted_words": len(text.split()) if text else 0
                }), 422
            
            # Run analysis
            pages_detail = extraction.get('pages_detail', None)
            result = run_analysis_pipeline(
                text=text,
                filename=safe_name,
                pages=extraction.get('pages', 1),
                pages_detail=pages_detail
            )
            
            # Add extraction metadata
            result['extraction_metadata'] = {
                "original_filename": safe_name,
                "file_size_mb": validation.get('size_mb', 0),
                "format": extraction.get('format', 'unknown'),
                "encoding": extraction.get('encoding', 'utf-8'),
            }
            
            return jsonify(result), 200
            
        finally:
            # Always cleanup temp file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        
    except Exception as e:
        logger.error(f"Error in /analyze-document: {e}", exc_info=True)
        return jsonify({"error": f"Document analysis failed: {str(e)}", "status": "error"}), 500


@api_bp.route('/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Batch analyze multiple documents (ZIP file).
    
    Form Data:
    - files: multiple files OR
    - zip: zip archive containing documents
    """
    try:
        from models.document_processor import extract_text, validate_file
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        results = []
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                "error": "No files uploaded. Use form-data with key 'files' (multiple files supported)",
                "status": "error"
            }), 400
        
        if len(files) > 10:
            return jsonify({"error": "Maximum 10 files per batch", "status": "error"}), 400
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                results.append({
                    "filename": file.filename,
                    "status": "skipped",
                    "reason": "Invalid file type"
                })
                continue
            
            safe_name = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            temp_filepath = os.path.join(upload_folder, f"{unique_id}_{safe_name}")
            
            try:
                file.save(temp_filepath)
                extraction = extract_text(temp_filepath)
                
                if 'error' in extraction:
                    results.append({"filename": safe_name, "status": "error", "error": extraction['error']})
                    continue
                
                text = extraction.get('text', '')
                if len(text.split()) < 10:
                    results.append({"filename": safe_name, "status": "error", "error": "Insufficient text"})
                    continue
                
                analysis = run_analysis_pipeline(text, safe_name, extraction.get('pages', 1))
                results.append({"filename": safe_name, "status": "success", **analysis})
                
            except Exception as e:
                results.append({"filename": safe_name, "status": "error", "error": str(e)})
            finally:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
        
        return jsonify({
            "status": "complete",
            "total_documents": len(files),
            "processed": len([r for r in results if r.get('status') == 'success']),
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Batch analyze error: {e}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500
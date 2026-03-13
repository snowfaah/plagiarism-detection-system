{
  "info": {
    "name": "Trace-AI — Plagiarism Detector API",
    "description": "Academic Plagiarism Detection API with document upload support.\n\n**Run locally:** `python app.py`\n**Base URL:** http://localhost:5000\n\nEndpoints:\n- GET  /api/health\n- POST /api/analyze         (JSON text input)\n- POST /api/analyze-document (file upload)\n- POST /api/batch-analyze   (multiple files)",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "version": { "major": 2, "minor": 0, "patch": 0 }
  },
  "variable": [
    { "key": "baseUrl", "value": "http://localhost:5000", "type": "string" }
  ],
  "item": [
    {
      "name": "1. Health Check",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/api/health",
        "description": "Check API status and available endpoints."
      },
      "response": []
    },
    {
      "name": "2. Analyze Text (JSON)",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{baseUrl}}/api/analyze",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"text\": \"Machine learning is a branch of artificial intelligence that focuses on enabling computers to learn from data without being explicitly programmed. The field has seen remarkable advances in recent years, particularly in deep learning techniques that use neural networks with many layers to model complex patterns. Supervised learning remains one of the most widely used approaches, where algorithms are trained on labeled datasets to make predictions. Researchers have also explored unsupervised learning methods that discover hidden structure in unlabeled data. Reinforcement learning, inspired by behavioral psychology, enables agents to learn optimal strategies through trial and error interactions with an environment.\",\n  \"language\": \"auto\"\n}",
          "options": { "raw": { "language": "json" } }
        },
        "description": "Analyze plain text for plagiarism and AI-generated content.\n\n**Body (JSON):**\n- `text` (required): Academic text to analyze\n- `language` (optional): 'auto' or language code (en, fr, de, es, zh...)"
      },
      "response": []
    },
    {
      "name": "3. Upload PDF Document",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/analyze-document",
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": "/path/to/your/research_paper.pdf",
              "description": "Upload PDF, DOCX, or TXT file (max 10MB)"
            },
            {
              "key": "language",
              "value": "auto",
              "type": "text",
              "description": "Language: 'auto' for detection, or 'en', 'fr', 'de', etc."
            }
          ]
        },
        "description": "Upload a PDF document for plagiarism analysis.\n\n**Form Data:**\n- `file`: PDF document (max 10MB)\n- `language`: 'auto' (optional)\n\n**Response includes:**\n- similarity_score: 0-100%\n- plagiarism_level: LOW/MEDIUM/HIGH/CRITICAL\n- ai_probability: 0-100%\n- sources: matched academic sources\n- xai_report: explainable AI breakdown\n- graph_data: chart data for visualization\n- page_scores: per-page analysis\n- citations: APA/MLA/Chicago format"
      },
      "response": []
    },
    {
      "name": "4. Upload DOCX Document",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/analyze-document",
        "body": {
          "mode": "formdata",
          "formdata": [
            { "key": "file", "type": "file", "src": "/path/to/essay.docx" },
            { "key": "language", "value": "auto", "type": "text" }
          ]
        },
        "description": "Upload a Word document (.docx) for analysis."
      },
      "response": []
    },
    {
      "name": "5. Upload TXT Document",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/analyze-document",
        "body": {
          "mode": "formdata",
          "formdata": [
            { "key": "file", "type": "file", "src": "/path/to/paper.txt" },
            { "key": "language", "value": "en", "type": "text" }
          ]
        },
        "description": "Upload a plain text file for analysis."
      },
      "response": []
    },
    {
      "name": "6. Batch Analyze (Multiple Files)",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/batch-analyze",
        "body": {
          "mode": "formdata",
          "formdata": [
            { "key": "files", "type": "file", "src": "/path/to/paper1.pdf" },
            { "key": "files", "type": "file", "src": "/path/to/paper2.docx" },
            { "key": "files", "type": "file", "src": "/path/to/paper3.txt" }
          ]
        },
        "description": "Batch analyze up to 10 documents at once.\n\n**Form Data:**\n- `files`: Multiple files (use 'files' key multiple times)\n\n**Response:**\n```json\n{\n  \"total_documents\": 3,\n  \"processed\": 3,\n  \"results\": [{ ...analysis per file... }]\n}\n```"
      },
      "response": []
    },
    {
      "name": "7. Test Error Handling (Empty File)",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{baseUrl}}/api/analyze",
        "body": {
          "mode": "raw",
          "raw": "{ \"text\": \"too short\" }",
          "options": { "raw": { "language": "json" } }
        },
        "description": "Test error handling for text that's too short."
      },
      "response": []
    }
  ]
}
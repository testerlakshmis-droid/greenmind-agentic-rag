# Logging utility for GreenMind Agent

import os
import logging
from datetime import datetime
from pathlib import Path
import json

class GreenMindLogger:
    """Custom logger for GreenMind with structured logging"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"greenmind_{timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger("GreenMind")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Structured logs (JSON format)
        self.structured_logs = []
    
    def log_query(self, query, session_id):
        """Log user query"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "query",
            "content": query,
            "session_id": session_id
        }
        self.structured_logs.append(log_entry)
        self.logger.info(f"Query: {query}")
    
    def log_tool_usage(self, tool_name, tool_input, tool_output, session_id):
        """Log tool usage with input and output"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_usage",
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output[:500] if isinstance(tool_output, str) else str(tool_output)[:500],
            "session_id": session_id
        }
        self.structured_logs.append(log_entry)
        self.logger.info(f"Tool: {tool_name} | Input: {tool_input}")
    
    def log_rag_retrieval(self, query, retrieved_docs, source, session_id):
        """Log RAG retrieval"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "rag_retrieval",
            "query": query,
            "source": source,
            "doc_count": len(retrieved_docs),
            "session_id": session_id
        }
        self.structured_logs.append(log_entry)
        self.logger.info(f"RAG Retrieval from {source}: Retrieved {len(retrieved_docs)} documents")
    
    def log_response(self, response, session_id, processing_time=None):
        """Log agent response"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "content": response[:1000] if len(response) > 1000 else response,
            "session_id": session_id,
            "processing_time_ms": processing_time
        }
        self.structured_logs.append(log_entry)
        self.logger.info(f"Response: {response[:200]}...")
    
    def log_error(self, error_message, error_type, session_id):
        """Log errors"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": error_message,
            "error_type": error_type,
            "session_id": session_id
        }
        self.structured_logs.append(log_entry)
        self.logger.error(f"Error ({error_type}): {error_message}")
    
    def save_structured_logs(self):
        """Save structured logs to JSON file"""
        json_log_file = self.log_dir / f"{self.log_file.stem}_structured.json"
        with open(json_log_file, 'w') as f:
            json.dump(self.structured_logs, f, indent=2)
    
    def get_session_summary(self, session_id):
        """Get summary of activities in a session"""
        session_logs = [log for log in self.structured_logs if log.get("session_id") == session_id]
        
        summary = {
            "session_id": session_id,
            "total_interactions": len(session_logs),
            "queries": len([l for l in session_logs if l["type"] == "query"]),
            "tools_used": list(set([l["tool_name"] for l in session_logs if l["type"] == "tool_usage"])),
            "errors": len([l for l in session_logs if l["type"] == "error"])
        }
        return summary

# Global logger instance
logger = GreenMindLogger()

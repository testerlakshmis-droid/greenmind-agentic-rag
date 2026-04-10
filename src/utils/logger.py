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
        
        try:
            self.log_dir.mkdir(exist_ok=True, parents=True)
        except OSError as e:
            print(f"Warning: Cannot create log directory {log_dir}: {e}")
            self.log_dir = Path(".")  # Fallback to current directory
        
        # Create session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"greenmind_{timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger("GreenMind")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicate log entries
        self.logger.handlers.clear()
        
        # File handler with error handling
        file_handler = None
        try:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.INFO)
        except (OSError, IOError) as e:
            print(f"Warning: Cannot create log file, using console only: {e}")
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if file_handler:
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Structured logs (JSON format) with size limit to prevent unbounded memory growth
        self.structured_logs = []
        self.max_logs = 10000
    
    def log_query(self, query, session_id):
        """Log user query with validation"""
        try:
            if not query:
                return
            query_str = str(query)[:2000]
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "query",
                "content": query_str,
                "session_id": str(session_id)[:100]
            }
            if len(self.structured_logs) < self.max_logs:
                self.structured_logs.append(log_entry)
            self.logger.info(f"Query: {query_str[:200]}")
        except Exception as e:
            self.logger.error(f"Error logging query: {e}")
    
    def log_tool_usage(self, tool_name, tool_input, tool_output, session_id):
        """Log tool usage with input and output, with validation"""
        try:
            if not tool_name:
                return
            tool_name_str = str(tool_name)[:100]
            input_str = str(tool_input)[:500]
            output_str = str(tool_output)[:800] if tool_output else "No output"
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "tool_usage",
                "tool_name": tool_name_str,
                "input": input_str,
                "output": output_str,
                "session_id": str(session_id)[:100]
            }
            if len(self.structured_logs) < self.max_logs:
                self.structured_logs.append(log_entry)
            self.logger.info(f"Tool: {tool_name_str} | Input: {input_str[:100]}")
        except Exception as e:
            self.logger.error(f"Error logging tool usage: {e}")
    
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
        """Save structured logs to JSON file with error handling"""
        try:
            json_log_file = self.log_dir / f"{self.log_file.stem}_structured.json"
            with open(json_log_file, 'w') as f:
                json.dump(self.structured_logs, f, indent=2, default=str)
            self.logger.info(f"Structured logs saved to {json_log_file}")
        except (OSError, IOError) as e:
            self.logger.error(f"Cannot save structured logs: {e}")
        except Exception as e:
            self.logger.error(f"Error serializing structured logs: {e}")
    
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

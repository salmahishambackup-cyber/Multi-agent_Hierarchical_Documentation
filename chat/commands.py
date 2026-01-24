"""
Command parser for chat interface.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import re


class CommandParser:
    """
    Parse user commands and natural language input.
    """
    
    COMMANDS = {
        "document": "Full pipeline - analyze and generate documentation",
        "analyze": "Phase 1 only - static code analysis",
        "generate docstrings": "Phase 2 only - generate docstrings",
        "generate readme": "Phase 3 only - generate README",
        "validate": "Phase 4 only - validate documentation",
        "evaluate": "Phase 5 only - evaluate documentation",
        "show readme": "Display generated README",
        "show report": "Display evaluation report",
        "help": "Show available commands",
        "status": "Show pipeline state",
        "exit": "Exit the assistant",
        "quit": "Exit the assistant",
    }
    
    @staticmethod
    def parse(user_input: str) -> Dict[str, Any]:
        """
        Parse user input into command and parameters.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Dictionary with command type and parameters
        """
        user_input = user_input.strip().lower()
        
        # Exit commands
        if user_input in ["exit", "quit", "q"]:
            return {"command": "exit"}
        
        # Help command
        if user_input in ["help", "?"]:
            return {"command": "help"}
        
        # Status command
        if user_input == "status":
            return {"command": "status"}
        
        # Show commands
        if "show readme" in user_input:
            return {"command": "show_readme"}
        
        if "show report" in user_input:
            return {"command": "show_report"}
        
        # Generate commands
        if "generate docstring" in user_input:
            return {"command": "phase2"}
        
        if "generate readme" in user_input:
            return {"command": "phase3"}
        
        # Validate command
        if "validate" in user_input:
            return {"command": "phase4"}
        
        # Evaluate command
        if "evaluate" in user_input:
            return {"command": "phase5"}
        
        # Analyze command
        if "analyze" in user_input:
            # Extract path if provided
            path_match = re.search(r'analyze\s+([^\s]+)', user_input)
            path = path_match.group(1) if path_match else None
            return {"command": "phase1", "path": path}
        
        # Document command (natural language or explicit)
        if any(keyword in user_input for keyword in ["document", "please document", "can you document"]):
            # Extract path if provided
            path_match = re.search(r'(?:document|this project)\s+([^\s]+)', user_input)
            path = path_match.group(1) if path_match else None
            return {"command": "document", "path": path}
        
        # Default: treat as document command
        return {"command": "unknown", "input": user_input}
    
    @staticmethod
    def get_help() -> str:
        """Get help text with available commands."""
        lines = ["\n📖 Available Commands:"]
        for cmd, desc in CommandParser.COMMANDS.items():
            lines.append(f"  • {cmd:<20} - {desc}")
        return "\n".join(lines)

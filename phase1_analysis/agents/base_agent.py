"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, repo_path: str, artifacts_dir: str = "./artifacts"):
        """
        Initialize base agent.
        
        Args:
            repo_path: Path to repository
            artifacts_dir: Directory for artifacts
        """
        self.repo_path = Path(repo_path).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Run the agent.
        
        Returns:
            Dictionary with results
        """
        pass
    
    def get_artifact_path(self, filename: str) -> Path:
        """
        Get path for an artifact file.
        
        Args:
            filename: Name of the artifact file
            
        Returns:
            Full path to artifact
        """
        return self.artifacts_dir / filename
    
    def save_artifact(self, filename: str, data: Any) -> Path:
        """
        Save artifact to file.
        
        Args:
            filename: Name of the artifact file
            data: Data to save
            
        Returns:
            Path to saved file
        """
        from utils.json_writer import write_json
        
        artifact_path = self.get_artifact_path(filename)
        write_json(artifact_path, data)
        return artifact_path

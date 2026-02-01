"""
Phase 4: Validation

This phase validates the generated documentation using a Critic agent.
"""

from .validator import Validator
from .agents.critic import Critic

__all__ = ["Validator", "Critic"]

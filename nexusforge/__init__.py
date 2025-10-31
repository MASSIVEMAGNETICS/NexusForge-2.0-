"""
NexusForge 2.0 - AGI-lite Autonomous Agent Framework

Combines FractalAgentForge's recursive templates, Auto-GPT's goal-breaking,
BabyAGI's self-building functions, SuperAGI's production GUI, JARVIS's
multi-modal experts, AutoGen's agent chats, and CrewAI's role crews.
"""

__version__ = "2.0.0"
__author__ = "MASSIVEMAGNETICS"

from nexusforge.core.fractal_agent import FractalAgent
from nexusforge.core.nexus import NexusForge

__all__ = ["FractalAgent", "NexusForge"]

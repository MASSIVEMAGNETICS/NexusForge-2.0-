"""
NexusForge 2.0 - AGI-lite Autonomous Agent Framework

Combines FractalAgentForge's recursive templates, Auto-GPT's goal-breaking,
BabyAGI's self-building functions, SuperAGI's production GUI, JARVIS's
multi-modal experts, AutoGen's agent chats, and CrewAI's role crews —
extended with:

* Persistent identity-locked episodic memory (HDDR)
* REM sleep cycles for idle memory consolidation and pruning
* Self-synthesis engine for novel idea generation
* Gravitational attention (physics-based transformer replacement)
* GravitationalTokenFormer (next-generation sequence model)
* Multi-modal sensory processing pipeline
"""

__version__ = "2.0.0"
__author__ = "MASSIVEMAGNETICS"

from nexusforge.core.fractal_agent import FractalAgent
from nexusforge.core.nexus import NexusForge

# Memory subsystems
from nexusforge.memory.identity_anchor import IdentityAnchor
from nexusforge.memory.episodic_memory import EpisodicMemory, MemoryType
from nexusforge.memory.rem_cycle import REMCycleEngine
from nexusforge.memory.synthesis import SelfSynthesisEngine

# Attention & model
from nexusforge.attention.gravitational import GravitationalAttentionLayer, GravitationalConfig
from nexusforge.tokenformer.tokenformer import GravitationalTokenFormer, TokenFormerConfig

# Sensory layer
from nexusforge.sensory.processor import SensoryProcessor, SensoryModality

__all__ = [
    # Core
    "FractalAgent",
    "NexusForge",
    # Memory
    "IdentityAnchor",
    "EpisodicMemory",
    "MemoryType",
    "REMCycleEngine",
    "SelfSynthesisEngine",
    # Attention & model
    "GravitationalAttentionLayer",
    "GravitationalConfig",
    "GravitationalTokenFormer",
    "TokenFormerConfig",
    # Sensory
    "SensoryProcessor",
    "SensoryModality",
]

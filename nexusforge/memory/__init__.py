"""
NexusForge Memory System

Implements persistent, identity-locked memory with REM sleep cycles,
episodic storage, HDDR compression, and self-synthesis.
"""

from nexusforge.memory.identity_anchor import IdentityAnchor, IdentityVector
from nexusforge.memory.episodic_memory import (
    EpisodicMemory,
    MemoryEpisode,
    MemoryType,
    HDDREncoder,
)
from nexusforge.memory.rem_cycle import REMCycleEngine, REMPhase, REMCycleStats
from nexusforge.memory.synthesis import SelfSynthesisEngine

__all__ = [
    "IdentityAnchor",
    "IdentityVector",
    "EpisodicMemory",
    "MemoryEpisode",
    "MemoryType",
    "HDDREncoder",
    "REMCycleEngine",
    "REMPhase",
    "REMCycleStats",
    "SelfSynthesisEngine",
]

"""
NexusForge Memory System

In-memory identity-locked episodic store with REM sleep cycle consolidation,
HDDR compression, and self-synthesis.  All state is held in Python objects
(no file or database I/O); callers that need durable persistence should
serialise the ``EpisodicMemory`` instance externally.
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

"""
Sensory Processor — Multi-modal sensory data ingestion connected to episodic
memory.

The sensory layer is the front door of the NexusForge memory system.  Raw
signals from any modality (text, numeric, structured, binary, …) are:

1. **Pre-processed** into a canonical string / numeric representation.
2. **Salience-filtered** — only events above a computed importance threshold
   are forwarded to episodic memory (sparse parsing).
3. **Tagged** with modality, timestamp, and optional metadata.
4. **Stored** in the :class:`~nexusforge.memory.episodic_memory.EpisodicMemory`
   as a ``SENSORY`` episode.
5. **Notified** to the REM engine (so sleep cycles reset their idle timer).

The processor deliberately mirrors the biological sensory → hippocampus →
long-term memory pipeline:

    Sensory cortex     → Sensory Processor
    Thalamic gating    → Salience filter (importance threshold)
    Hippocampus        → EpisodicMemory.store()
    Sleep consolidation→ REMCycleEngine
"""

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SensoryModality(Enum):
    """Input modality categories."""

    TEXT = "text"
    NUMERIC = "numeric"
    STRUCTURED = "structured"   # dict / list / JSON-like
    BINARY = "binary"           # bytes / file content
    EVENT = "event"             # system / agent events
    INTERNAL = "internal"       # agent's own outputs / thoughts


@dataclass
class SensoryEvent:
    """A single sensory event before it is stored in episodic memory."""

    modality: SensoryModality
    raw_data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Filled in after processing
    episode_id: Optional[str] = None
    was_stored: bool = False


class SensoryProcessor:
    """
    Multi-modal sensory data processor.

    Accepts raw signals, scores their salience, and injects important events
    into the episodic memory system.

    Args:
        episodic_memory: An
            :class:`~nexusforge.memory.episodic_memory.EpisodicMemory` instance.
        rem_engine: Optional
            :class:`~nexusforge.memory.rem_cycle.REMCycleEngine` to notify
            on each input (resets the idle timer).
        base_importance_threshold: Minimum computed importance for an event to
            be stored (0.0–1.0).  Events below this are discarded.
        novelty_boost: Extra importance added when an event is novel (not
            similar to recent memories).

    Example::

        processor = SensoryProcessor(episodic_memory=memory)
        event = processor.process("The gravitational attention model converged.")
        print(event.episode_id)   # UUID if stored, None if filtered out
    """

    def __init__(
        self,
        episodic_memory=None,
        rem_engine=None,
        base_importance_threshold: float = 0.3,
        novelty_boost: float = 0.2,
    ):
        self.memory = episodic_memory
        self.rem_engine = rem_engine
        self.importance_threshold = base_importance_threshold
        self.novelty_boost = novelty_boost

        # Recent event ring buffer for novelty detection
        self._recent_texts: List[str] = []
        self._recent_capacity = 20

        # Running statistics
        self.total_received = 0
        self.total_stored = 0
        self.total_filtered = 0

    # ------------------------------------------------------------------
    # Primary interface
    # ------------------------------------------------------------------

    def process(
        self,
        data: Any,
        modality: Optional[SensoryModality] = None,
        importance_override: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SensoryEvent:
        """
        Process a single piece of sensory data.

        Args:
            data: The raw input — can be a string, number, dict, list, etc.
            modality: If ``None``, the modality is auto-detected.
            importance_override: If provided, bypasses salience scoring.
            tags: Optional string tags for the episode.
            metadata: Optional key-value metadata.

        Returns:
            A :class:`SensoryEvent` describing what happened.  Check
            ``event.was_stored`` and ``event.episode_id``.
        """
        self.total_received += 1

        # Notify REM engine (reset idle timer)
        if self.rem_engine is not None:
            self.rem_engine.record_activity()

        # Auto-detect modality
        if modality is None:
            modality = self._detect_modality(data)

        # Convert to canonical string form
        canonical = self._canonicalize(data, modality)

        # Compute salience
        if importance_override is not None:
            importance = float(importance_override)
        else:
            importance = self._compute_importance(canonical, modality)

        # Novelty boost
        importance = self._apply_novelty_boost(canonical, importance)

        # Build event
        event = SensoryEvent(
            modality=modality,
            raw_data=data,
            importance=importance,
            tags=list(tags) if tags else [modality.value],
            metadata=dict(metadata) if metadata else {},
        )

        # Store in episodic memory if above threshold
        if importance >= self.importance_threshold and self.memory is not None:
            from nexusforge.memory.episodic_memory import MemoryType

            episode_id = self.memory.store(
                content=canonical,
                memory_type=MemoryType.SENSORY,
                importance=importance,
                tags=event.tags,
                context=event.metadata,
            )
            event.episode_id = episode_id
            event.was_stored = episode_id is not None
            if event.was_stored:
                self.total_stored += 1
            else:
                self.total_filtered += 1
        else:
            self.total_filtered += 1

        # Update novelty buffer
        self._update_recent(canonical)

        return event

    def process_batch(
        self,
        items: List[Any],
        modality: Optional[SensoryModality] = None,
    ) -> List[SensoryEvent]:
        """Process a list of sensory inputs in order."""
        return [self.process(item, modality=modality) for item in items]

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return ingestion statistics."""
        return {
            "total_received": self.total_received,
            "total_stored": self.total_stored,
            "total_filtered": self.total_filtered,
            "storage_rate": (
                round(self.total_stored / self.total_received, 3)
                if self.total_received > 0
                else 0.0
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_modality(self, data: Any) -> SensoryModality:
        """Infer the modality from the Python type of *data*."""
        if isinstance(data, str):
            return SensoryModality.TEXT
        if isinstance(data, (int, float)):
            return SensoryModality.NUMERIC
        if isinstance(data, (dict, list)):
            return SensoryModality.STRUCTURED
        if isinstance(data, (bytes, bytearray)):
            return SensoryModality.BINARY
        return SensoryModality.EVENT

    def _canonicalize(self, data: Any, modality: SensoryModality) -> str:
        """Convert *data* to a canonical string representation."""
        if modality == SensoryModality.TEXT:
            return str(data).strip()
        if modality == SensoryModality.NUMERIC:
            return f"numeric_value:{data}"
        if modality == SensoryModality.STRUCTURED:
            # Flatten dict/list to a readable string
            if isinstance(data, dict):
                parts = [f"{k}={v}" for k, v in data.items()]
                return "structured:{" + ", ".join(parts) + "}"
            return f"structured:{data}"
        if modality == SensoryModality.BINARY:
            return f"binary_data:len={len(data)}"
        return str(data)

    def _compute_importance(self, text: str, modality: SensoryModality) -> float:
        """
        Estimate the salience of a sensory event.

        Heuristics:
        * **Length signal** — longer texts carry more information.
        * **Question/command markers** — interrogatives and imperatives tend
          to be important.
        * **Numeric data** — always gets a moderate default.
        * **Structural complexity** — dicts with many keys are more salient.
        """
        if modality == SensoryModality.NUMERIC:
            return 0.5

        if modality == SensoryModality.BINARY:
            return 0.4

        # Text-based importance
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        # Length signal (log scale, capped)
        length_score = min(1.0, math.log(word_count + 1) / math.log(50))

        # Question or command markers boost importance
        question_words = {"what", "why", "how", "when", "where", "who", "which"}
        has_question = any(w.lower() in question_words for w in words[:5])
        question_bonus = 0.15 if has_question else 0.0

        # Capitalised nouns (entities) signal higher importance
        entities = sum(1 for w in words if w[0].isupper() and w.lower() not in question_words)
        entity_score = min(0.2, entities * 0.04)

        base = 0.3  # Floor
        importance = base + 0.35 * length_score + question_bonus + entity_score
        return min(1.0, importance)

    def _apply_novelty_boost(self, text: str, importance: float) -> float:
        """Boost importance if the event is dissimilar to recent events."""
        if not self._recent_texts:
            return importance

        # Simple novelty: fraction of words not seen in recent texts
        words = set(re.findall(r"\b\w+\b", text.lower()))
        recent_words: set = set()
        for rt in self._recent_texts:
            recent_words.update(re.findall(r"\b\w+\b", rt.lower()))

        if not words:
            return importance

        overlap = len(words & recent_words) / len(words)
        novelty = 1.0 - overlap

        if novelty > 0.5:
            importance = min(1.0, importance + self.novelty_boost * novelty)
        return importance

    def _update_recent(self, text: str) -> None:
        """Maintain the novelty-detection ring buffer."""
        self._recent_texts.append(text)
        if len(self._recent_texts) > self._recent_capacity:
            self._recent_texts.pop(0)

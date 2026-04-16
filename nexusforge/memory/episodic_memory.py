"""
Episodic Memory — Human-like day-to-day memory with HDDR compression.

Implements an episodic memory system modelled on human autobiographical
memory with:

* **Temporal context** — every episode is timestamped
* **Semantic context** — HDDR (High-Dimensional Dense Representation)
  vectors allow rapid similarity search without an external vector store
* **Importance scoring** — critical events are retained longer
* **Identity alignment** — memories aligned with the user's identity are
  preserved preferentially during REM pruning
* **Intelligent pruning** — a *retention score* combines importance,
  identity alignment, recency, and access frequency
* **Sparse parsing** — low-importance input is silently dropped so the
  store does not fill with noise
* **Working memory** — a 7-slot ring buffer for the most recent context
  (Miller's Law: 7 ± 2)
"""

import math
import re
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class MemoryType(Enum):
    """Semantic categories for memory episodes."""

    SENSORY = "sensory"          # Raw sensory input
    SEMANTIC = "semantic"        # Factual / conceptual knowledge
    PROCEDURAL = "procedural"    # How-to knowledge
    EMOTIONAL = "emotional"      # Emotionally tagged experiences
    EPISODIC = "episodic"        # Time-stamped personal experiences
    WORKING = "working"          # Current active context


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MemoryEpisode:
    """A single episode stored in episodic memory."""

    episode_id: str
    content: Any
    memory_type: MemoryType
    timestamp: datetime

    # Quality metrics
    importance: float = 0.5           # 0.0–1.0
    identity_alignment: float = 0.5   # 0.0–1.0
    emotional_valence: float = 0.0    # -1.0 (negative) … +1.0 (positive)

    # Access tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # HDDR semantic embedding
    embedding: Optional[List[float]] = None

    # Organisation
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    # Compression state
    is_compressed: bool = False
    compression_summary: Optional[str] = None

    # ------------------------------------------------------------------
    def access(self) -> None:
        """Record an access and slightly boost importance (rehearsal effect)."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.importance = min(1.0, self.importance + 0.02)

    def decay(self, rate: float = 0.01) -> None:
        """Apply forgetting-curve decay to importance."""
        self.importance = max(0.0, self.importance - rate)

    @property
    def retention_score(self) -> float:
        """
        Combined score (0–1) determining whether a memory should be kept.

        Weights:
          * 40 % importance
          * 30 % identity alignment
          * 20 % recency (exponential decay)
          * 10 % access frequency (capped at 10 accesses)
        """
        recency = 1.0
        reference_time = self.last_accessed if self.last_accessed else self.timestamp
        days_old = (datetime.now() - reference_time).total_seconds() / 86_400
        recency = math.exp(-0.1 * days_old)

        return (
            0.4 * self.importance
            + 0.3 * self.identity_alignment
            + 0.2 * recency
            + 0.1 * min(1.0, self.access_count / 10.0)
        )


# ---------------------------------------------------------------------------
# HDDR encoder
# ---------------------------------------------------------------------------


class HDDREncoder:
    """
    High-Dimensional Dense Representation encoder.

    Maps arbitrary text to a fixed-size float vector using a deterministic
    prime-based projection.  No external ML library is required — only the
    Python standard library and basic arithmetic.

    The design provides:
    * **Determinism** — same text always yields the same vector
    * **Similarity preservation** — semantically similar texts produce
      vectors with higher cosine similarity than dissimilar texts
    * **Compression** — multiple vectors can be merged into a centroid
    """

    _PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

    def __init__(self, dim: int = 128):
        self.dim = dim
        self._basis = self._create_basis(dim)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encode(self, text: str) -> List[float]:
        """Encode *text* to an L2-normalized HDDR vector."""
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return [0.0] * self.dim

        vector = [0.0] * self.dim
        for pos, word in enumerate(words):
            word_hash = sum(ord(c) * (i + 1) for i, c in enumerate(word))
            primary = word_hash % self.dim
            weight = 1.0 / math.log(pos + 2)
            for d in range(self.dim):
                vector[d] += weight * self._basis[primary][d]

        return self._normalize(vector)

    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Cosine similarity between two HDDR vectors (clamped to [-1, 1])."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        return max(-1.0, min(1.0, dot))

    def compress(self, vectors: List[List[float]]) -> List[float]:
        """Compress a collection of HDDR vectors into a single centroid."""
        if not vectors:
            return [0.0] * self.dim
        merged = [sum(v[d] for v in vectors) / len(vectors) for d in range(self.dim)]
        return self._normalize(merged)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_basis(self, dim: int) -> List[List[float]]:
        """Create a deterministic set of *dim* orthogonal-ish basis vectors."""
        basis = []
        for i in range(dim):
            vec = [
                math.sin(i * self._PRIMES[j % len(self._PRIMES)] + j * 0.1)
                for j in range(dim)
            ]
            basis.append(self._normalize(vec))
        return basis

    @staticmethod
    def _normalize(vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec


# ---------------------------------------------------------------------------
# Episodic Memory store
# ---------------------------------------------------------------------------


class EpisodicMemory:
    """
    Human-like episodic memory store with intelligent pruning and HDDR.

    The store models three tiers of human memory:

    1. **Working memory** — a 7-slot ring buffer of the most recent episodes
       (always retained, Miller's Law)
    2. **Active episodic store** — episodes above the sparse threshold that
       are retained as long as their retention score is healthy
    3. **Compressed archive** — old episodes whose details are collapsed to a
       short summary, preserving their embedding for future recall

    Pruning is triggered automatically when the store exceeds *max_episodes*,
    and more aggressively by the :class:`~nexusforge.memory.rem_cycle.REMCycleEngine`
    during sleep phases.
    """

    def __init__(
        self,
        identity_anchor=None,
        hddr_dim: int = 128,
        max_episodes: int = 1000,
        pruning_threshold: float = 0.2,
        sparse_threshold: float = 0.3,
    ):
        """
        Args:
            identity_anchor: Optional :class:`~nexusforge.memory.identity_anchor.IdentityAnchor`
                used to score identity alignment of incoming episodes.
            hddr_dim: Dimensionality of the HDDR embedding space.
            max_episodes: Maximum episodes before automatic pruning.
            pruning_threshold: Episodes with *retention_score* below this
                value are candidates for removal.
            sparse_threshold: Episodes with *importance* below this value are
                silently dropped (sparse parsing), unless they are working-memory
                type.
        """
        self.identity_anchor = identity_anchor
        self.hddr = HDDREncoder(dim=hddr_dim)
        self.max_episodes = max_episodes
        self.pruning_threshold = pruning_threshold
        self.sparse_threshold = sparse_threshold

        self.episodes: Dict[str, MemoryEpisode] = {}
        self.temporal_index: List[str] = []          # Ordered by insertion time
        self.semantic_index: Dict[str, List[str]] = {}  # tag → [episode_ids]

        # Working memory — small ring buffer (Miller's Law: 7 ± 2)
        self.working_memory: List[str] = []
        self.working_memory_capacity = 7

        # Aggregate counters
        self.total_stored = 0
        self.total_pruned = 0

    # ------------------------------------------------------------------
    # Primary operations
    # ------------------------------------------------------------------

    def store(
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Store a new memory episode.

        Applies **sparse parsing** — episodes below the *sparse_threshold*
        are silently dropped unless they are ``WORKING`` type.

        Returns:
            The new episode's ID, or ``None`` if the episode was filtered out.
        """
        # Sparse parsing filter
        if memory_type != MemoryType.WORKING and importance < self.sparse_threshold:
            return None

        content_str = str(content) if not isinstance(content, str) else content

        # HDDR embedding
        embedding = self.hddr.encode(content_str)

        # Identity alignment
        identity_alignment = 0.5
        if self.identity_anchor and self.identity_anchor.is_configured():
            raw = self.identity_anchor.compute_alignment(content_str)
            identity_alignment = raw  # already in [0, 1]

        episode = MemoryEpisode(
            episode_id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            identity_alignment=identity_alignment,
            emotional_valence=emotional_valence,
            embedding=embedding,
            tags=list(tags) if tags else [],
            context=dict(context) if context else {},
        )

        self.episodes[episode.episode_id] = episode
        self.temporal_index.append(episode.episode_id)

        # Semantic tag index
        for tag in episode.tags:
            self.semantic_index.setdefault(tag, []).append(episode.episode_id)

        self._update_working_memory(episode.episode_id)
        self.total_stored += 1

        # Auto-prune when over capacity
        if len(self.episodes) > self.max_episodes:
            self._prune_weak_memories()

        return episode.episode_id

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
    ) -> List[MemoryEpisode]:
        """
        Retrieve the *top_k* episodes most relevant to *query*.

        Relevance is a weighted combination of HDDR cosine similarity and the
        episode's retention score.  Accessing a recalled episode strengthens it
        (rehearsal effect).
        """
        if not self.episodes:
            return []

        query_vec = self.hddr.encode(query)

        candidates = list(self.episodes.values())
        if memory_type:
            candidates = [e for e in candidates if e.memory_type == memory_type]
        if min_importance > 0:
            candidates = [e for e in candidates if e.importance >= min_importance]

        if not candidates:
            return []

        scored = []
        for ep in candidates:
            sim = self.hddr.similarity(query_vec, ep.embedding) if ep.embedding else 0.0
            score = 0.6 * sim + 0.4 * ep.retention_score
            scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for _, ep in scored[:top_k]:
            ep.access()
            results.append(ep)
        return results

    def get_recent(self, n: int = 10) -> List[MemoryEpisode]:
        """Return the *n* most recently stored episodes."""
        recent_ids = self.temporal_index[-n:]
        return [
            self.episodes[eid]
            for eid in reversed(recent_ids)
            if eid in self.episodes
        ]

    def get_working_memory(self) -> List[MemoryEpisode]:
        """Return the current working-memory ring buffer."""
        return [self.episodes[eid] for eid in self.working_memory if eid in self.episodes]

    # ------------------------------------------------------------------
    # Pruning & housekeeping (called by REMCycleEngine and internally)
    # ------------------------------------------------------------------

    def _update_working_memory(self, episode_id: str) -> None:
        """Maintain the 7-slot working-memory ring buffer."""
        self.working_memory.append(episode_id)
        if len(self.working_memory) > self.working_memory_capacity:
            self.working_memory.pop(0)

    def _prune_weak_memories(self, n_prune: Optional[int] = None) -> int:
        """
        Intelligent pruning — remove low-value memories.

        Protected: working-memory slots are never pruned.
        Pruning order: ascending *retention_score* (weakest first).

        Returns:
            Number of episodes actually removed.
        """
        if not self.episodes:
            return 0

        protected: Set[str] = set(self.working_memory)

        scored = [
            (ep.retention_score, ep.episode_id)
            for ep in self.episodes.values()
            if ep.episode_id not in protected
        ]
        if not scored:
            return 0

        scored.sort(key=lambda x: x[0])

        if n_prune is None:
            target = int(self.max_episodes * 0.8)
            n_prune = max(0, len(self.episodes) - target)

        pruned = 0
        for score, eid in scored:
            if pruned >= n_prune:
                break
            if score < self.pruning_threshold or len(self.episodes) > self.max_episodes:
                self._remove_episode(eid)
                pruned += 1

        self.total_pruned += pruned
        return pruned

    def _remove_episode(self, episode_id: str) -> None:
        """Remove an episode from all indices."""
        if episode_id not in self.episodes:
            return

        ep = self.episodes.pop(episode_id)

        if episode_id in self.temporal_index:
            self.temporal_index.remove(episode_id)

        for tag in ep.tags:
            if tag in self.semantic_index:
                self.semantic_index[tag] = [
                    eid for eid in self.semantic_index[tag] if eid != episode_id
                ]

        if episode_id in self.working_memory:
            self.working_memory.remove(episode_id)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return a summary of the current memory state."""
        if self.episodes:
            importances = [e.importance for e in self.episodes.values()]
            alignments = [e.identity_alignment for e in self.episodes.values()]
            avg_importance = sum(importances) / len(importances)
            avg_alignment = sum(alignments) / len(alignments)
        else:
            avg_importance = avg_alignment = 0.0

        type_counts: Dict[str, int] = {}
        for ep in self.episodes.values():
            key = ep.memory_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        return {
            "total_episodes": len(self.episodes),
            "total_stored": self.total_stored,
            "total_pruned": self.total_pruned,
            "working_memory_size": len(self.working_memory),
            "avg_importance": round(avg_importance, 3),
            "avg_identity_alignment": round(avg_alignment, 3),
            "by_type": type_counts,
            "capacity_used": f"{len(self.episodes)}/{self.max_episodes}",
        }

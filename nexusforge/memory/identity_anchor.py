"""
Identity Anchor — Locks agent identity via user's "I am" paragraph statement.

The identity anchor:
  1. Stores the user's self-describing paragraph
  2. Computes an identity embedding vector (no external deps — pure Python)
  3. Provides alignment scoring for incoming data
  4. Prevents identity drift by anchoring all memory operations

Inspired by cognitive theories of autobiographical memory where the
self-concept acts as an organising schema for all personal memories.
"""

import re
import math
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IdentityVector:
    """Dense vector representation of a user's identity."""

    vector: List[float]
    dimensions: int
    vocabulary: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


class IdentityAnchor:
    """
    Identity Anchor — the "I am" statement that defines agent identity.

    Records who the user says they are and produces a compact vector that
    every piece of incoming information can be compared against.  Memories
    that align strongly with the identity are retained and reinforced;
    memories that deviate are down-weighted during REM pruning.

    Usage::

        anchor = IdentityAnchor()
        anchor.set_identity(
            "I am a creative engineer who values deep thinking, "
            "long-term vision, and building systems that learn."
        )
        score = anchor.compute_alignment("building adaptive learning systems")
        # score ≈ 0.85  (high alignment)
    """

    STOPWORDS = frozenset(
        [
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "am", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "can", "i", "my", "me", "we", "our", "you", "your",
        ]
    )

    def __init__(self, vector_dim: int = 64):
        self.vector_dim = vector_dim
        self.identity_statement: Optional[str] = None
        self.identity_vector: Optional[IdentityVector] = None
        self.identity_id: Optional[str] = None
        self.core_values: List[str] = []
        self.creation_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_identity(self, paragraph: str) -> IdentityVector:
        """
        Set the identity from a user's "I am" paragraph.

        The paragraph should describe who the agent is, their values,
        capabilities, and perspective on the world.

        Args:
            paragraph: Free-text self-description starting with "I am …"

        Returns:
            The computed :class:`IdentityVector`.
        """
        self.identity_statement = paragraph
        self.creation_time = datetime.now()

        self.core_values = self._extract_core_values(paragraph)
        vocab = self._build_vocabulary(paragraph)
        vector = self._compute_embedding(paragraph, vocab)

        self.identity_vector = IdentityVector(
            vector=vector,
            dimensions=self.vector_dim,
            vocabulary=vocab,
            timestamp=self.creation_time,
        )

        # Stable identity hash (16-char hex)
        self.identity_id = hashlib.sha256(paragraph.encode()).hexdigest()[:16]

        return self.identity_vector

    def compute_alignment(self, text: str) -> float:
        """
        Compute identity alignment score for given text.

        Returns a cosine similarity in [0, 1] where:
          * **1.0** — perfectly aligned with identity
          * **0.5** — moderately similar (~60° angle)
          * **0.0** — orthogonal / completely unrelated to identity

        Negative values are not possible because the embedding vectors are
        non-negative, so 0.0 is the minimum (orthogonal), not counter-aligned.

        If no identity has been set, returns 0.5 (moderate similarity midpoint).
        """
        if not self.identity_vector:
            return 0.5

        text_vector = self._compute_embedding(text, self.identity_vector.vocabulary)

        # Similarity score in [0, 1] — embedding vectors are non-negative so
        # the dot product of two unit vectors always falls in [0, 1].
        dot = sum(a * b for a, b in zip(self.identity_vector.vector, text_vector))
        return max(0.0, min(1.0, dot))

    def is_configured(self) -> bool:
        """Check whether an identity paragraph has been provided."""
        return self.identity_statement is not None

    def get_identity_summary(self) -> Dict[str, Any]:
        """Return a human-readable summary of the current identity state."""
        preview = None
        if self.identity_statement:
            preview = (
                self.identity_statement[:100] + "…"
                if len(self.identity_statement) > 100
                else self.identity_statement
            )
        return {
            "identity_id": self.identity_id,
            "has_identity": self.is_configured(),
            "core_values": self.core_values,
            "statement_preview": preview,
            "vector_dimensions": self.vector_dim,
            "creation_time": (
                self.creation_time.isoformat() if self.creation_time else None
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_core_values(self, text: str) -> List[str]:
        """Extract the most significant identity terms from the paragraph."""
        words = re.findall(r"\b[a-z]+\b", text.lower())
        filtered = [w for w in words if w not in self.STOPWORDS and len(w) > 3]
        freq: Dict[str, int] = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
        sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:20]]

    def _build_vocabulary(self, text: str) -> Dict[str, int]:
        """Build a vocabulary → dimension-index mapping from text."""
        words = re.findall(r"\b[a-z]+\b", text.lower())
        vocab: Dict[str, int] = {}
        idx = 0
        for w in words:
            if w not in vocab and w not in self.STOPWORDS:
                vocab[w] = idx % self.vector_dim
                idx += 1
        return vocab

    def _compute_embedding(self, text: str, vocab: Dict[str, int]) -> List[float]:
        """
        Compute a dense positional embedding vector for *text* using *vocab*.

        Uses a bag-of-words approach with position-weighted contributions and
        harmonic spread so that related terms influence nearby dimensions.
        """
        vector = [0.0] * self.vector_dim
        words = re.findall(r"\b[a-z]+\b", text.lower())

        for i, word in enumerate(words):
            if word in vocab:
                dim = vocab[word]
                pos_weight = 1.0 / math.log(i + 2)
                vector[dim] += pos_weight
                # Harmonic spread into neighbouring dimensions
                for h in range(1, 4):
                    harmonic_dim = (dim + h * 7) % self.vector_dim
                    vector[harmonic_dim] += pos_weight / (h * 2)

        # L2 normalise
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

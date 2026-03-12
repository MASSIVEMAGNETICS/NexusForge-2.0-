"""
Self-Synthesis Engine — Novel idea generation through self-inference.

When the agent introspects over its own memory it can produce emergent
concepts that were never explicitly stored.  This module implements that
capacity:

1. **Concept extraction** — pull the most salient terms from a sample of
   memories, weighted by importance.
2. **Connection discovery** — find semantic bridges between concepts using
   HDDR similarity.
3. **Synthesis narrative** — compose a human-readable synthesis sentence
   describing the emergent understanding.
4. **Identity-framing** — optionally frame the synthesis relative to the
   user's identity anchor.
5. **Novelty scoring** — estimate how creative/novel the synthesis is (higher
   when connections are moderate rather than obvious).

The engine deliberately avoids large language models so it works with zero
external dependencies beyond ``numpy`` (which is only used for optional
extensions).  All synthesis is rule-based recombination of existing memories,
which mirrors classical theories of creative cognition (e.g. Mednick's
Remote Associates theory).
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class SelfSynthesisEngine:
    """
    Self-synthesis engine — generates novel ideas from existing memories.

    Usage::

        engine = SelfSynthesisEngine(memory=episodic_memory, identity_anchor=anchor)
        result = engine.synthesize(seed="gravity attention")
        print(result["synthesis"])
    """

    _STOPWORDS = frozenset(
        [
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "will", "would", "could", "should", "and",
            "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "from", "this", "that", "it", "its", "as", "so", "if", "not",
            "then", "than", "more", "less", "very", "also", "just", "about",
        ]
    )

    def __init__(self, memory=None, identity_anchor=None):
        """
        Args:
            memory: An :class:`~nexusforge.memory.episodic_memory.EpisodicMemory`
                instance to draw from.
            identity_anchor: Optional
                :class:`~nexusforge.memory.identity_anchor.IdentityAnchor`
                used to frame the synthesis.
        """
        self.memory = memory
        self.identity_anchor = identity_anchor
        self._history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        seed: Optional[str] = None,
        depth: int = 2,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Synthesize novel ideas from memory.

        Args:
            seed: Optional concept to focus retrieval (e.g. ``"gravity"``).
            depth: Number of inference hops (currently used for connection
                depth; reserved for future multi-hop reasoning).
            top_k: How many memories to use as raw material.

        Returns:
            A dictionary with keys:
            ``timestamp``, ``seed``, ``source_memory_count``,
            ``concepts``, ``connections``, ``synthesis``,
            ``identity_context``, ``novel_score``.
        """
        if not self.memory:
            return self._empty_result(seed, "No memory system attached")

        # Fetch source memories
        if seed:
            sources = self.memory.recall(seed, top_k=top_k)
        else:
            sources = self.memory.get_recent(n=top_k)

        if not sources:
            return self._empty_result(seed, "No memories available for synthesis")

        concepts = self._extract_concepts(sources)
        connections = self._find_connections(concepts, depth)
        synthesis = self._generate_synthesis(concepts, connections, seed)
        identity_context = self._apply_identity_context(synthesis)

        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "source_memory_count": len(sources),
            "concepts": concepts[:10],
            "connections": [
                {"a": a, "b": b, "strength": round(s, 3)}
                for a, b, s in connections[:5]
            ],
            "synthesis": synthesis,
            "identity_context": identity_context,
            "novel_score": round(self._novelty_score(connections), 3),
        }
        self._history.append(result)
        return result

    def infer(self, statement: str) -> Dict[str, Any]:
        """
        Self-inference: given a statement, what does the agent already know
        that is relevant, and what new insight can it draw?

        This is a lightweight version of :meth:`synthesize` focused on a
        single query rather than free exploration.
        """
        return self.synthesize(seed=statement, depth=1, top_k=3)

    def get_synthesis_history(self) -> List[Dict[str, Any]]:
        """Return the last 20 synthesis results."""
        return self._history[-20:]

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _extract_concepts(self, memories) -> List[str]:
        """Extract the most salient concepts from a list of MemoryEpisodes."""
        freq: Dict[str, float] = {}
        for ep in memories:
            words = re.findall(r"\b[a-zA-Z][a-zA-Z]+\b", str(ep.content))
            for w in words:
                wl = w.lower()
                if wl not in self._STOPWORDS and len(wl) > 3:
                    # Importance-weighted frequency
                    freq[wl] = freq.get(wl, 0.0) + ep.importance

        sorted_concepts = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [c for c, _ in sorted_concepts[:20]]

    def _find_connections(
        self,
        concepts: List[str],
        depth: int = 2,
    ) -> List[Tuple[str, str, float]]:
        """
        Discover semantic connections between concept pairs.

        A "strong" connection (≥ 0.7) means both concepts appear in the same
        memory.  A "weak" connection (0.3–0.7) means their memory embeddings
        are moderately similar — the creative sweet-spot.
        """
        if not self.memory:
            return []

        connections: List[Tuple[str, str, float]] = []

        for i in range(min(len(concepts), 10)):
            for j in range(i + 1, min(len(concepts), 10)):
                ca, cb = concepts[i], concepts[j]

                mems_a = self.memory.recall(ca, top_k=3)
                mems_b = self.memory.recall(cb, top_k=3)
                if not mems_a or not mems_b:
                    continue

                # Check for co-occurrence in the same memory
                for ma in mems_a:
                    if cb in str(ma.content).lower():
                        connections.append((ca, cb, 0.9))
                        break
                else:
                    # Embedding similarity
                    if mems_a[0].embedding and mems_b[0].embedding:
                        sim = self.memory.hddr.similarity(
                            mems_a[0].embedding, mems_b[0].embedding
                        )
                        if sim > 0.25:
                            connections.append((ca, cb, sim))

        connections.sort(key=lambda x: x[2], reverse=True)
        return connections

    def _generate_synthesis(
        self,
        concepts: List[str],
        connections: List[Tuple[str, str, float]],
        seed: Optional[str],
    ) -> str:
        """Compose a human-readable synthesis from concepts and connections."""
        if not concepts:
            return "Insufficient concepts available for synthesis."

        parts: List[str] = []

        if seed:
            parts.append(f"Synthesising around '{seed}':")

        if len(concepts) >= 3:
            parts.append(f"Core themes: {', '.join(concepts[:3])}.")

        if connections:
            a, b, strength = connections[0]
            adverb = "strongly" if strength > 0.7 else "moderately"
            parts.append(f"'{a}' and '{b}' are {adverb} connected.")

        novel = self._novel_combination(concepts, connections)
        if novel:
            parts.append(f"Novel synthesis: {novel}")

        return " ".join(parts) if parts else "No synthesis generated."

    def _novel_combination(
        self,
        concepts: List[str],
        connections: List[Tuple[str, str, float]],
    ) -> Optional[str]:
        """
        Generate an emergent concept by combining existing ones.

        Moderate-strength connections (0.3–0.7) are the most creative —
        the concepts are related enough to be bridged but different enough
        to produce genuine novelty.
        """
        for a, b, strength in connections:
            if 0.3 < strength < 0.7:
                prefix = a[:3]
                suffix = b[-3:]
                return (
                    f"The intersection of '{a}' and '{b}' suggests "
                    f"emergent '{prefix}{suffix}' dynamics."
                )

        if len(concepts) >= 2:
            return (
                f"Viewing '{concepts[0]}' through the lens of '{concepts[1]}' "
                f"yields a new perspective."
            )

        return None

    def _apply_identity_context(self, synthesis: str) -> str:
        """Annotate the synthesis with its alignment to the identity anchor."""
        if not self.identity_anchor or not self.identity_anchor.is_configured():
            return synthesis

        alignment = self.identity_anchor.compute_alignment(synthesis)
        if alignment > 0.3:
            return f"[Identity-aligned] {synthesis}"
        if alignment < -0.3:
            return f"[Identity-divergent — review carefully] {synthesis}"
        return synthesis

    def _novelty_score(self, connections: List[Tuple[str, str, float]]) -> float:
        """
        Estimate how novel/creative a synthesis is.

        Higher when there are many moderate-strength connections (creative
        sweet-spot) relative to total connections.
        """
        if not connections:
            return 0.0
        moderate = sum(1 for _, _, s in connections if 0.2 < s < 0.7)
        base = moderate / len(connections)
        diversity_bonus = min(0.3, len(connections) * 0.03)
        return min(1.0, base + diversity_bonus)

    @staticmethod
    def _empty_result(seed: Optional[str], reason: str) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "seed": seed,
            "source_memory_count": 0,
            "concepts": [],
            "connections": [],
            "synthesis": reason,
            "identity_context": reason,
            "novel_score": 0.0,
        }

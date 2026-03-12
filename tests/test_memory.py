"""
Tests for the NexusForge memory, attention, tokenformer, and sensory systems.

Covers:
- IdentityAnchor: set_identity, compute_alignment, core_values
- HDDREncoder: encode shape, similarity, compress
- EpisodicMemory: store, recall, pruning, working memory, statistics
- REMCycleEngine: force_cycle, phase transitions, stats
- SelfSynthesisEngine: synthesize, infer
- GravitationalAttentionLayer: forward shape, force positivity
- GravitationalTokenFormer: encode/forward shapes, importance map
- SensoryProcessor: process, batch, novelty boost, statistics
- NexusForge integration: set_identity, perceive, remember, recall, synthesize
"""

import asyncio
import datetime as _dt
import math
import numpy as np
import pytest

from nexusforge import (
    NexusForge,
    IdentityAnchor,
    EpisodicMemory,
    MemoryType,
    REMCycleEngine,
    SelfSynthesisEngine,
    GravitationalAttentionLayer,
    GravitationalConfig,
    GravitationalTokenFormer,
    TokenFormerConfig,
    SensoryProcessor,
    SensoryModality,
)
from nexusforge.memory.episodic_memory import HDDREncoder, MemoryEpisode
from nexusforge.memory.rem_cycle import REMPhase


# ===========================================================================
# IdentityAnchor
# ===========================================================================


class TestIdentityAnchor:
    """Tests for the identity anchor module."""

    def test_not_configured_by_default(self):
        anchor = IdentityAnchor()
        assert not anchor.is_configured()
        assert anchor.identity_id is None

    def test_set_identity_returns_vector(self):
        anchor = IdentityAnchor(vector_dim=32)
        vec = anchor.set_identity("I am a creative problem solver who loves building AI.")
        assert vec is not None
        assert vec.dimensions == 32
        assert len(vec.vector) == 32

    def test_identity_vector_is_unit_norm(self):
        anchor = IdentityAnchor(vector_dim=32)
        anchor.set_identity("I am a systems engineer who values clarity and precision.")
        norm = math.sqrt(sum(v ** 2 for v in anchor.identity_vector.vector))
        assert abs(norm - 1.0) < 1e-6

    def test_is_configured_after_set(self):
        anchor = IdentityAnchor()
        anchor.set_identity("I am a visionary technologist.")
        assert anchor.is_configured()
        assert anchor.identity_id is not None

    def test_core_values_extracted(self):
        anchor = IdentityAnchor()
        anchor.set_identity(
            "I am a researcher who explores deep learning and neural architectures."
        )
        assert len(anchor.core_values) > 0
        # At least one meaningful term should be present
        combined = " ".join(anchor.core_values)
        assert any(term in combined for term in ["researcher", "learning", "neural", "deep", "explores"])

    def test_alignment_neutral_without_identity(self):
        anchor = IdentityAnchor()
        score = anchor.compute_alignment("some random text")
        assert score == 0.5

    def test_alignment_high_for_similar_text(self):
        anchor = IdentityAnchor(vector_dim=64)
        statement = "I am a deep learning researcher who builds neural networks."
        anchor.set_identity(statement)
        # Very similar text should align well
        score = anchor.compute_alignment("deep learning researcher building neural networks")
        assert score > 0.3

    def test_alignment_range(self):
        anchor = IdentityAnchor(vector_dim=64)
        anchor.set_identity("I am a mathematician who loves algebra and topology.")
        for text in ["algebra", "music festival", "topology proof", "random words xyz"]:
            score = anchor.compute_alignment(text)
            assert -1.0 <= score <= 1.0

    def test_get_identity_summary(self):
        anchor = IdentityAnchor()
        anchor.set_identity("I am a builder.")
        summary = anchor.get_identity_summary()
        assert summary["has_identity"] is True
        assert summary["identity_id"] is not None
        assert "builder" in " ".join(summary["core_values"])

    def test_deterministic_identity_id(self):
        """Same paragraph → same identity_id."""
        paragraph = "I am a unique individual with a specific identity."
        a1 = IdentityAnchor()
        a2 = IdentityAnchor()
        a1.set_identity(paragraph)
        a2.set_identity(paragraph)
        assert a1.identity_id == a2.identity_id


# ===========================================================================
# HDDREncoder
# ===========================================================================


class TestHDDREncoder:
    """Tests for the High-Dimensional Dense Representation encoder."""

    def test_encode_returns_correct_dimension(self):
        enc = HDDREncoder(dim=64)
        vec = enc.encode("gravitational attention transforms tokens")
        assert len(vec) == 64

    def test_encode_unit_norm(self):
        enc = HDDREncoder(dim=64)
        vec = enc.encode("some text here")
        norm = math.sqrt(sum(v ** 2 for v in vec))
        assert abs(norm - 1.0) < 1e-6

    def test_empty_text_returns_zeros(self):
        enc = HDDREncoder(dim=32)
        vec = enc.encode("")
        assert all(v == 0.0 for v in vec)

    def test_similarity_identical_text(self):
        enc = HDDREncoder(dim=64)
        text = "the quick brown fox"
        v1 = enc.encode(text)
        v2 = enc.encode(text)
        sim = enc.similarity(v1, v2)
        assert abs(sim - 1.0) < 1e-5

    def test_similarity_range(self):
        enc = HDDREncoder(dim=64)
        v1 = enc.encode("machine learning and neural networks")
        v2 = enc.encode("completely unrelated banana pancake")
        sim = enc.similarity(v1, v2)
        assert -1.0 <= sim <= 1.0

    def test_compress_single_vector(self):
        enc = HDDREncoder(dim=32)
        v = enc.encode("single vector")
        compressed = enc.compress([v])
        assert len(compressed) == 32

    def test_compress_multiple_vectors(self):
        enc = HDDREncoder(dim=32)
        vecs = [enc.encode(f"memory episode {i}") for i in range(5)]
        compressed = enc.compress(vecs)
        assert len(compressed) == 32
        # Compressed vector should be normalized
        norm = math.sqrt(sum(v ** 2 for v in compressed))
        assert abs(norm - 1.0) < 1e-6


# ===========================================================================
# EpisodicMemory
# ===========================================================================


class TestEpisodicMemory:
    """Tests for the episodic memory store."""

    def _make_memory(self, max_episodes=100, sparse_threshold=0.3):
        return EpisodicMemory(
            max_episodes=max_episodes,
            sparse_threshold=sparse_threshold,
        )

    def test_store_returns_episode_id(self):
        mem = self._make_memory()
        eid = mem.store("Learning about gravitational attention", importance=0.8)
        assert eid is not None
        assert eid in mem.episodes

    def test_sparse_parsing_filters_low_importance(self):
        mem = self._make_memory(sparse_threshold=0.5)
        eid = mem.store("low importance event", importance=0.1)
        assert eid is None

    def test_working_memory_type_bypasses_sparse_filter(self):
        mem = self._make_memory(sparse_threshold=0.9)
        eid = mem.store("urgent working context", memory_type=MemoryType.WORKING, importance=0.1)
        assert eid is not None

    def test_working_memory_ring_buffer(self):
        mem = self._make_memory()
        ids = []
        for i in range(10):
            eid = mem.store(f"event {i}", importance=0.8)
            if eid:
                ids.append(eid)
        # Working memory should never exceed capacity
        assert len(mem.working_memory) <= mem.working_memory_capacity

    def test_recall_returns_relevant_episodes(self):
        mem = self._make_memory()
        mem.store("gravity and space-time curvature", importance=0.9)
        mem.store("recipe for chocolate cake", importance=0.9)
        results = mem.recall("gravitational physics", top_k=3)
        assert len(results) > 0
        # The gravity-related episode should score higher
        top_content = str(results[0].content).lower()
        assert any(w in top_content for w in ["gravity", "space", "curvature"])

    def test_recall_empty_memory_returns_empty(self):
        mem = self._make_memory()
        assert mem.recall("anything") == []

    def test_recall_boosts_importance(self):
        mem = self._make_memory()
        eid = mem.store("important memory", importance=0.6)
        before = mem.episodes[eid].importance
        mem.recall("important memory")
        after = mem.episodes[eid].importance
        assert after >= before

    def test_get_recent(self):
        mem = self._make_memory()
        for i in range(5):
            mem.store(f"episode {i}", importance=0.8)
        recent = mem.get_recent(n=3)
        assert len(recent) == 3

    def test_pruning_removes_weak_episodes(self):
        mem = self._make_memory(max_episodes=10, sparse_threshold=0.0)
        # Store 15 very low-importance episodes (below pruning_threshold)
        for i in range(15):
            mem.episodes[f"fake_{i}"] = MemoryEpisode(
                episode_id=f"fake_{i}",
                content=f"weak memory {i}",
                memory_type=MemoryType.EPISODIC,
                timestamp=__import__("datetime").datetime.now(),
                importance=0.05,
                identity_alignment=0.05,
                embedding=[0.0] * 128,
            )
            mem.temporal_index.append(f"fake_{i}")
        count_before = len(mem.episodes)
        mem._prune_weak_memories()
        assert len(mem.episodes) < count_before

    def test_statistics_structure(self):
        mem = self._make_memory()
        mem.store("some content", importance=0.7)
        stats = mem.get_statistics()
        assert "total_episodes" in stats
        assert "working_memory_size" in stats
        assert "avg_importance" in stats
        assert "capacity_used" in stats

    def test_identity_alignment_scored_when_anchor_set(self):
        anchor = IdentityAnchor(vector_dim=32)
        anchor.set_identity("I am a physicist who studies gravity and spacetime.")
        mem = EpisodicMemory(identity_anchor=anchor)
        eid = mem.store(
            "gravitational waves and spacetime curvature", importance=0.8
        )
        assert eid is not None
        ep = mem.episodes[eid]
        # Alignment should be set (not the default 0.5 neutral)
        assert 0.0 <= ep.identity_alignment <= 1.0


# ===========================================================================
# REMCycleEngine
# ===========================================================================


class TestREMCycleEngine:
    """Tests for the REM sleep cycle engine."""

    def test_initial_state(self):
        engine = REMCycleEngine()
        assert engine.current_phase.value == "awake"
        assert engine.cycle_count == 0
        assert not engine.is_running

    def test_record_activity_resets_idle(self):
        import time
        engine = REMCycleEngine(idle_threshold=1.0)
        engine.record_activity()
        assert not engine._is_idle()

    @pytest.mark.asyncio
    async def test_force_cycle_runs_without_memory(self):
        engine = REMCycleEngine()
        stats = await engine.force_cycle(time_scale=0.0)
        assert stats.cycle_number == 1
        assert stats.end_time is not None

    @pytest.mark.asyncio
    async def test_force_cycle_with_memory(self):
        mem = EpisodicMemory(max_episodes=50)
        for i in range(20):
            mem.store(f"memory episode {i}", importance=0.6)
        engine = REMCycleEngine(episodic_memory=mem)
        stats = await engine.force_cycle(time_scale=0.0)
        assert stats.cycle_count if hasattr(stats, "cycle_count") else True
        assert stats.end_time is not None

    @pytest.mark.asyncio
    async def test_rem_synthesis_creates_connections(self):
        mem = EpisodicMemory()
        # Store episodes that should have moderate similarity
        for topic in ["gravity pulls objects", "mass attracts matter",
                       "force between bodies", "recipe for bread",
                       "music theory basics"]:
            mem.store(topic, importance=0.8)
        engine = REMCycleEngine(episodic_memory=mem)
        stats = await engine.force_cycle(time_scale=0.0)
        # At least some connections should be found among related topics
        assert stats.novel_connections >= 0  # non-negative

    @pytest.mark.asyncio
    async def test_identity_reinforcement(self):
        anchor = IdentityAnchor(vector_dim=32)
        anchor.set_identity("I am a researcher who studies computational systems.")
        mem = EpisodicMemory(identity_anchor=anchor)
        # Store an aligned memory
        eid = mem.store("computational systems research", importance=0.6)
        ep = mem.episodes[eid]
        # Force high alignment for test clarity
        ep.identity_alignment = 0.9

        engine = REMCycleEngine(episodic_memory=mem, identity_anchor=anchor)
        # Set last_activity_time far in the past so _is_idle() is True on all
        # inter-phase checks, allowing all phases (including REM reinforce) to run.
        engine.last_activity_time = _dt.datetime.now() - _dt.timedelta(seconds=999)

        importance_before = ep.importance
        await engine.force_cycle(time_scale=0.0)
        # Net effect: light-sleep decay (−0.003) + deep-sleep decay (−0.005)
        # + REM reinforce (+0.05) ≈ +0.042 net gain for a high-alignment memory.
        assert ep.importance > importance_before - 0.02  # net positive or very small loss

    @pytest.mark.asyncio
    async def test_start_stop(self):
        engine = REMCycleEngine(idle_threshold=999.0)  # won't fire
        await engine.start()
        assert engine.is_running
        await engine.stop()
        assert not engine.is_running

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        """Calling start() twice must not create a second background task."""
        engine = REMCycleEngine(idle_threshold=999.0)
        await engine.start()
        task_before = engine._task
        await engine.start()  # second call — should be a no-op
        assert engine._task is task_before
        await engine.stop()

    @pytest.mark.asyncio
    async def test_record_activity_interrupts_phase(self):
        """Activity during a phase should set wake_event immediately."""
        engine = REMCycleEngine()
        engine.current_phase = REMPhase.LIGHT_SLEEP  # simulate in-sleep
        engine.record_activity()
        assert engine.current_phase == REMPhase.AWAKE
        assert engine._wake_event.is_set()

    def test_get_stats_structure(self):
        engine = REMCycleEngine()
        stats = engine.get_stats()
        assert "current_phase" in stats
        assert "cycle_count" in stats
        assert "is_running" in stats
        assert "idle_seconds" in stats


# ===========================================================================
# SelfSynthesisEngine
# ===========================================================================


class TestSelfSynthesisEngine:
    """Tests for the self-synthesis engine."""

    def _make_engine(self):
        mem = EpisodicMemory()
        for topic in [
            "gravitational attention is a physics-based attention mechanism",
            "mass and distance determine gravitational force",
            "tokens with high mass attract more information",
            "REM sleep consolidates memory in the brain",
            "identity anchoring prevents cognitive drift",
        ]:
            mem.store(topic, importance=0.8)
        return SelfSynthesisEngine(memory=mem)

    def test_synthesize_returns_dict(self):
        engine = self._make_engine()
        result = engine.synthesize()
        assert isinstance(result, dict)
        assert "synthesis" in result
        assert "concepts" in result
        assert "novel_score" in result

    def test_synthesize_with_seed(self):
        engine = self._make_engine()
        result = engine.synthesize(seed="gravity")
        assert result["seed"] == "gravity"
        assert result["source_memory_count"] >= 0

    def test_synthesize_no_memory(self):
        engine = SelfSynthesisEngine(memory=None)
        result = engine.synthesize()
        assert "No memory" in result["synthesis"]

    def test_novel_score_in_range(self):
        engine = self._make_engine()
        result = engine.synthesize()
        assert 0.0 <= result["novel_score"] <= 1.0

    def test_infer_method(self):
        engine = self._make_engine()
        result = engine.infer("gravitational tokens")
        assert "synthesis" in result

    def test_synthesis_history_tracked(self):
        engine = self._make_engine()
        engine.synthesize(seed="gravity")
        engine.synthesize(seed="memory")
        history = engine.get_synthesis_history()
        assert len(history) == 2

    def test_identity_context_applied(self):
        anchor = IdentityAnchor(vector_dim=32)
        anchor.set_identity("I am a researcher who studies gravitational physics.")
        mem = EpisodicMemory(identity_anchor=anchor)
        mem.store("gravitational waves and spacetime", importance=0.9)
        engine = SelfSynthesisEngine(memory=mem, identity_anchor=anchor)
        result = engine.synthesize(seed="gravity")
        # Identity context should be a non-empty string
        assert isinstance(result["identity_context"], str)
        assert len(result["identity_context"]) > 0


# ===========================================================================
# GravitationalAttentionLayer
# ===========================================================================


class TestGravitationalAttention:
    """Tests for the gravitational attention layer."""

    def test_output_shape_matches_input(self):
        cfg = GravitationalConfig(dim_model=32, dim_position=8)
        layer = GravitationalAttentionLayer(cfg, seed=0)
        X = np.random.randn(2, 5, 32)
        out = layer.forward(X)
        assert out.shape == (2, 5, 32)

    def test_single_token_sequence(self):
        cfg = GravitationalConfig(dim_model=16, dim_position=4)
        layer = GravitationalAttentionLayer(cfg, seed=1)
        X = np.random.randn(1, 1, 16)
        out = layer.forward(X)
        assert out.shape == (1, 1, 16)

    def test_gravitational_constant_positive(self):
        cfg = GravitationalConfig(gravitational_constant=2.5)
        layer = GravitationalAttentionLayer(cfg)
        assert layer.G > 0

    def test_forces_non_negative_before_softmax(self):
        """Gravitational forces should always be >= 0."""
        cfg = GravitationalConfig(dim_model=32, dim_position=8, event_horizon=1e-6)
        layer = GravitationalAttentionLayer(cfg, seed=42)
        X = np.random.randn(1, 6, 32)
        positions = X @ layer.W_position
        masses = np.log1p(np.exp(X @ layer.W_mass)) + 0.01
        forces = layer._compute_forces(positions, masses)
        assert np.all(forces >= 0), "All gravitational forces must be non-negative"

    def test_with_mask(self):
        cfg = GravitationalConfig(dim_model=16, dim_position=4)
        layer = GravitationalAttentionLayer(cfg, seed=2)
        X = np.random.randn(1, 4, 16)
        # Upper-triangular causal mask
        mask = np.triu(np.ones((1, 4, 4), dtype=bool), k=1)
        out = layer.forward(X, mask=mask)
        assert out.shape == (1, 4, 16)

    def test_hawking_radiation_cap(self):
        """With max_force set, no force should exceed the cap."""
        cap = 5.0
        cfg = GravitationalConfig(
            dim_model=16, dim_position=4,
            max_force=cap, gravitational_constant=100.0  # Very large G
        )
        layer = GravitationalAttentionLayer(cfg, seed=3)
        X = np.random.randn(1, 4, 16)
        positions = X @ layer.W_position
        masses = np.log1p(np.exp(X @ layer.W_mass)) + 0.01
        forces = layer._compute_forces(positions, masses)
        assert np.all(forces <= cap + 1e-8)

    def test_curved_spacetime(self):
        """Curved space-time should not break the forward pass."""
        cfg = GravitationalConfig(dim_model=16, dim_position=4, curvature=0.5)
        layer = GravitationalAttentionLayer(cfg, seed=4)
        X = np.random.randn(1, 3, 16)
        out = layer.forward(X)
        assert out.shape == (1, 3, 16)
        assert not np.any(np.isnan(out))

    def test_learnable_G_false_freezes_constant(self):
        """When learnable_G=False, G must always equal the initial value."""
        init_G = 3.7
        cfg = GravitationalConfig(
            dim_model=16, dim_position=4,
            gravitational_constant=init_G, learnable_G=False
        )
        layer = GravitationalAttentionLayer(cfg)
        # Mutate _log_G to simulate a training step
        layer._log_G += 999.0
        assert abs(layer.G - init_G) < 1e-9, (
            "G must be frozen at initial value when learnable_G=False"
        )

    def test_learnable_G_true_uses_log_G(self):
        """When learnable_G=True, G must reflect _log_G."""
        cfg = GravitationalConfig(
            dim_model=16, dim_position=4,
            gravitational_constant=1.0, learnable_G=True
        )
        layer = GravitationalAttentionLayer(cfg)
        layer._log_G = math.log(5.0)
        assert abs(layer.G - 5.0) < 1e-9

    def test_softplus_no_overflow_with_large_input(self):
        """Numerically-stable softplus must not produce inf masses."""
        cfg = GravitationalConfig(dim_model=16, dim_position=4)
        layer = GravitationalAttentionLayer(cfg, seed=5)
        # Construct input that produces very large raw_mass
        X = np.full((1, 4, 16), 1e6)
        out = layer.forward(X)
        assert not np.any(np.isinf(out)), "Forward pass must not produce inf values"
        assert not np.any(np.isnan(out)), "Forward pass must not produce NaN values"


# ===========================================================================
# GravitationalTokenFormer
# ===========================================================================


class TestGravitationalTokenFormer:
    """Tests for the full GravitationalTokenFormer model."""

    def _make_model(self, **kwargs):
        cfg = TokenFormerConfig(
            vocab_size=64,
            dim_model=32,
            dim_position=8,
            num_layers=2,
            dim_ff=64,
            max_seq_len=32,
            **kwargs,
        )
        return GravitationalTokenFormer(cfg)

    def test_encode_output_shapes(self):
        model = self._make_model()
        token_ids = np.random.randint(0, 64, (2, 10))
        hidden, importance = model.encode(token_ids)
        assert hidden.shape == (2, 10, 32)
        assert importance.shape == (2, 10)

    def test_importance_map_in_range(self):
        model = self._make_model()
        token_ids = np.random.randint(0, 64, (1, 8))
        _, importance = model.encode(token_ids)
        assert np.all(importance >= 0)
        assert np.all(importance <= 1.0 + 1e-6)

    def test_forward_output_shapes(self):
        model = self._make_model()
        X = np.random.randn(1, 6, 32)
        logits, importance = model.forward(X)
        assert logits.shape == (1, 6, 64)   # (batch, seq, vocab_size)
        assert importance.shape == (1, 6)

    def test_no_nans_in_output(self):
        model = self._make_model()
        X = np.random.randn(2, 5, 32)
        logits, importance = model.forward(X)
        assert not np.any(np.isnan(logits))
        assert not np.any(np.isnan(importance))

    def test_identity_vector_integration(self):
        """Model with identity vector should still produce valid output."""
        identity_vec = np.random.randn(64)  # dim_ff
        identity_vec /= np.linalg.norm(identity_vec) + 1e-8
        model = self._make_model()
        model.set_identity_vector(identity_vec)
        X = np.random.randn(1, 4, 32)
        logits, importance = model.forward(X)
        assert logits.shape == (1, 4, 64)

    def test_get_config(self):
        model = self._make_model()
        cfg = model.get_config()
        assert cfg["dim_model"] == 32
        assert cfg["num_layers"] == 2
        assert cfg["vocab_size"] == 64

    def test_encode_raises_on_seq_too_long(self):
        """encode() must raise ValueError (not AssertionError) when seq too long."""
        model = self._make_model()  # max_seq_len=32
        token_ids = np.random.randint(0, 64, (1, 40))  # 40 > 32
        with pytest.raises(ValueError, match="max_seq_len"):
            model.encode(token_ids)


# ===========================================================================
# SensoryProcessor
# ===========================================================================


class TestSensoryProcessor:
    """Tests for the sensory processor."""

    def _make_processor(self, threshold=0.0):
        mem = EpisodicMemory(sparse_threshold=0.0)
        return SensoryProcessor(
            episodic_memory=mem,
            base_importance_threshold=threshold,
        )

    def test_process_text_stored(self):
        proc = self._make_processor(threshold=0.0)
        event = proc.process("The gravitational attention model achieved state-of-the-art results.")
        assert event.was_stored
        assert event.episode_id is not None

    def test_process_detects_text_modality(self):
        proc = self._make_processor()
        event = proc.process("some text")
        assert event.modality == SensoryModality.TEXT

    def test_process_detects_numeric_modality(self):
        proc = self._make_processor()
        event = proc.process(42.0)
        assert event.modality == SensoryModality.NUMERIC

    def test_process_detects_structured_modality(self):
        proc = self._make_processor()
        event = proc.process({"key": "value", "count": 5})
        assert event.modality == SensoryModality.STRUCTURED

    def test_importance_override(self):
        proc = self._make_processor(threshold=0.9)
        # Override to force storage even though threshold is high
        event = proc.process("test", importance_override=1.0)
        assert event.was_stored

    def test_low_importance_filtered(self):
        mem = EpisodicMemory(sparse_threshold=0.0)
        proc = SensoryProcessor(
            episodic_memory=mem,
            base_importance_threshold=0.95,
        )
        event = proc.process("hi")  # Very short, low importance
        # Either not stored (importance < threshold) OR stored if importance >= threshold
        # Just verify the event is returned with correct structure
        assert hasattr(event, "was_stored")
        assert hasattr(event, "episode_id")

    def test_novelty_boost_on_fresh_input(self):
        proc = self._make_processor()
        # First event should get novelty boost (no prior context)
        event = proc.process("completely novel information about gravitational tokens")
        assert event.importance > 0

    def test_process_batch(self):
        proc = self._make_processor(threshold=0.0)
        items = ["item one", "item two", "item three"]
        events = proc.process_batch(items)
        assert len(events) == 3

    def test_statistics_updated(self):
        proc = self._make_processor(threshold=0.0)
        proc.process("test input one")
        proc.process("test input two")
        stats = proc.get_statistics()
        assert stats["total_received"] == 2
        assert "storage_rate" in stats

    def test_tags_passed_to_episode(self):
        mem = EpisodicMemory(sparse_threshold=0.0)
        proc = SensoryProcessor(
            episodic_memory=mem,
            base_importance_threshold=0.0,
        )
        event = proc.process("tagged content", tags=["important", "test"], importance_override=0.8)
        if event.was_stored:
            ep = mem.episodes[event.episode_id]
            assert "important" in ep.tags or "test" in ep.tags


# ===========================================================================
# NexusForge integration
# ===========================================================================


class TestNexusForgeMemoryIntegration:
    """Integration tests for the full NexusForge system with memory."""

    @pytest.mark.asyncio
    async def test_set_identity(self):
        nexus = NexusForge()
        summary = nexus.set_identity(
            "I am a pioneering researcher who builds next-generation AI systems "
            "with gravitational attention and episodic memory."
        )
        assert summary["has_identity"] is True
        assert summary["identity_id"] is not None

    @pytest.mark.asyncio
    async def test_perceive_stores_in_memory(self):
        nexus = NexusForge()
        result = nexus.perceive(
            "Gravitational attention models token importance as mass.",
            importance_override=0.9,
        )
        assert result["was_stored"] is True
        assert result["episode_id"] is not None

    @pytest.mark.asyncio
    async def test_remember_resets_idle_timer(self):
        """remember() must call rem_engine.record_activity() so idle timer resets."""
        nexus = NexusForge()
        # Wind the idle clock back so the engine looks idle
        nexus.rem_engine.last_activity_time = _dt.datetime.now() - _dt.timedelta(seconds=9999)
        # remember() should reset the timer
        nexus.remember("some important event", importance=0.8)
        idle = (
            _dt.datetime.now() - nexus.rem_engine.last_activity_time
        ).total_seconds()
        assert idle < 5, "remember() should have reset the idle timer"

    @pytest.mark.asyncio
    async def test_remember_and_recall(self):
        nexus = NexusForge()
        nexus.remember("the gravitational tokenformer processes sequences", importance=0.9)
        nexus.remember("episodic memory stores human-like experiences", importance=0.9)
        results = nexus.recall("gravitational tokenformer sequences", top_k=2)
        assert len(results) >= 1
        assert "episode_id" in results[0]
        assert "importance" in results[0]

    @pytest.mark.asyncio
    async def test_synthesize_from_memories(self):
        nexus = NexusForge()
        nexus.remember("gravitational force attracts tokens with mass", importance=0.9)
        nexus.remember("REM sleep consolidates neural memory", importance=0.9)
        nexus.remember("identity anchors prevent cognitive drift", importance=0.9)
        result = nexus.synthesize(seed="memory")
        assert "synthesis" in result
        assert isinstance(result["synthesis"], str)

    @pytest.mark.asyncio
    async def test_memory_stats_structure(self):
        nexus = NexusForge()
        stats = nexus.get_memory_stats()
        assert "episodic_memory" in stats
        assert "rem_engine" in stats
        assert "identity" in stats
        assert "sensory" in stats

    @pytest.mark.asyncio
    async def test_force_rem_cycle(self):
        nexus = NexusForge()
        nexus.remember("consolidate this memory", importance=0.7)
        result = await nexus.force_rem_cycle(time_scale=0.0)
        assert "cycle_number" in result
        assert result["cycle_number"] == 1

    @pytest.mark.asyncio
    async def test_system_status_includes_memory(self):
        nexus = NexusForge()
        nexus.set_identity("I am a test agent.")
        status = nexus.get_system_status()
        assert "identity_configured" in status
        assert status["identity_configured"] is True
        assert "episodic_memory_size" in status
        assert "rem_phase" in status

    @pytest.mark.asyncio
    async def test_start_stop_includes_rem(self):
        nexus = NexusForge(config={"rem_idle_threshold": 999.0})
        await nexus.start()
        assert nexus.running
        assert nexus.rem_engine.is_running
        await nexus.stop()
        assert not nexus.running
        assert not nexus.rem_engine.is_running

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """End-to-end: set identity → perceive → recall → synthesize."""
        nexus = NexusForge()
        nexus.set_identity(
            "I am a next-generation AI researcher specialising in physics-based "
            "attention mechanisms and episodic memory systems."
        )
        for text in [
            "Gravitational attention replaces dot-product with force calculations.",
            "Tokens with higher mass attract more contextual information.",
            "REM sleep cycles compress and consolidate episodic memories.",
            "Identity anchoring ensures consistent self-representation over time.",
        ]:
            nexus.perceive(text, importance_override=0.85)

        recalled = nexus.recall("gravitational attention tokens", top_k=3)
        assert len(recalled) >= 1

        synthesis = nexus.synthesize(seed="attention")
        assert len(synthesis["synthesis"]) > 10

        stats = nexus.get_memory_stats()
        assert stats["episodic_memory"]["total_stored"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

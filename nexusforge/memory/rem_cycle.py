"""
REM Sleep Cycle Engine — Identity-anchored memory consolidation and compression.

When the NexusForge system has been idle longer than ``IDLE_THRESHOLD_SECONDS``,
the REM engine wakes up and runs a four-phase sleep cycle:

Phase 1 – **Light Sleep (N1)**  — memory sorting, mild decay applied.
Phase 2 – **Deep Sleep (N2/N3)** — slow-wave consolidation: prune weak
    memories, compress old episodes (replacing full content with a short
    summary while preserving the HDDR embedding).
Phase 3 – **REM** — active synthesis: find novel connections between
    semantically adjacent memories, reinforce identity-aligned episodes.
Phase 4 – **Returning** — short transition back to awake state.

Activity detected during any phase interrupts the cycle immediately by
signalling a ``asyncio.Event``, so the wait on each phase's sleep unblocks
without having to wait for the full phase duration.  All phase durations are
intentionally short (seconds, not 90-minute biological cycles) so the digital
agent consolidates frequently.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class REMPhase(Enum):
    """Current phase of the sleep–wake cycle."""

    AWAKE = "awake"
    LIGHT_SLEEP = "light_sleep"
    DEEP_SLEEP = "deep_sleep"
    REM = "rem"
    RETURNING = "returning"


@dataclass
class REMCycleStats:
    """Statistics captured during a single REM cycle run."""

    cycle_number: int
    start_time: datetime
    end_time: Optional[datetime]
    phase: REMPhase
    memories_consolidated: int = 0
    memories_pruned: int = 0
    memories_compressed: int = 0
    novel_connections: int = 0
    identity_reinforcements: int = 0


class REMCycleEngine:
    """
    REM Sleep Cycle Engine.

    Runs as a background ``asyncio`` task.  When idle for
    ``IDLE_THRESHOLD_SECONDS`` seconds it executes a compressed sleep cycle
    that consolidates, compresses, and synthesises memories.

    Args:
        episodic_memory: An :class:`~nexusforge.memory.episodic_memory.EpisodicMemory`
            instance to operate on.
        identity_anchor: An :class:`~nexusforge.memory.identity_anchor.IdentityAnchor`
            used to guide identity-locked pruning.
        idle_threshold: Seconds of inactivity before a cycle begins
            (default 30 s).
    """

    # Phase durations (seconds) — short for a digital agent
    PHASE_DURATIONS: Dict[REMPhase, float] = {
        REMPhase.LIGHT_SLEEP: 5.0,
        REMPhase.DEEP_SLEEP: 10.0,
        REMPhase.REM: 8.0,
        REMPhase.RETURNING: 2.0,
    }

    def __init__(
        self,
        episodic_memory=None,
        identity_anchor=None,
        idle_threshold: float = 30.0,
    ):
        self.memory = episodic_memory
        self.identity_anchor = identity_anchor
        self.idle_threshold = idle_threshold

        self.current_phase = REMPhase.AWAKE
        self.cycle_count = 0
        self.last_activity_time = datetime.now()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # Event used to interrupt phase sleeps immediately when activity occurs
        self._wake_event: asyncio.Event = asyncio.Event()

        self.cycle_history: List[REMCycleStats] = []
        self.logger = logging.getLogger("REMCycleEngine")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background idle-monitoring loop.

        Safe to call multiple times — a second call while already running
        is a no-op (the existing task is kept).  If ``is_running`` is stale
        (task finished abnormally without ``stop()`` being called), the state
        is corrected and a fresh task is started.
        """
        task_alive = self._task is not None and not self._task.done()
        if self.is_running and task_alive:
            self.logger.warning("REM cycle engine is already running; ignoring start()")
            return
        # Correct potentially stale is_running flag before (re)starting
        self.is_running = True
        self._wake_event.clear()
        self._task = asyncio.create_task(self._monitor_loop())
        self.logger.info("REM cycle engine started")

    async def stop(self) -> None:
        """Stop the background loop gracefully."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("REM cycle engine stopped")

    # ------------------------------------------------------------------
    # Activity tracking
    # ------------------------------------------------------------------

    def record_activity(self) -> None:
        """
        Notify the engine that the system is active.

        Resets the idle timer and, if currently sleeping, signals the wake
        event so any in-progress phase sleep is interrupted immediately rather
        than waiting for the phase duration to expire.
        """
        self.last_activity_time = datetime.now()
        if self.current_phase != REMPhase.AWAKE:
            self._wake_event.set()  # unblocks _phase_sleep() immediately
            self._wake_up()

    # ------------------------------------------------------------------
    # Public triggers
    # ------------------------------------------------------------------

    async def force_cycle(self, *, time_scale: float = 1.0) -> REMCycleStats:
        """
        Immediately trigger a full sleep cycle regardless of idle state.

        Useful for testing or explicit memory consolidation requests.

        Args:
            time_scale: Multiplier applied to all phase durations.  Pass
                ``0.0`` (or any value near zero) to skip real-time sleeping
                entirely — phases execute instantly, which is useful for fast,
                deterministic tests.
        """
        return await self._run_sleep_cycle(time_scale=time_scale)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return a summary of REM engine state and cycle history."""
        last = None
        if self.cycle_history:
            lc = self.cycle_history[-1]
            last = {
                "cycle_number": lc.cycle_number,
                "memories_pruned": lc.memories_pruned,
                "memories_compressed": lc.memories_compressed,
                "novel_connections": lc.novel_connections,
                "identity_reinforcements": lc.identity_reinforcements,
            }
        return {
            "current_phase": self.current_phase.value,
            "cycle_count": self.cycle_count,
            "is_running": self.is_running,
            "idle_seconds": (datetime.now() - self.last_activity_time).total_seconds(),
            "last_cycle": last,
        }

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    async def _monitor_loop(self) -> None:
        """Poll for idle state every 5 seconds and trigger sleep when ready."""
        while self.is_running:
            try:
                await asyncio.sleep(5)
                if self.current_phase == REMPhase.AWAKE and self._is_idle():
                    await self._run_sleep_cycle()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("REM monitor error: %s", exc)

    async def _phase_sleep(self, duration: float, time_scale: float) -> None:
        """
        Sleep for ``duration * time_scale`` seconds, but wake immediately if
        ``_wake_event`` is set (i.e. activity was detected mid-phase).
        """
        scaled = duration * time_scale
        if scaled <= 0:
            return
        self._wake_event.clear()
        try:
            await asyncio.wait_for(self._wake_event.wait(), timeout=scaled)
        except asyncio.TimeoutError:
            pass  # Normal case: full phase duration elapsed without activity

    async def _run_sleep_cycle(self, *, time_scale: float = 1.0) -> REMCycleStats:
        """Execute a complete four-phase sleep cycle."""
        self.cycle_count += 1
        stats = REMCycleStats(
            cycle_number=self.cycle_count,
            start_time=datetime.now(),
            end_time=None,
            phase=REMPhase.LIGHT_SLEEP,
        )
        self.logger.info("Starting REM cycle #%d", self.cycle_count)

        # --- Phase 1: Light Sleep ---
        self.current_phase = REMPhase.LIGHT_SLEEP
        stats.phase = REMPhase.LIGHT_SLEEP
        if self.memory:
            self._light_sleep_decay()
        await self._phase_sleep(self.PHASE_DURATIONS[REMPhase.LIGHT_SLEEP], time_scale)
        if not self._is_idle():
            return self._complete_cycle(stats)

        # --- Phase 2: Deep Sleep ---
        self.current_phase = REMPhase.DEEP_SLEEP
        stats.phase = REMPhase.DEEP_SLEEP
        if self.memory:
            stats.memories_pruned = self._deep_sleep_consolidation()
            stats.memories_compressed = self._compress_old_memories()
        await self._phase_sleep(self.PHASE_DURATIONS[REMPhase.DEEP_SLEEP], time_scale)
        if not self._is_idle():
            return self._complete_cycle(stats)

        # --- Phase 3: REM ---
        self.current_phase = REMPhase.REM
        stats.phase = REMPhase.REM
        stats.novel_connections = self._rem_synthesis()
        stats.identity_reinforcements = self._reinforce_identity()
        await self._phase_sleep(self.PHASE_DURATIONS[REMPhase.REM], time_scale)

        # --- Phase 4: Returning ---
        self.current_phase = REMPhase.RETURNING
        await self._phase_sleep(self.PHASE_DURATIONS[REMPhase.RETURNING], time_scale)

        self.current_phase = REMPhase.AWAKE
        return self._complete_cycle(stats)

    # ------------------------------------------------------------------
    # Phase implementations
    # ------------------------------------------------------------------

    def _light_sleep_decay(self) -> None:
        """Apply gentle forgetting-curve decay to all stored episodes."""
        for ep in self.memory.episodes.values():
            ep.decay(rate=0.003)

    def _deep_sleep_consolidation(self) -> int:
        """
        Prune weak memories and apply stronger decay.

        Returns the number of pruned episodes.
        """
        if not self.memory or not self.memory.episodes:
            return 0

        # Stronger decay during deep sleep
        for ep in self.memory.episodes.values():
            ep.decay(rate=0.005)

        before = len(self.memory.episodes)
        self.memory._prune_weak_memories()
        pruned = before - len(self.memory.episodes)
        if pruned:
            self.logger.info("Deep sleep: pruned %d memories", pruned)
        return pruned

    def _compress_old_memories(self) -> int:
        """
        Compress episodes older than 7 days with importance < 0.7.

        Compression truncates ``ep.content`` to a short summary string and sets
        ``ep.is_compressed = True``.  The HDDR embedding is preserved intact so
        the episode remains searchable via semantic recall even after its full
        content is reduced.

        Returns the number of episodes compressed.
        """
        if not self.memory or not self.memory.episodes:
            return 0

        threshold_date = datetime.now() - timedelta(days=7)
        working_set = set(self.memory.working_memory)
        compressed = 0

        for ep in self.memory.episodes.values():
            if (
                not ep.is_compressed
                and ep.timestamp < threshold_date
                and ep.importance < 0.7
                and ep.episode_id not in working_set
            ):
                content_str = str(ep.content)
                if len(content_str) > 100:
                    summary = content_str[:80] + "… [compressed]"
                    ep.compression_summary = summary
                    ep.content = summary   # replace full content with summary
                    ep.is_compressed = True
                    compressed += 1

        if compressed:
            self.logger.info("Compressed %d old memories", compressed)
        return compressed

    def _rem_synthesis(self) -> int:
        """
        Discover novel connections between semantically related memories.

        Pairs whose HDDR similarity falls in the "creative sweet spot"
        (0.2–0.6) are tagged as connected — semantically adjacent but not
        identical, which is the fertile ground for emergent ideas.

        Returns the number of novel connection pairs found.
        """
        if not self.memory or len(self.memory.episodes) < 2:
            return 0

        episodes = list(self.memory.episodes.values())
        # Cap at 30 to keep O(n²) manageable
        episodes = episodes[:30]
        novel = 0

        for i in range(len(episodes)):
            for j in range(i + 1, len(episodes)):
                ep_a, ep_b = episodes[i], episodes[j]
                if not (ep_a.embedding and ep_b.embedding):
                    continue
                sim = self.memory.hddr.similarity(ep_a.embedding, ep_b.embedding)
                if 0.2 < sim < 0.6:
                    tag_ab = f"rem_link:{ep_b.episode_id[:8]}"
                    tag_ba = f"rem_link:{ep_a.episode_id[:8]}"
                    if tag_ab not in ep_a.tags:
                        ep_a.tags.append(tag_ab)
                    if tag_ba not in ep_b.tags:
                        ep_b.tags.append(tag_ba)
                    novel += 1

        if novel:
            self.logger.info("REM synthesis: %d novel connections", novel)
        return novel

    def _reinforce_identity(self) -> int:
        """
        Reinforce identity-aligned memories and weaken counter-aligned ones.

        * identity_alignment > 0.7 → importance += 0.05
        * identity_alignment < 0.2 → importance -= 0.05

        Returns the number of reinforced episodes.
        """
        if not self.memory or not self.identity_anchor:
            return 0
        if not self.identity_anchor.is_configured():
            return 0

        reinforced = 0
        for ep in self.memory.episodes.values():
            if ep.identity_alignment > 0.7:
                ep.importance = min(1.0, ep.importance + 0.05)
                reinforced += 1
            elif ep.identity_alignment < 0.2:
                ep.importance = max(0.0, ep.importance - 0.05)

        return reinforced

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_idle(self) -> bool:
        idle = (datetime.now() - self.last_activity_time).total_seconds()
        return idle >= self.idle_threshold

    def _wake_up(self) -> None:
        self.current_phase = REMPhase.AWAKE
        self.logger.info("REM cycle interrupted — returning to awake state")

    def _complete_cycle(self, stats: REMCycleStats) -> REMCycleStats:
        stats.end_time = datetime.now()
        self.cycle_history.append(stats)
        # Keep only the last 100 cycle records
        if len(self.cycle_history) > 100:
            self.cycle_history.pop(0)
        duration = (stats.end_time - stats.start_time).total_seconds()
        self.logger.info(
            "REM cycle #%d complete in %.1fs: pruned=%d compressed=%d novel=%d",
            stats.cycle_number,
            duration,
            stats.memories_pruned,
            stats.memories_compressed,
            stats.novel_connections,
        )
        return stats

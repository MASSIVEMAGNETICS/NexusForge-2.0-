"""
Main NexusForge orchestrator

Central system that combines all components: fractal agents, communication,
crews, experts, persistent memory, identity anchoring, REM sleep cycles,
gravitational attention, tokenformer, and sensory processing.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from nexusforge.core.fractal_agent import FractalAgent, AgentTemplate
from nexusforge.communication.hub import CommunicationHub, MessageType
from nexusforge.agents.crew import CrewManager, CrewRole
from nexusforge.agents.experts import MultiModalExpertSystem, ExpertModality

# Memory subsystems
from nexusforge.memory.identity_anchor import IdentityAnchor
from nexusforge.memory.episodic_memory import EpisodicMemory
from nexusforge.memory.rem_cycle import REMCycleEngine
from nexusforge.memory.synthesis import SelfSynthesisEngine

# Sensory processing
from nexusforge.sensory.processor import SensoryProcessor


class NexusForge:
    """
    Main orchestrator for NexusForge 2.0

    Combines fractal agent hierarchies, multi-agent communication, crew
    management, and multi-modal experts into a unified system — now extended
    with:

    * **Persistent episodic memory** with HDDR compression
    * **Identity anchor** — user-supplied "I am" paragraph locks identity
    * **REM sleep cycles** — idle-triggered memory consolidation and pruning
    * **Self-synthesis engine** — novel idea generation from self-inference
    * **Gravitational attention** — physics-based token attention
    * **GravitationalTokenFormer** — next-generation sequence model
    * **Sensory processor** — multi-modal input → episodic memory pipeline
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("NexusForge")

        # ---- Original subsystems ----
        self.communication_hub = CommunicationHub()
        self.crew_manager = CrewManager(self.communication_hub)
        self.expert_system = MultiModalExpertSystem()

        # Agent registry
        self.agents: Dict[str, FractalAgent] = {}
        self.root_agents: List[str] = []

        # System state
        self.running = False
        self.start_time: Optional[datetime] = None

        # ---- Memory subsystems ----
        # Identity anchor (must be configured by the user via set_identity())
        self.identity_anchor = IdentityAnchor(
            vector_dim=self.config.get("identity_vector_dim", 64)
        )

        # Episodic memory (connects to identity anchor for alignment scoring)
        self.episodic_memory = EpisodicMemory(
            identity_anchor=self.identity_anchor,
            hddr_dim=self.config.get("hddr_dim", 128),
            max_episodes=self.config.get("max_episodes", 1000),
            pruning_threshold=self.config.get("pruning_threshold", 0.2),
            sparse_threshold=self.config.get("sparse_threshold", 0.3),
        )

        # REM sleep cycle engine
        self.rem_engine = REMCycleEngine(
            episodic_memory=self.episodic_memory,
            identity_anchor=self.identity_anchor,
            idle_threshold=self.config.get("rem_idle_threshold", 30.0),
        )

        # Self-synthesis engine
        self.synthesis_engine = SelfSynthesisEngine(
            memory=self.episodic_memory,
            identity_anchor=self.identity_anchor,
        )

        # Sensory processor (front-door for all external data)
        self.sensory_processor = SensoryProcessor(
            episodic_memory=self.episodic_memory,
            rem_engine=self.rem_engine,
            base_importance_threshold=self.config.get("sensory_threshold", 0.3),
        )

        self._setup_logging()
        self.logger.info("NexusForge 2.0 initialized")
    
    def _setup_logging(self):
        """Configure logging"""
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def register_agent(self, agent: FractalAgent):
        """Register an agent with the nexus"""
        self.agents[agent.agent_id] = agent
        self.communication_hub.register_agent(agent.agent_id, agent)
        
        # Track root agents (depth 0)
        if agent.depth == 0:
            self.root_agents.append(agent.agent_id)
        
        self.logger.info(f"Registered agent: {agent.state.name} ({agent.agent_id})")
    
    def create_agent_from_template(
        self,
        template: AgentTemplate,
        parent_id: Optional[str] = None
    ) -> FractalAgent:
        """Create and register a new agent from template"""
        depth = 0
        if parent_id and parent_id in self.agents:
            depth = self.agents[parent_id].depth + 1
        
        agent = FractalAgent(
            template=template,
            depth=depth,
            parent_id=parent_id,
            nexus=self
        )
        
        self.register_agent(agent)
        return agent
    
    async def bootstrap_from_goal(self, goal: str, root_agent_name: str = "RootAgent") -> str:
        """
        Bootstrap the system from a high-level goal
        
        Creates a root agent and spawns a fractal hierarchy to achieve the goal.
        This is the main entry point for NexusForge.
        """
        self.logger.info(f"Bootstrapping from goal: {goal}")
        
        # Create root agent template
        root_template = AgentTemplate(
            name=root_agent_name,
            role="Coordinator",
            capabilities=["coordinate", "delegate", "monitor", "plan"],
            goal_template=goal,
            max_depth=5,
            spawn_threshold=0.7
        )
        
        # Create root agent
        root_agent = self.create_agent_from_template(root_template)
        
        # Process the goal (will spawn children as needed)
        result = await root_agent.process_goal(goal)
        
        self.logger.info(f"Bootstrap complete. Root agent: {root_agent.agent_id}")
        return root_agent.agent_id
    
    def get_agent(self, agent_id: str) -> Optional[FractalAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[FractalAgent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def get_agent_hierarchy(self, root_agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the full agent hierarchy
        
        If root_agent_id is None, returns all root agents and their hierarchies.
        """
        if root_agent_id:
            agent = self.agents.get(root_agent_id)
            return agent.get_hierarchy() if agent else {}
        
        # Return all root hierarchies
        return {
            "hierarchies": [
                self.agents[agent_id].get_hierarchy()
                for agent_id in self.root_agents
                if agent_id in self.agents
            ]
        }
    
    def create_crew(
        self,
        name: str,
        agent_ids: List[str],
        roles: List[CrewRole],
        leader_id: Optional[str] = None,
        goals: Optional[List[str]] = None
    ) -> str:
        """Create a crew from existing agents"""
        if len(agent_ids) != len(roles):
            raise ValueError("Number of agents must match number of roles")
        
        # Create crew
        crew_id = self.crew_manager.create_crew(name, leader_id, goals)
        
        # Add members
        for agent_id, role in zip(agent_ids, roles):
            if agent_id in self.agents:
                self.crew_manager.add_member(crew_id, agent_id, role)
        
        self.logger.info(f"Created crew: {name} with {len(agent_ids)} members")
        return crew_id
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str
    ) -> str:
        """Send a message between agents"""
        return await self.communication_hub.chat(from_agent, to_agent, message)
    
    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task: Dict[str, Any]
    ) -> str:
        """Delegate a task between agents"""
        return await self.communication_hub.delegate_task(from_agent, to_agent, task)
    
    # ------------------------------------------------------------------
    # Identity & Memory API
    # ------------------------------------------------------------------

    def set_identity(self, paragraph: str) -> Dict[str, Any]:
        """
        Set the agent's identity from a user-supplied "I am" paragraph.

        This is the primary way to lock the system's identity.  Every future
        memory stored will be scored for alignment with this statement, and
        REM sleep cycles will reinforce aligned memories while pruning
        counter-aligned ones.

        Args:
            paragraph: Free-text "I am …" self-description.

        Returns:
            Identity summary dict (see :meth:`IdentityAnchor.get_identity_summary`).
        """
        self.identity_anchor.set_identity(paragraph)
        self.logger.info(
            "Identity anchor set: %s…",
            paragraph[:60],
        )
        return self.identity_anchor.get_identity_summary()

    def remember(
        self,
        content: Any,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        emotional_valence: float = 0.0,
    ) -> Optional[str]:
        """
        Store a memory episode directly (bypasses sensory processor).

        Args:
            content: The content to remember (any serialisable type).
            importance: Salience score 0–1.
            tags: Optional categorisation tags.
            emotional_valence: Emotional tone -1 (negative) … +1 (positive).

        Returns:
            Episode ID (str) or ``None`` if filtered by sparse parsing.
        """
        self.rem_engine.record_activity()
        return self.episodic_memory.store(
            content=content,
            importance=importance,
            tags=tags,
            emotional_valence=emotional_valence,
        )

    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories relevant to *query*.

        Returns:
            List of episode summaries ordered by relevance.
        """
        episodes = self.episodic_memory.recall(query, top_k=top_k)
        return [
            {
                "episode_id": ep.episode_id,
                "content": ep.content,
                "importance": round(ep.importance, 3),
                "identity_alignment": round(ep.identity_alignment, 3),
                "timestamp": ep.timestamp.isoformat(),
                "tags": ep.tags,
                "access_count": ep.access_count,
            }
            for ep in episodes
        ]

    def perceive(
        self,
        data: Any,
        importance_override: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Feed raw sensory data into the system through the sensory processor.

        This is the recommended entry point for external data — the processor
        will auto-detect modality, score salience, apply novelty boost, and
        store in episodic memory if above threshold.

        Args:
            data: Raw input (str, int, float, dict, list, …).
            importance_override: Force a specific importance score.
            tags: Optional tags.

        Returns:
            Event summary dict.
        """
        event = self.sensory_processor.process(
            data,
            importance_override=importance_override,
            tags=tags,
        )
        return {
            "modality": event.modality.value,
            "importance": round(event.importance, 3),
            "was_stored": event.was_stored,
            "episode_id": event.episode_id,
        }

    def synthesize(self, seed: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Run the self-synthesis engine to generate novel ideas from memory.

        Args:
            seed: Optional concept to focus the synthesis.
            top_k: Number of memories to draw from.

        Returns:
            Synthesis result dict with ``synthesis``, ``concepts``,
            ``connections``, and ``novel_score``.
        """
        return self.synthesis_engine.synthesize(seed=seed, top_k=top_k)

    async def force_rem_cycle(self, *, time_scale: float = 1.0) -> Dict[str, Any]:
        """
        Manually trigger a REM sleep cycle immediately.

        Useful when you want to consolidate memory on demand rather than
        waiting for the idle threshold.

        Args:
            time_scale: Multiplier applied to phase durations (``0.0`` = no
                real-time sleep, useful for tests).

        Returns:
            Stats from the completed cycle.
        """
        stats = await self.rem_engine.force_cycle(time_scale=time_scale)
        return {
            "cycle_number": stats.cycle_number,
            "memories_pruned": stats.memories_pruned,
            "memories_compressed": stats.memories_compressed,
            "novel_connections": stats.novel_connections,
            "identity_reinforcements": stats.identity_reinforcements,
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """Return combined memory and REM cycle statistics."""
        return {
            "episodic_memory": self.episodic_memory.get_statistics(),
            "rem_engine": self.rem_engine.get_stats(),
            "identity": self.identity_anchor.get_identity_summary(),
            "sensory": self.sensory_processor.get_statistics(),
        }

    # ------------------------------------------------------------------
    # System status (existing, extended with memory info)
    # ------------------------------------------------------------------

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "total_agents": len(self.agents),
            "root_agents": len(self.root_agents),
            "total_crews": len(self.crew_manager.get_all_crews()),
            "total_experts": len(self.expert_system.get_all_experts()),
            "message_count": len(self.communication_hub.message_history),
            "agents_by_status": self._get_agents_by_status(),
            "identity_configured": self.identity_anchor.is_configured(),
            "episodic_memory_size": len(self.episodic_memory.episodes),
            "rem_phase": self.rem_engine.current_phase.value,
        }
    
    def _get_agents_by_status(self) -> Dict[str, int]:
        """Count agents by status"""
        status_counts = {}
        for agent in self.agents.values():
            status = agent.state.status
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts
    
    async def start(self):
        """Start the NexusForge system"""
        if self.running:
            self.logger.warning("System already running")
            return

        self.running = True
        self.start_time = datetime.now()

        await self.communication_hub.start()
        await self.rem_engine.start()

        self.logger.info("NexusForge system started")

    async def stop(self):
        """Stop the NexusForge system"""
        if not self.running:
            return

        self.running = False
        await self.rem_engine.stop()
        await self.communication_hub.stop()

        self.logger.info("NexusForge system stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed system statistics"""
        agent_stats = {
            "total": len(self.agents),
            "by_depth": {},
            "by_role": {},
            "by_status": self._get_agents_by_status()
        }

        for agent in self.agents.values():
            # Count by depth
            depth = agent.depth
            agent_stats["by_depth"][depth] = agent_stats["by_depth"].get(depth, 0) + 1

            # Count by role
            role = agent.state.role
            agent_stats["by_role"][role] = agent_stats["by_role"].get(role, 0) + 1

        return {
            "system_status": self.get_system_status(),
            "agent_stats": agent_stats,
            "crew_stats": {
                "total": len(self.crew_manager.get_all_crews()),
                "active": len([c for c in self.crew_manager.get_all_crews() if c.status == "active"])
            },
            "expert_stats": {
                "total": len(self.expert_system.get_all_experts()),
                "by_modality": {
                    modality.value: len(expert_ids)
                    for modality, expert_ids in self.expert_system.modality_experts.items()
                }
            },
            "communication_stats": {
                "total_messages": len(self.communication_hub.message_history),
                "conversations": len(self.communication_hub.conversations)
            },
            "memory_stats": self.get_memory_stats(),
        }

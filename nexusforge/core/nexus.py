"""
Main NexusForge orchestrator

Central system that combines all components: fractal agents, communication,
crews, experts, and provides the main API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from nexusforge.core.fractal_agent import FractalAgent, AgentTemplate
from nexusforge.communication.hub import CommunicationHub, MessageType
from nexusforge.agents.crew import CrewManager, CrewRole
from nexusforge.agents.experts import MultiModalExpertSystem, ExpertModality


class NexusForge:
    """
    Main orchestrator for NexusForge 2.0
    
    Combines fractal agent hierarchies, multi-agent communication,
    crew management, and multi-modal experts into a unified system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("NexusForge")
        
        # Initialize subsystems
        self.communication_hub = CommunicationHub()
        self.crew_manager = CrewManager(self.communication_hub)
        self.expert_system = MultiModalExpertSystem()
        
        # Agent registry
        self.agents: Dict[str, FractalAgent] = {}
        self.root_agents: List[str] = []
        
        # System state
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Set up logging
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
        goals: Optional[List[str]] = None,
        workflow_pattern = None  # Import will be added
    ) -> str:
        """Create a crew from existing agents with workflow pattern"""
        if len(agent_ids) != len(roles):
            raise ValueError("Number of agents must match number of roles")
        
        # Import here to avoid circular import
        from nexusforge.agents.crew import WorkflowPattern
        if workflow_pattern is None:
            workflow_pattern = WorkflowPattern.SEQUENTIAL
        
        # Create crew with workflow
        crew_id = self.crew_manager.create_crew(
            name, 
            leader_id, 
            goals,
            workflow_pattern=workflow_pattern
        )
        
        # Add members
        for agent_id, role in zip(agent_ids, roles):
            if agent_id in self.agents:
                self.crew_manager.add_member(crew_id, agent_id, role)
        
        self.logger.info(
            f"Created crew: {name} with {len(agent_ids)} members "
            f"using {workflow_pattern.value} workflow"
        )
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
            "agents_by_status": self._get_agents_by_status()
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
        
        self.logger.info("NexusForge system started")
    
    async def stop(self):
        """Stop the NexusForge system"""
        if not self.running:
            return
        
        self.running = False
        await self.communication_hub.stop()
        
        self.logger.info("NexusForge system stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed system statistics with enhanced metrics"""
        agent_stats = {
            "total": len(self.agents),
            "by_depth": {},
            "by_role": {},
            "by_status": self._get_agents_by_status(),
            "top_performers": []  # New
        }
        
        # Collect performance data
        agent_performances = []
        
        for agent in self.agents.values():
            # Count by depth
            depth = agent.depth
            agent_stats["by_depth"][depth] = agent_stats["by_depth"].get(depth, 0) + 1
            
            # Count by role
            role = agent.state.role
            agent_stats["by_role"][role] = agent_stats["by_role"].get(role, 0) + 1
            
            # Collect performance metrics
            agent_performances.append(agent.get_performance_metrics())
        
        # Get top 5 performers
        agent_performances.sort(
            key=lambda x: x.get("performance_score", 0) * x.get("success_rate", 0),
            reverse=True
        )
        agent_stats["top_performers"] = agent_performances[:5]
        
        return {
            "system_status": self.get_system_status(),
            "agent_stats": agent_stats,
            "crew_stats": {
                "total": len(self.crew_manager.get_all_crews()),
                "active": len([c for c in self.crew_manager.get_all_crews() if c.status == "active"]),
                "by_workflow": self._get_crews_by_workflow()  # New
            },
            "expert_stats": {
                "total": len(self.expert_system.get_all_experts()),
                "by_modality": {
                    modality.value: len(expert_ids)
                    for modality, expert_ids in self.expert_system.modality_experts.items()
                },
                "top_experts": self.expert_system.get_top_experts(5)  # New
            },
            "communication_stats": {
                "total_messages": len(self.communication_hub.message_history),
                "conversations": len(self.communication_hub.conversations),
                "pending_messages": self.communication_hub.get_pending_message_count()  # New
            }
        }
    
    def _get_crews_by_workflow(self) -> Dict[str, int]:
        """Count crews by workflow pattern"""
        workflow_counts = {}
        for crew in self.crew_manager.get_all_crews():
            pattern = crew.workflow_pattern.value
            workflow_counts[pattern] = workflow_counts.get(pattern, 0) + 1
        return workflow_counts
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        agent = self.agents.get(agent_id)
        return agent.get_performance_metrics() if agent else {}
    
    def get_top_performing_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing agents by performance score and success rate"""
        performances = [
            agent.get_performance_metrics()
            for agent in self.agents.values()
        ]
        
        performances.sort(
            key=lambda x: x.get("performance_score", 0) * x.get("success_rate", 0),
            reverse=True
        )
        
        return performances[:limit]
    
    async def send_priority_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        priority: str = "NORMAL"
    ) -> str:
        """Send a message with specific priority level"""
        from nexusforge.communication.hub import MessagePriority, MessageType
        
        priority_map = {
            "LOW": MessagePriority.LOW,
            "NORMAL": MessagePriority.NORMAL,
            "HIGH": MessagePriority.HIGH,
            "URGENT": MessagePriority.URGENT
        }
        
        return await self.communication_hub.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.CHAT,
            content=message,
            priority=priority_map.get(priority, MessagePriority.NORMAL)
        )
    
    def record_expert_task_result(self, expert_id: str, task_id: str, 
                                  success: bool, completion_time: float,
                                  confidence_score: float = 1.0):
        """Record the result of a task executed by an expert"""
        from nexusforge.agents.experts import TaskResult
        
        result = TaskResult(
            task_id=task_id,
            expert_id=expert_id,
            success=success,
            completion_time=completion_time,
            confidence_score=confidence_score
        )
        
        self.expert_system.record_task_result(result)
        self.logger.info(f"Recorded task result for expert {expert_id}: {'success' if success else 'failure'}")

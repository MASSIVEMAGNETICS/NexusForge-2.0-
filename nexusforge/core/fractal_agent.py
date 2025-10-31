"""
Core Fractal Agent Implementation

Implements recursive agent templates that can spawn child agents in a fractal hierarchy.
Inspired by FractalAgentForge's recursive template system.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


@dataclass
class AgentTemplate:
    """Template for spawning fractal agents"""
    name: str
    role: str
    capabilities: List[str]
    goal_template: str
    max_depth: int = 5
    spawn_threshold: float = 0.7  # Threshold for complexity that triggers child spawning (0.0-1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """State of an agent in the hierarchy"""
    agent_id: str
    name: str
    role: str
    depth: int
    parent_id: Optional[str]
    children: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    status: str = "active"  # active, idle, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FractalAgent:
    """
    Fractal Agent with recursive spawning capabilities
    
    Each agent can break down complex goals and spawn child agents to handle subtasks,
    creating a fractal hierarchy of specialized agents.
    """
    
    def __init__(
        self,
        template: AgentTemplate,
        depth: int = 0,
        parent_id: Optional[str] = None,
        nexus: Optional[Any] = None
    ):
        self.agent_id = str(uuid.uuid4())
        self.template = template
        self.depth = depth
        self.parent_id = parent_id
        self.nexus = nexus
        
        self.state = AgentState(
            agent_id=self.agent_id,
            name=template.name,
            role=template.role,
            depth=depth,
            parent_id=parent_id
        )
        
        self.children: List[FractalAgent] = []
        self.functions: Dict[str, Callable] = {}
        self.logger = logging.getLogger(f"FractalAgent.{self.state.name}")
        
    def can_spawn(self) -> bool:
        """Check if agent can spawn children based on depth and threshold"""
        return self.depth < self.template.max_depth
    
    async def break_down_goal(self, goal: str) -> List[Dict[str, Any]]:
        """
        Break down a complex goal into subtasks (Auto-GPT style)
        
        Returns list of subtask definitions that can spawn child agents
        """
        self.logger.info(f"Breaking down goal: {goal}")
        
        # Simple goal decomposition - in production this would use LLM
        subtasks = []
        
        # Analyze goal complexity
        words = goal.lower().split()
        
        if "and" in words or "then" in words:
            # Sequential tasks
            parts = goal.replace(" and ", " , ").replace(" then ", " , ").split(",")
            for i, part in enumerate(parts):
                subtasks.append({
                    "goal": part.strip(),
                    "type": "sequential",
                    "priority": i,
                    "role": self._infer_role(part.strip())
                })
        elif any(word in words for word in ["research", "analyze", "build", "test"]):
            # Specialized tasks
            if "research" in words:
                subtasks.append({
                    "goal": f"Research for: {goal}",
                    "type": "research",
                    "priority": 0,
                    "role": "Researcher"
                })
            if "analyze" in words:
                subtasks.append({
                    "goal": f"Analyze: {goal}",
                    "type": "analysis",
                    "priority": 1,
                    "role": "Analyst"
                })
            if "build" in words or "create" in words:
                subtasks.append({
                    "goal": f"Build: {goal}",
                    "type": "builder",
                    "priority": 2,
                    "role": "Builder"
                })
            if "test" in words or "verify" in words:
                subtasks.append({
                    "goal": f"Test: {goal}",
                    "type": "testing",
                    "priority": 3,
                    "role": "Tester"
                })
        else:
            # Single complex task - create support agents
            subtasks.append({
                "goal": f"Execute: {goal}",
                "type": "execution",
                "priority": 0,
                "role": "Executor"
            })
        
        return subtasks
    
    def _infer_role(self, task: str) -> str:
        """Infer agent role from task description"""
        task_lower = task.lower()
        
        role_keywords = {
            "Researcher": ["research", "investigate", "find", "search"],
            "Analyst": ["analyze", "evaluate", "assess", "review"],
            "Builder": ["build", "create", "develop", "implement"],
            "Tester": ["test", "verify", "validate", "check"],
            "Writer": ["write", "document", "describe", "explain"],
            "Coordinator": ["coordinate", "manage", "organize", "plan"]
        }
        
        for role, keywords in role_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                return role
        
        return "GeneralAgent"
    
    async def spawn_child(self, subtask: Dict[str, Any]) -> Optional['FractalAgent']:
        """
        Spawn a child agent for a subtask (fractal recursion)
        """
        if not self.can_spawn():
            self.logger.warning(f"Max depth reached, cannot spawn child for: {subtask['goal']}")
            return None
        
        # Create child template
        child_template = AgentTemplate(
            name=f"{subtask['role']}_{len(self.children)}",
            role=subtask['role'],
            capabilities=self._inherit_capabilities(subtask['type']),
            goal_template=subtask['goal'],
            max_depth=self.template.max_depth,
            spawn_threshold=self.template.spawn_threshold,
            metadata={"parent_task": subtask['goal'], "priority": subtask['priority']}
        )
        
        # Spawn child agent
        child = FractalAgent(
            template=child_template,
            depth=self.depth + 1,
            parent_id=self.agent_id,
            nexus=self.nexus
        )
        
        child.state.goals.append(subtask['goal'])
        self.children.append(child)
        self.state.children.append(child.agent_id)
        
        self.logger.info(f"Spawned child agent: {child.state.name} at depth {child.depth}")
        
        # Register with nexus if available
        if self.nexus:
            self.nexus.register_agent(child)
        
        return child
    
    def _inherit_capabilities(self, task_type: str) -> List[str]:
        """Inherit and specialize capabilities based on task type"""
        base_capabilities = ["communicate", "delegate", "report"]
        
        type_capabilities = {
            "research": ["search", "gather", "synthesize"],
            "analysis": ["analyze", "evaluate", "compare"],
            "builder": ["design", "implement", "integrate"],
            "testing": ["test", "validate", "debug"],
            "sequential": ["coordinate", "sequence", "monitor"],
            "execution": ["execute", "optimize", "adapt"]
        }
        
        return base_capabilities + type_capabilities.get(task_type, [])
    
    def register_function(self, name: str, func: Callable):
        """
        Register a self-building function (BabyAGI style)
        
        Agents can dynamically register new capabilities
        """
        self.functions[name] = func
        self.logger.info(f"Registered function: {name}")
        
        # Add to capabilities
        if name not in self.template.capabilities:
            self.template.capabilities.append(name)
    
    async def execute_function(self, name: str, *args, **kwargs) -> Any:
        """Execute a registered function"""
        if name not in self.functions:
            raise ValueError(f"Function {name} not registered")
        
        self.logger.info(f"Executing function: {name}")
        result = self.functions[name](*args, **kwargs)
        
        # Handle async functions
        if asyncio.iscoroutine(result):
            result = await result
        
        return result
    
    async def process_goal(self, goal: str) -> Dict[str, Any]:
        """
        Process a goal by breaking it down and spawning children if needed
        """
        self.state.goals.append(goal)
        self.logger.info(f"Processing goal: {goal}")
        
        # Break down the goal
        subtasks = await self.break_down_goal(goal)
        
        results = {
            "goal": goal,
            "agent_id": self.agent_id,
            "subtasks": subtasks,
            "children": [],
            "status": "in_progress"
        }
        
        # Spawn children for subtasks if threshold met and depth allows
        if len(subtasks) > 1 and self.can_spawn():
            for subtask in subtasks:
                child = await self.spawn_child(subtask)
                if child:
                    results["children"].append(child.agent_id)
        
        return results
    
    def get_hierarchy(self) -> Dict[str, Any]:
        """Get the full agent hierarchy tree"""
        return {
            "agent_id": self.agent_id,
            "name": self.state.name,
            "role": self.state.role,
            "depth": self.depth,
            "status": self.state.status,
            "goals": self.state.goals,
            "capabilities": self.template.capabilities,
            "children": [child.get_hierarchy() for child in self.children]
        }
    
    def set_status(self, status: str):
        """Update agent status"""
        self.state.status = status
        self.logger.info(f"Status changed to: {status}")

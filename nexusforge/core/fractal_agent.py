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
    """State of an agent in the hierarchy with enhanced tracking"""
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
    # Enhanced state tracking
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    performance_score: float = 1.0  # 0.5 to 2.0, starts at 1.0
    current_task: Optional[str] = None
    message_count: int = 0


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
        
        Enhanced with complexity analysis, dependency tracking, and smart prioritization.
        Returns list of subtask definitions that can spawn child agents.
        """
        self.logger.info(f"Breaking down goal: {goal}")
        
        # Analyze goal complexity
        complexity_score = self._analyze_goal_complexity(goal)
        words = goal.lower().split()
        subtasks = []
        
        # Enhanced: Handle compound goals with better parsing
        if "and" in words or "then" in words:
            # Sequential tasks with dependency tracking
            parts = goal.replace(" and ", " , ").replace(" then ", " , ").split(",")
            for i, part in enumerate(parts):
                subtasks.append({
                    "goal": part.strip(),
                    "type": "sequential",
                    "priority": i,
                    "role": self._infer_role(part.strip()),
                    "complexity": self._analyze_goal_complexity(part.strip()),
                    "dependencies": [i - 1] if i > 0 else [],
                    "estimated_effort": self._estimate_effort(part.strip())
                })
        elif any(word in words for word in ["research", "analyze", "build", "test", "design", "implement", "deploy"]):
            # Specialized tasks with proper workflow ordering
            if "research" in words or "investigate" in words:
                subtasks.append({
                    "goal": f"Research for: {goal}",
                    "type": "research",
                    "priority": 0,
                    "role": "Researcher",
                    "complexity": min(complexity_score, 0.6),
                    "dependencies": [],
                    "estimated_effort": "medium"
                })
            if "design" in words or "plan" in words:
                subtasks.append({
                    "goal": f"Design: {goal}",
                    "type": "design",
                    "priority": 1,
                    "role": "Designer",
                    "complexity": complexity_score * 0.7,
                    "dependencies": [0] if len(subtasks) > 0 else [],
                    "estimated_effort": "medium"
                })
            if "analyze" in words:
                subtasks.append({
                    "goal": f"Analyze: {goal}",
                    "type": "analysis",
                    "priority": len(subtasks),
                    "role": "Analyst",
                    "complexity": complexity_score * 0.6,
                    "dependencies": list(range(len(subtasks))),
                    "estimated_effort": "medium"
                })
            if "build" in words or "create" in words or "implement" in words:
                subtasks.append({
                    "goal": f"Build: {goal}",
                    "type": "builder",
                    "priority": len(subtasks),
                    "role": "Builder",
                    "complexity": complexity_score * 0.9,
                    "dependencies": list(range(len(subtasks))),
                    "estimated_effort": "high"
                })
            if "test" in words or "verify" in words or "validate" in words:
                subtasks.append({
                    "goal": f"Test: {goal}",
                    "type": "testing",
                    "priority": len(subtasks),
                    "role": "Tester",
                    "complexity": complexity_score * 0.5,
                    "dependencies": list(range(len(subtasks))),
                    "estimated_effort": "medium"
                })
            if "deploy" in words or "release" in words:
                subtasks.append({
                    "goal": f"Deploy: {goal}",
                    "type": "deployment",
                    "priority": len(subtasks),
                    "role": "DevOps",
                    "complexity": complexity_score * 0.4,
                    "dependencies": list(range(len(subtasks))),
                    "estimated_effort": "low"
                })
        else:
            # Single complex task - analyze if it needs breakdown
            if complexity_score > 0.7:
                # High complexity: break into phases
                subtasks.extend([
                    {
                        "goal": f"Plan: {goal}",
                        "type": "planning",
                        "priority": 0,
                        "role": "Planner",
                        "complexity": 0.4,
                        "dependencies": [],
                        "estimated_effort": "low"
                    },
                    {
                        "goal": f"Execute: {goal}",
                        "type": "execution",
                        "priority": 1,
                        "role": "Executor",
                        "complexity": complexity_score,
                        "dependencies": [0],
                        "estimated_effort": "high"
                    },
                    {
                        "goal": f"Verify: {goal}",
                        "type": "verification",
                        "priority": 2,
                        "role": "Verifier",
                        "complexity": 0.3,
                        "dependencies": [1],
                        "estimated_effort": "low"
                    }
                ])
            else:
                # Low complexity: single task
                subtasks.append({
                    "goal": f"Execute: {goal}",
                    "type": "execution",
                    "priority": 0,
                    "role": "Executor",
                    "complexity": complexity_score,
                    "dependencies": [],
                    "estimated_effort": "low" if complexity_score < 0.3 else "medium"
                })
        
        self.logger.info(f"Decomposed into {len(subtasks)} subtasks with complexity {complexity_score:.2f}")
        return subtasks
    
    def _analyze_goal_complexity(self, goal: str) -> float:
        """
        Analyze goal complexity using multiple heuristics
        
        Returns complexity score from 0.1 (simple) to 1.0 (very complex)
        """
        words = goal.lower().split()
        
        # Factors contributing to complexity
        length_factor = min(len(words) / 20.0, 1.0)  # Longer goals = more complex
        
        # Technical keywords increase complexity
        technical_keywords = [
            "integrate", "optimize", "scale", "deploy", "architect",
            "implement", "distributed", "concurrent", "algorithm"
        ]
        tech_factor = sum(1 for kw in technical_keywords if kw in words) / 5.0
        
        # Multiple action verbs = higher complexity
        action_verbs = [
            "build", "create", "design", "analyze", "test",
            "research", "implement", "deploy", "monitor"
        ]
        action_factor = min(sum(1 for verb in action_verbs if verb in words) / 3.0, 1.0)
        
        # Compound goals (and/or/then) increase complexity
        compound_factor = 0.3 if any(conj in words for conj in ["and", "or", "then", "after"]) else 0.0
        
        # Calculate weighted complexity
        complexity = (
            length_factor * 0.3 +
            tech_factor * 0.3 +
            action_factor * 0.2 +
            compound_factor * 0.2
        )
        
        return min(max(complexity, 0.1), 1.0)  # Clamp between 0.1 and 1.0
    
    def _estimate_effort(self, goal: str) -> str:
        """Estimate effort level for a goal"""
        complexity = self._analyze_goal_complexity(goal)
        
        if complexity < 0.3:
            return "low"
        elif complexity < 0.7:
            return "medium"
        else:
            return "high"
    
    def _infer_role(self, task: str) -> str:
        """Infer agent role from task description with expanded role types"""
        task_lower = task.lower()
        
        role_keywords = {
            "DevOps": ["deploy", "release", "launch", "publish", "ship"],
            "Researcher": ["research", "investigate", "find", "search", "explore", "discover"],
            "Analyst": ["analyze", "evaluate", "assess", "review", "examine", "study"],
            "Builder": ["build", "create", "develop", "construct", "code", "program"],
            "Implementer": ["implement", "execute", "apply"],
            "Designer": ["design", "architect", "model", "structure", "blueprint"],
            "Tester": ["test", "verify", "validate", "check", "qa", "quality"],
            "Planner": ["plan", "strategize", "roadmap", "schedule"],
            "Verifier": ["verify", "confirm", "ensure", "guarantee"],
            "Writer": ["write", "document", "describe", "explain", "annotate"],
            "Coordinator": ["coordinate", "manage", "organize", "orchestrate", "supervise"],
            "Optimizer": ["optimize", "improve", "enhance", "refine", "tune"]
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
        """Inherit and specialize capabilities based on task type - expanded with new types"""
        base_capabilities = ["communicate", "delegate", "report"]
        
        type_capabilities = {
            "research": ["search", "gather", "synthesize", "investigate"],
            "analysis": ["analyze", "evaluate", "compare", "interpret"],
            "builder": ["design", "implement", "integrate", "construct"],
            "testing": ["test", "validate", "debug", "qa"],
            "sequential": ["coordinate", "sequence", "monitor", "track"],
            "execution": ["execute", "optimize", "adapt", "perform"],
            "planning": ["plan", "strategize", "schedule", "prioritize"],
            "design": ["architect", "model", "blueprint", "structure"],
            "deployment": ["deploy", "release", "monitor", "rollback"],
            "verification": ["verify", "confirm", "audit", "certify"]
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
        """Update agent status with activity tracking"""
        self.state.status = status
        self.state.last_activity = datetime.now()
        self.logger.info(f"Status changed to: {status}")
    
    def record_task_completion(self, success: bool, execution_time: float = 0.0):
        """
        Record task completion to update performance metrics
        
        Note: Uses asymmetric learning rates - failures penalize 2.5x more than successes reward.
        This design encourages reliability and penalizes errors more heavily to drive improvement.
        """
        if success:
            self.state.tasks_completed += 1
            # Increase performance score on success (up to 2.0)
            self.state.performance_score = min(2.0, self.state.performance_score + 0.02)
        else:
            self.state.tasks_failed += 1
            # Decrease performance score on failure more than success increase (down to 0.5)
            # Asymmetric: -0.05 vs +0.02 to emphasize reliability
            self.state.performance_score = max(0.5, self.state.performance_score - 0.05)
        
        self.state.total_execution_time += execution_time
        self.state.last_activity = datetime.now()
        
        self.logger.info(
            f"Task {'completed' if success else 'failed'}. "
            f"Performance: {self.state.performance_score:.2f}, "
            f"Success rate: {self.get_success_rate():.1%}"
        )
    
    def get_success_rate(self) -> float:
        """Calculate success rate for this agent"""
        total = self.state.tasks_completed + self.state.tasks_failed
        return self.state.tasks_completed / total if total > 0 else 1.0
    
    def get_avg_execution_time(self) -> float:
        """Get average execution time per task"""
        total_tasks = self.state.tasks_completed + self.state.tasks_failed
        return self.state.total_execution_time / total_tasks if total_tasks > 0 else 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for this agent"""
        total_tasks = self.state.tasks_completed + self.state.tasks_failed
        uptime = (datetime.now() - self.state.created_at).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "name": self.state.name,
            "role": self.state.role,
            "status": self.state.status,
            "performance_score": self.state.performance_score,
            "tasks_completed": self.state.tasks_completed,
            "tasks_failed": self.state.tasks_failed,
            "success_rate": self.get_success_rate(),
            "avg_execution_time": self.get_avg_execution_time(),
            "total_tasks": total_tasks,
            "uptime_seconds": uptime,
            "message_count": self.state.message_count,
            "last_activity": self.state.last_activity.isoformat(),
            "children_count": len(self.children)
        }
    
    def increment_message_count(self):
        """Track message activity"""
        self.state.message_count += 1
        self.state.last_activity = datetime.now()

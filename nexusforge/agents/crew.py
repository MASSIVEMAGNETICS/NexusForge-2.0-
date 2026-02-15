"""
Agent Crew System - CrewAI-inspired role-based crews

Manages teams of agents with specific roles working together on complex tasks.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CrewRole(Enum):
    """Standard crew roles - expanded"""
    LEADER = "leader"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    BUILDER = "builder"
    TESTER = "tester"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    DESIGNER = "designer"  # New
    OPTIMIZER = "optimizer"  # New
    MONITOR = "monitor"  # New


class WorkflowPattern(Enum):
    """Workflow execution patterns for crews"""
    SEQUENTIAL = "sequential"  # Tasks run one after another
    PARALLEL = "parallel"  # All tasks run simultaneously
    PIPELINE = "pipeline"  # Output of one feeds into next
    MAP_REDUCE = "map_reduce"  # Distribute work, then aggregate
    HIERARCHICAL = "hierarchical"  # Tree-like delegation


@dataclass
class CrewMember:
    """Member of a crew with specific role"""
    agent_id: str
    role: CrewRole
    specialization: Optional[str] = None
    active: bool = True


@dataclass
class Crew:
    """A crew of agents working together with workflow support"""
    crew_id: str
    name: str
    leader_id: Optional[str]
    members: List[CrewMember] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    status: str = "forming"  # forming, active, paused, completed
    metadata: Dict[str, Any] = field(default_factory=dict)
    workflow_pattern: WorkflowPattern = WorkflowPattern.SEQUENTIAL  # New
    task_queue: List[Dict[str, Any]] = field(default_factory=list)  # New: pending tasks
    completed_tasks: List[str] = field(default_factory=list)  # New: track completion


class CrewManager:
    """
    Manages crews of agents with defined roles
    
    Inspired by CrewAI's role-based team system where agents work together
    with clear roles and responsibilities.
    """
    
    def __init__(self, communication_hub: Any):
        self.crews: Dict[str, Crew] = {}
        self.agent_crews: Dict[str, List[str]] = {}  # agent_id -> crew_ids
        self.communication_hub = communication_hub
        self.logger = logging.getLogger("CrewManager")
    
    def create_crew(
        self,
        name: str,
        leader_id: Optional[str] = None,
        goals: Optional[List[str]] = None,
        workflow_pattern: WorkflowPattern = WorkflowPattern.SEQUENTIAL
    ) -> str:
        """Create a new crew with specified workflow pattern"""
        import uuid
        crew_id = str(uuid.uuid4())
        
        crew = Crew(
            crew_id=crew_id,
            name=name,
            leader_id=leader_id,
            goals=goals or [],
            workflow_pattern=workflow_pattern
        )
        
        self.crews[crew_id] = crew
        
        if leader_id:
            self._add_agent_to_crew_tracking(leader_id, crew_id)
        
        self.logger.info(
            f"Created crew: {name} ({crew_id}) with {workflow_pattern.value} workflow"
        )
        return crew_id
    
    def add_member(
        self,
        crew_id: str,
        agent_id: str,
        role: CrewRole,
        specialization: Optional[str] = None
    ):
        """Add a member to a crew"""
        if crew_id not in self.crews:
            raise ValueError(f"Crew {crew_id} not found")
        
        member = CrewMember(
            agent_id=agent_id,
            role=role,
            specialization=specialization
        )
        
        self.crews[crew_id].members.append(member)
        self._add_agent_to_crew_tracking(agent_id, crew_id)
        
        self.logger.info(f"Added {agent_id} as {role.value} to crew {crew_id}")
    
    def _add_agent_to_crew_tracking(self, agent_id: str, crew_id: str):
        """Track which crews an agent belongs to"""
        if agent_id not in self.agent_crews:
            self.agent_crews[agent_id] = []
        self.agent_crews[agent_id].append(crew_id)
    
    def remove_member(self, crew_id: str, agent_id: str):
        """Remove a member from a crew"""
        if crew_id not in self.crews:
            return
        
        crew = self.crews[crew_id]
        crew.members = [m for m in crew.members if m.agent_id != agent_id]
        
        if agent_id in self.agent_crews:
            self.agent_crews[agent_id] = [
                cid for cid in self.agent_crews[agent_id] if cid != crew_id
            ]
        
        self.logger.info(f"Removed {agent_id} from crew {crew_id}")
    
    def get_crew(self, crew_id: str) -> Optional[Crew]:
        """Get crew details"""
        return self.crews.get(crew_id)
    
    def get_agent_crews(self, agent_id: str) -> List[Crew]:
        """Get all crews an agent belongs to"""
        crew_ids = self.agent_crews.get(agent_id, [])
        return [self.crews[cid] for cid in crew_ids if cid in self.crews]
    
    def get_crew_members(self, crew_id: str, role: Optional[CrewRole] = None) -> List[CrewMember]:
        """Get members of a crew, optionally filtered by role"""
        if crew_id not in self.crews:
            return []
        
        members = self.crews[crew_id].members
        
        if role:
            members = [m for m in members if m.role == role]
        
        return members
    
    def assign_goal(self, crew_id: str, goal: str):
        """Assign a goal to a crew"""
        if crew_id in self.crews:
            self.crews[crew_id].goals.append(goal)
            self.logger.info(f"Assigned goal to crew {crew_id}: {goal}")
    
    def set_crew_status(self, crew_id: str, status: str):
        """Update crew status"""
        if crew_id in self.crews:
            self.crews[crew_id].status = status
            self.logger.info(f"Crew {crew_id} status: {status}")
    
    async def broadcast_to_crew(self, crew_id: str, message: str, from_agent: str):
        """Broadcast a message to all crew members"""
        if crew_id not in self.crews:
            return
        
        crew = self.crews[crew_id]
        for member in crew.members:
            if member.agent_id != from_agent and member.active:
                await self.communication_hub.chat(
                    from_agent=from_agent,
                    to_agent=member.agent_id,
                    message=f"[Crew: {crew.name}] {message}"
                )
    
    def get_all_crews(self) -> List[Crew]:
        """Get all crews"""
        return list(self.crews.values())
    
    async def assign_task_to_crew(
        self,
        crew_id: str,
        task: Dict[str, Any],
        from_agent: Optional[str] = None
    ):
        """
        Assign a task to a crew, will be distributed based on workflow pattern
        """
        if crew_id not in self.crews:
            self.logger.error(f"Crew {crew_id} not found")
            return
        
        crew = self.crews[crew_id]
        crew.task_queue.append(task)
        
        self.logger.info(f"Task assigned to crew {crew_id}: {task.get('description', 'Unnamed task')}")
        
        # Execute based on workflow pattern
        try:
            await self._execute_crew_workflow(crew_id, task)
        finally:
            # Remove task from queue after execution to maintain accurate pending count
            try:
                crew.task_queue.remove(task)
            except ValueError:
                pass  # Task already removed or not in queue
    
    async def _execute_crew_workflow(self, crew_id: str, task: Dict[str, Any]):
        """Execute task based on crew's workflow pattern"""
        crew = self.crews[crew_id]
        
        if crew.workflow_pattern == WorkflowPattern.SEQUENTIAL:
            await self._execute_sequential(crew, task)
        elif crew.workflow_pattern == WorkflowPattern.PARALLEL:
            await self._execute_parallel(crew, task)
        elif crew.workflow_pattern == WorkflowPattern.PIPELINE:
            await self._execute_pipeline(crew, task)
        elif crew.workflow_pattern == WorkflowPattern.MAP_REDUCE:
            await self._execute_map_reduce(crew, task)
        elif crew.workflow_pattern == WorkflowPattern.HIERARCHICAL:
            await self._execute_hierarchical(crew, task)
    
    async def _execute_sequential(self, crew: Crew, task: Dict[str, Any]):
        """Execute task sequentially through crew members"""
        self.logger.info(f"Executing sequential workflow for crew {crew.crew_id}")
        
        # Assign to members in order of their roles
        for i, member in enumerate(crew.members):
            if member.active:
                subtask = {
                    **task,
                    "phase": i,
                    "total_phases": len(crew.members),
                    "previous_member": crew.members[i-1].agent_id if i > 0 else None
                }
                
                await self.communication_hub.delegate_task(
                    from_agent=crew.leader_id or "crew_manager",
                    to_agent=member.agent_id,
                    task=subtask
                )
    
    async def _execute_parallel(self, crew: Crew, task: Dict[str, Any]):
        """Execute task in parallel across all crew members"""
        self.logger.info(f"Executing parallel workflow for crew {crew.crew_id}")
        
        # Distribute to all active members simultaneously
        for member in crew.members:
            if member.active:
                await self.communication_hub.delegate_task(
                    from_agent=crew.leader_id or "crew_manager",
                    to_agent=member.agent_id,
                    task=task
                )
    
    async def _execute_pipeline(self, crew: Crew, task: Dict[str, Any]):
        """Execute as pipeline where output feeds to next stage"""
        self.logger.info(f"Executing pipeline workflow for crew {crew.crew_id}")
        
        # Similar to sequential but with explicit data passing
        # First member gets the task
        if crew.members and crew.members[0].active:
            pipeline_task = {
                **task,
                "pipeline_stage": 0,
                "total_stages": len(crew.members),
                "next_agent": crew.members[1].agent_id if len(crew.members) > 1 else None
            }
            
            await self.communication_hub.delegate_task(
                from_agent=crew.leader_id or "crew_manager",
                to_agent=crew.members[0].agent_id,
                task=pipeline_task
            )
    
    async def _execute_map_reduce(self, crew: Crew, task: Dict[str, Any]):
        """Map work to workers, then reduce results with leader"""
        self.logger.info(f"Executing map-reduce workflow for crew {crew.crew_id}")
        
        # Map phase: distribute to non-leader members
        workers = [m for m in crew.members if m.agent_id != crew.leader_id and m.active]
        
        for i, member in enumerate(workers):
            map_task = {
                **task,
                "map_partition": i,
                "total_partitions": len(workers),
                "reduce_to": crew.leader_id
            }
            
            await self.communication_hub.delegate_task(
                from_agent=crew.leader_id or "crew_manager",
                to_agent=member.agent_id,
                task=map_task
            )
    
    async def _execute_hierarchical(self, crew: Crew, task: Dict[str, Any]):
        """Hierarchical delegation from leader down"""
        self.logger.info(f"Executing hierarchical workflow for crew {crew.crew_id}")
        
        # Leader receives task and delegates to subordinates
        if crew.leader_id:
            hierarchical_task = {
                **task,
                "delegation_level": 0,
                "subordinates": [m.agent_id for m in crew.members if m.agent_id != crew.leader_id]
            }
            
            await self.communication_hub.delegate_task(
                from_agent="crew_manager",
                to_agent=crew.leader_id,
                task=hierarchical_task
            )
    
    def mark_task_complete(self, crew_id: str, task_id: str):
        """Mark a task as completed"""
        if crew_id in self.crews:
            crew = self.crews[crew_id]
            if task_id not in crew.completed_tasks:
                crew.completed_tasks.append(task_id)
                self.logger.info(f"Task {task_id} completed in crew {crew_id}")
    
    def get_crew_statistics(self, crew_id: str) -> Dict[str, Any]:
        """Get statistics for a crew"""
        if crew_id not in self.crews:
            return {}
        
        crew = self.crews[crew_id]
        active_members = sum(1 for m in crew.members if m.active)
        
        return {
            "crew_id": crew_id,
            "name": crew.name,
            "status": crew.status,
            "workflow_pattern": crew.workflow_pattern.value,
            "total_members": len(crew.members),
            "active_members": active_members,
            "pending_tasks": len(crew.task_queue),
            "completed_tasks": len(crew.completed_tasks),
            "goals": len(crew.goals)
        }

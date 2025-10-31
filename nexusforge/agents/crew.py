"""
Agent Crew System - CrewAI-inspired role-based crews

Manages teams of agents with specific roles working together on complex tasks.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CrewRole(Enum):
    """Standard crew roles"""
    LEADER = "leader"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    BUILDER = "builder"
    TESTER = "tester"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


@dataclass
class CrewMember:
    """Member of a crew with specific role"""
    agent_id: str
    role: CrewRole
    specialization: Optional[str] = None
    active: bool = True


@dataclass
class Crew:
    """A crew of agents working together"""
    crew_id: str
    name: str
    leader_id: Optional[str]
    members: List[CrewMember] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    status: str = "forming"  # forming, active, paused, completed
    metadata: Dict[str, Any] = field(default_factory=dict)


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
        goals: Optional[List[str]] = None
    ) -> str:
        """Create a new crew"""
        import uuid
        crew_id = str(uuid.uuid4())
        
        crew = Crew(
            crew_id=crew_id,
            name=name,
            leader_id=leader_id,
            goals=goals or []
        )
        
        self.crews[crew_id] = crew
        
        if leader_id:
            self._add_agent_to_crew_tracking(leader_id, crew_id)
        
        self.logger.info(f"Created crew: {name} ({crew_id})")
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

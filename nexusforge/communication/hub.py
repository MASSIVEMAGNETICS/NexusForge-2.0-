"""
Communication Hub for Agent Conversations and Delegation

Implements AutoGen-style agent chat and message passing between agents.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MessageType(Enum):
    """Types of messages agents can exchange"""
    CHAT = "chat"
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    DELEGATION = "delegation"
    STATUS = "status"
    BROADCAST = "broadcast"


@dataclass
class Message:
    """Message structure for agent communication"""
    message_id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None


class CommunicationHub:
    """
    Central hub for agent-to-agent communication
    
    Enables AutoGen-style conversations where agents can:
    - Send direct messages
    - Broadcast to all agents
    - Delegate tasks
    - Query for information
    - Report status and results
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.message_history: List[Message] = []
        self.conversations: Dict[str, List[Message]] = {}
        self.handlers: Dict[MessageType, List[Callable]] = {mt: [] for mt in MessageType}
        self.logger = logging.getLogger("CommunicationHub")
        self._running = False
        
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent with the communication hub"""
        self.agents[agent_id] = agent
        self.message_queues[agent_id] = asyncio.Queue()
        self.logger.info(f"Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the hub"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.message_queues[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: Optional[str],
        message_type: MessageType,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a message from one agent to another (or broadcast)
        """
        import uuid
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            reply_to=reply_to
        )
        
        # Store in history
        self.message_history.append(message)
        
        # Track conversation
        conv_key = f"{from_agent}:{to_agent or 'broadcast'}"
        if conv_key not in self.conversations:
            self.conversations[conv_key] = []
        self.conversations[conv_key].append(message)
        
        # Deliver message
        if to_agent:
            # Direct message
            if to_agent in self.message_queues:
                await self.message_queues[to_agent].put(message)
                self.logger.debug(f"Message {message_id} delivered to {to_agent}")
            else:
                self.logger.warning(f"Agent {to_agent} not found for message delivery")
        else:
            # Broadcast to all agents
            for agent_id, queue in self.message_queues.items():
                if agent_id != from_agent:
                    await queue.put(message)
            self.logger.debug(f"Message {message_id} broadcast to all agents")
        
        # Trigger handlers
        for handler in self.handlers[message_type]:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Handler error: {e}")
        
        return message_id
    
    async def receive_message(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """
        Receive a message for an agent (non-blocking with timeout)
        """
        if agent_id not in self.message_queues:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.message_queues[agent_id].get(),
                timeout=timeout
            )
            self.logger.debug(f"Agent {agent_id} received message {message.message_id}")
            return message
        except asyncio.TimeoutError:
            return None
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for a message type"""
        self.handlers[message_type].append(handler)
        self.logger.info(f"Registered handler for {message_type.value}")
    
    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task: Dict[str, Any]
    ) -> str:
        """
        Delegate a task from one agent to another
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.DELEGATION,
            content=task,
            metadata={"delegation_time": datetime.now().isoformat()}
        )
    
    async def report_result(
        self,
        from_agent: str,
        to_agent: str,
        result: Any,
        task_id: Optional[str] = None
    ) -> str:
        """
        Report a result back to a delegating agent
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.RESULT,
            content=result,
            metadata={"task_id": task_id} if task_id else {},
            reply_to=task_id
        )
    
    async def chat(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a chat message between agents
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.CHAT,
            content=message,
            reply_to=reply_to
        )
    
    def get_conversation(self, agent1: str, agent2: str) -> List[Message]:
        """Get conversation history between two agents"""
        conv_key1 = f"{agent1}:{agent2}"
        conv_key2 = f"{agent2}:{agent1}"
        
        messages = []
        messages.extend(self.conversations.get(conv_key1, []))
        messages.extend(self.conversations.get(conv_key2, []))
        
        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def get_agent_messages(self, agent_id: str) -> List[Message]:
        """Get all messages involving an agent"""
        return [
            msg for msg in self.message_history
            if msg.from_agent == agent_id or msg.to_agent == agent_id
        ]
    
    async def start(self):
        """Start the communication hub"""
        self._running = True
        self.logger.info("Communication hub started")
    
    async def stop(self):
        """Stop the communication hub"""
        self._running = False
        self.logger.info("Communication hub stopped")

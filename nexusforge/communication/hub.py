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
import heapq


class MessageType(Enum):
    """Types of messages agents can exchange"""
    CHAT = "chat"
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    DELEGATION = "delegation"
    STATUS = "status"
    BROADCAST = "broadcast"


class MessagePriority(Enum):
    """Message priority levels for queue ordering"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class Message:
    """Message structure for agent communication with priority support"""
    message_id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL  # New field
    dependencies: List[str] = field(default_factory=list)  # New: message dependencies
    
    def __lt__(self, other):
        """Enable priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


class CommunicationHub:
    """
    Central hub for agent-to-agent communication with priority queues
    
    Enables AutoGen-style conversations where agents can:
    - Send direct messages with priority levels
    - Broadcast to all agents
    - Delegate tasks with dependency tracking
    - Query for information
    - Report status and results
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        # Changed to priority queues (heapq-based)
        self.message_queues: Dict[str, List] = {}
        self.message_history: List[Message] = []
        self.conversations: Dict[str, List[Message]] = {}
        self.handlers: Dict[MessageType, List[Callable]] = {mt: [] for mt in MessageType}
        self.logger = logging.getLogger("CommunicationHub")
        self._running = False
        self._message_dependencies: Dict[str, List[str]] = {}  # Track dependencies
        self._pending_messages: Dict[str, Message] = {}  # Messages waiting for dependencies
        
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent with the communication hub"""
        self.agents[agent_id] = agent
        self.message_queues[agent_id] = []  # Priority queue (heap)
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
        reply_to: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        Send a message from one agent to another (or broadcast) with priority support
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
            reply_to=reply_to,
            priority=priority,
            dependencies=dependencies or []
        )
        
        # Store in history
        self.message_history.append(message)
        
        # Track conversation
        conv_key = f"{from_agent}:{to_agent or 'broadcast'}"
        if conv_key not in self.conversations:
            self.conversations[conv_key] = []
        self.conversations[conv_key].append(message)
        
        # Check dependencies
        if dependencies and not self._dependencies_satisfied(dependencies):
            # Store pending message
            self._pending_messages[message_id] = message
            self._message_dependencies[message_id] = dependencies
            self.logger.debug(f"Message {message_id} pending dependencies: {dependencies}")
            return message_id
        
        # Deliver message
        await self._deliver_message(message)
        
        # Check if this message satisfies any pending messages
        await self._process_pending_messages(message_id)
        
        return message_id
    
    def _dependencies_satisfied(self, dependencies: List[str]) -> bool:
        """Check if all message dependencies are satisfied"""
        return all(dep_id in [m.message_id for m in self.message_history] 
                   for dep_id in dependencies)
    
    async def _deliver_message(self, message: Message):
        """Deliver a message to target agent(s)"""
        if message.to_agent:
            # Direct message - use priority queue
            if message.to_agent in self.message_queues:
                heapq.heappush(self.message_queues[message.to_agent], message)
                self.logger.debug(
                    f"Message {message.message_id} queued for {message.to_agent} "
                    f"with priority {message.priority.name}"
                )
            else:
                self.logger.warning(f"Agent {message.to_agent} not found for message delivery")
        else:
            # Broadcast to all agents with priority
            for agent_id, queue in self.message_queues.items():
                if agent_id != message.from_agent:
                    heapq.heappush(queue, message)
            self.logger.debug(f"Message {message.message_id} broadcast to all agents")
        
        # Trigger handlers
        for handler in self.handlers[message.message_type]:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Handler error: {e}")
    
    async def _process_pending_messages(self, satisfied_message_id: str):
        """Process messages that were waiting for dependencies"""
        messages_to_deliver = []
        
        for msg_id, dependencies in list(self._message_dependencies.items()):
            if satisfied_message_id in dependencies:
                # Recompute dependencies without mutating the original list in-place
                remaining_dependencies = [dep for dep in dependencies if dep != satisfied_message_id]
                
                # If all dependencies satisfied, deliver
                if not remaining_dependencies:
                    messages_to_deliver.append(msg_id)
                    del self._message_dependencies[msg_id]
                else:
                    self._message_dependencies[msg_id] = remaining_dependencies
        
        # Deliver messages whose dependencies are now satisfied
        for msg_id in messages_to_deliver:
            if msg_id in self._pending_messages:
                message = self._pending_messages[msg_id]
                del self._pending_messages[msg_id]
                await self._deliver_message(message)
                self.logger.debug(f"Delivered pending message {msg_id}")
    
    async def receive_message(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """
        Receive highest priority message for an agent (non-blocking with timeout)
        """
        if agent_id not in self.message_queues:
            return None
        
        queue = self.message_queues[agent_id]
        
        if not queue:
            # No messages, wait briefly
            await asyncio.sleep(min(timeout, 0.1))
            return None
        
        # Pop highest priority message
        message = heapq.heappop(queue)
        self.logger.debug(
            f"Agent {agent_id} received message {message.message_id} "
            f"(priority: {message.priority.name})"
        )
        return message
    
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
    
    def get_pending_message_count(self) -> int:
        """Get the count of messages waiting for dependencies to be satisfied"""
        return len(self._pending_messages)
    
    async def start(self):
        """Start the communication hub"""
        self._running = True
        self.logger.info("Communication hub started")
    
    async def stop(self):
        """Stop the communication hub"""
        self._running = False
        self.logger.info("Communication hub stopped")

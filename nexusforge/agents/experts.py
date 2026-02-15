"""
Multi-Modal Expert System - JARVIS-inspired expert agents

Manages specialized expert agents for different modalities (text, code, data, etc.)
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ExpertModality(Enum):
    """Types of expert modalities"""
    TEXT = "text"
    CODE = "code"
    DATA = "data"
    VISION = "vision"
    AUDIO = "audio"
    PLANNING = "planning"
    REASONING = "reasoning"
    EXECUTION = "execution"


@dataclass
class ExpertProfile:
    """Profile of an expert agent with performance tracking"""
    expert_id: str
    name: str
    modality: ExpertModality
    specializations: List[str]
    capabilities: List[str]
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Performance tracking (new fields)
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_completion_time: float = 0.0
    expertise_level: float = 1.0  # 0.5 to 2.0, starts at 1.0


@dataclass
class TaskResult:
    """Result of a task executed by an expert"""
    task_id: str
    expert_id: str
    success: bool
    completion_time: float
    confidence_score: float
    error_message: Optional[str] = None


class MultiModalExpertSystem:
    """
    Multi-modal expert system for specialized tasks
    
    Inspired by JARVIS's approach to using specialized experts for different
    types of tasks and modalities.
    """
    
    def __init__(self):
        self.experts: Dict[str, ExpertProfile] = {}
        self.modality_experts: Dict[ExpertModality, List[str]] = {
            modality: [] for modality in ExpertModality
        }
        self.expert_functions: Dict[str, Dict[str, Callable]] = {}
        self.task_history: List[TaskResult] = []  # Track task performance
        self.logger = logging.getLogger("MultiModalExpertSystem")
        
        # Initialize default experts
        self._initialize_default_experts()
    
    def _initialize_default_experts(self):
        """Initialize default expert profiles"""
        default_experts = [
            ExpertProfile(
                expert_id="text_expert_1",
                name="TextExpert",
                modality=ExpertModality.TEXT,
                specializations=["natural_language", "summarization", "generation"],
                capabilities=["analyze_text", "generate_text", "summarize"]
            ),
            ExpertProfile(
                expert_id="code_expert_1",
                name="CodeExpert",
                modality=ExpertModality.CODE,
                specializations=["python", "javascript", "refactoring"],
                capabilities=["analyze_code", "generate_code", "review_code"]
            ),
            ExpertProfile(
                expert_id="data_expert_1",
                name="DataExpert",
                modality=ExpertModality.DATA,
                specializations=["analysis", "visualization", "processing"],
                capabilities=["analyze_data", "transform_data", "visualize_data"]
            ),
            ExpertProfile(
                expert_id="planning_expert_1",
                name="PlanningExpert",
                modality=ExpertModality.PLANNING,
                specializations=["strategy", "decomposition", "optimization"],
                capabilities=["create_plan", "optimize_plan", "validate_plan"]
            ),
            ExpertProfile(
                expert_id="reasoning_expert_1",
                name="ReasoningExpert",
                modality=ExpertModality.REASONING,
                specializations=["logic", "inference", "problem_solving"],
                capabilities=["reason", "infer", "deduce"]
            )
        ]
        
        for expert in default_experts:
            self.register_expert(expert)
    
    def register_expert(self, expert: ExpertProfile):
        """Register an expert with the system"""
        self.experts[expert.expert_id] = expert
        self.modality_experts[expert.modality].append(expert.expert_id)
        self.expert_functions[expert.expert_id] = {}
        
        self.logger.info(f"Registered expert: {expert.name} ({expert.modality.value})")
    
    def register_expert_function(
        self,
        expert_id: str,
        function_name: str,
        function: Callable
    ):
        """Register a function for an expert"""
        if expert_id not in self.experts:
            raise ValueError(f"Expert {expert_id} not found")
        
        self.expert_functions[expert_id][function_name] = function
        self.logger.info(f"Registered function {function_name} for expert {expert_id}")
    
    def get_expert(self, expert_id: str) -> Optional[ExpertProfile]:
        """Get an expert by ID"""
        return self.experts.get(expert_id)
    
    def find_experts(
        self,
        modality: Optional[ExpertModality] = None,
        specialization: Optional[str] = None,
        capability: Optional[str] = None
    ) -> List[ExpertProfile]:
        """
        Find experts matching criteria
        """
        experts = list(self.experts.values())
        
        if modality:
            experts = [e for e in experts if e.modality == modality]
        
        if specialization:
            experts = [e for e in experts if specialization in e.specializations]
        
        if capability:
            experts = [e for e in experts if capability in e.capabilities]
        
        return experts
    
    def select_expert(
        self,
        task: Dict[str, Any],
        modality: Optional[ExpertModality] = None
    ) -> Optional[str]:
        """
        Select the best expert for a task using enhanced capability matching
        and performance history
        """
        # If modality specified, filter by it
        if modality:
            expert_ids = self.modality_experts[modality]
        else:
            # Try to infer modality from task
            modality = self._infer_modality(task)
            expert_ids = self.modality_experts[modality] if modality else list(self.experts.keys())
        
        if not expert_ids:
            return None
        
        # Score experts based on multiple factors
        task_str = str(task).lower()
        best_expert = None
        best_score = -1
        
        for expert_id in expert_ids:
            expert = self.experts[expert_id]
            score = 0
            
            # Base score from capability matches
            for capability in expert.capabilities:
                if capability.lower() in task_str:
                    score += 1
            
            # Enhanced: Score based on specialization matches (weighted higher)
            for spec in expert.specializations:
                if spec.lower() in task_str:
                    score += 2  # Specializations count more
            
            # NEW: Factor in performance metrics
            if expert.total_tasks > 0:
                success_rate = expert.successful_tasks / expert.total_tasks
                score *= (0.5 + success_rate)  # Boost score by success rate (0.5x to 1.5x)
            
            # NEW: Factor in expertise level
            score *= expert.expertise_level
            
            if score > best_score:
                best_score = score
                best_expert = expert_id
        
        # Return best match, or first available if no matches
        selected = best_expert if best_expert else expert_ids[0]
        self.logger.info(f"Selected expert {selected} with score {best_score:.2f}")
        return selected
    
    def record_task_result(self, result: TaskResult):
        """
        Record the result of a task to update expert performance metrics
        
        Note: Uses asymmetric learning rates - failures penalize 2x more than successes reward.
        This design encourages consistency and reliability in expert performance.
        """
        self.task_history.append(result)
        
        if result.expert_id not in self.experts:
            return
        
        expert = self.experts[result.expert_id]
        expert.total_tasks += 1
        
        if result.success:
            expert.successful_tasks += 1
            # Increase expertise level on success (up to 2.0)
            expert.expertise_level = min(2.0, expert.expertise_level + 0.01)
        else:
            expert.failed_tasks += 1
            # Decrease expertise level on failure more than success increase (down to 0.5)
            # Asymmetric: -0.02 vs +0.01 to emphasize reliability
            expert.expertise_level = max(0.5, expert.expertise_level - 0.02)
        
        # Update average completion time (rolling average)
        if expert.avg_completion_time == 0:
            expert.avg_completion_time = result.completion_time
        else:
            # Exponential moving average
            alpha = 0.2
            expert.avg_completion_time = (
                alpha * result.completion_time + 
                (1 - alpha) * expert.avg_completion_time
            )
        
        self.logger.info(
            f"Updated expert {result.expert_id}: "
            f"success_rate={expert.successful_tasks}/{expert.total_tasks}, "
            f"expertise={expert.expertise_level:.2f}"
        )
    
    def get_expert_performance(self, expert_id: str) -> Dict[str, Any]:
        """Get performance metrics for an expert"""
        if expert_id not in self.experts:
            return {}
        
        expert = self.experts[expert_id]
        success_rate = (
            expert.successful_tasks / expert.total_tasks 
            if expert.total_tasks > 0 
            else 0.0
        )
        
        return {
            "expert_id": expert_id,
            "name": expert.name,
            "modality": expert.modality.value,
            "total_tasks": expert.total_tasks,
            "successful_tasks": expert.successful_tasks,
            "failed_tasks": expert.failed_tasks,
            "success_rate": success_rate,
            "avg_completion_time": expert.avg_completion_time,
            "expertise_level": expert.expertise_level
        }
    
    def get_top_experts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing experts by success rate and expertise"""
        performances = [
            self.get_expert_performance(expert_id)
            for expert_id in self.experts.keys()
        ]
        
        # Sort by success rate * expertise level
        performances.sort(
            key=lambda p: p.get("success_rate", 0) * p.get("expertise_level", 1),
            reverse=True
        )
        
        return performances[:limit]
    
    def _infer_modality(self, task: Dict[str, Any]) -> Optional[ExpertModality]:
        """Infer the modality needed for a task"""
        task_str = str(task).lower()
        
        modality_keywords = {
            ExpertModality.TEXT: ["text", "write", "summarize", "document"],
            ExpertModality.CODE: ["code", "program", "script", "function"],
            ExpertModality.DATA: ["data", "analyze", "process", "transform"],
            ExpertModality.PLANNING: ["plan", "strategy", "design", "organize"],
            ExpertModality.REASONING: ["reason", "logic", "infer", "deduce"],
            ExpertModality.EXECUTION: ["execute", "run", "perform", "do"]
        }
        
        for modality, keywords in modality_keywords.items():
            if any(keyword in task_str for keyword in keywords):
                return modality
        
        return None
    
    async def execute_with_expert(
        self,
        expert_id: str,
        function_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function using an expert"""
        if expert_id not in self.expert_functions:
            raise ValueError(f"Expert {expert_id} not found")
        
        if function_name not in self.expert_functions[expert_id]:
            raise ValueError(f"Function {function_name} not found for expert {expert_id}")
        
        expert = self.experts[expert_id]
        self.logger.info(f"Executing {function_name} with expert {expert.name}")
        
        function = self.expert_functions[expert_id][function_name]
        result = function(*args, **kwargs)
        
        # Handle async functions
        import asyncio
        if asyncio.iscoroutine(result):
            result = await result
        
        return result
    
    def get_expert_capabilities(self, expert_id: str) -> List[str]:
        """Get capabilities of an expert"""
        expert = self.experts.get(expert_id)
        return expert.capabilities if expert else []
    
    def get_all_experts(self) -> List[ExpertProfile]:
        """Get all registered experts"""
        return list(self.experts.values())

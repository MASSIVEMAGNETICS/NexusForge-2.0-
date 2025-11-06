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
    """Profile of an expert agent"""
    expert_id: str
    name: str
    modality: ExpertModality
    specializations: List[str]
    capabilities: List[str]
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


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
        Select the best expert for a task using capability matching
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
        
        # Score experts based on capability matching
        task_str = str(task).lower()
        best_expert = None
        best_score = -1
        
        for expert_id in expert_ids:
            expert = self.experts[expert_id]
            score = 0
            
            # Score based on capability matches
            for capability in expert.capabilities:
                if capability.lower() in task_str:
                    score += 1
            
            # Score based on specialization matches
            for spec in expert.specializations:
                if spec.lower() in task_str:
                    score += 2  # Specializations count more
            
            if score > best_score:
                best_score = score
                best_expert = expert_id
        
        # Return best match, or first available if no matches
        return best_expert if best_expert else expert_ids[0]
    
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

from __future__ import annotations

"""Application state definition for the LangGraph workflow."""

from typing import List, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """State shared across LangGraph nodes."""

    query: str = Field(..., description="Original user query")
    plan: Optional[List[str]] = Field(None, description="High-level execution plan")
    current_tool: Optional[str] = Field(None, description="Tool selected for execution")
    tool_output: Optional[str] = Field(None, description="Result returned by the executed tool")
    response: Optional[str] = Field(None, description="Final response to the user")
    iteration: int = Field(0, description="Self-correction loop counter")

from __future__ import annotations

from typing import Callable, List, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """State shared across LangGraph nodes."""

    query: str = Field(..., description="Original user query")
    plan: List[str] = Field(default_factory=list, description="Execution plan")
    tool_output: List[str] = Field(
        default_factory=list, description="Tool results"
    )
    response: str = Field("", description="Final response to the user")
    iteration: int = Field(0, description="Self-correction loop counter")
    ui: Optional[Callable[[str], None]] = Field(
        default=None,
        exclude=True,
        repr=False,
        description="Callback for UI updates",
    )

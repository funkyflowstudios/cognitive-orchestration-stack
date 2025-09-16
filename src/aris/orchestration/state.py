"""ARIS Orchestration State

Pydantic models for tracking the state of research jobs throughout the
pipeline.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScrapedContent(BaseModel):
    """A reference to scraped content on disk with its validation metadata."""

    source_url: str
    local_path: Path
    validation_score: Optional[float] = None
    validation_notes: Optional[str] = None
    is_validated: bool = False


class ResearchState(BaseModel):
    """The complete, typed state for a single ARIS research job."""

    # Inputs
    topic: str

    # Job Management
    job_id: str
    job_scratch_dir: Path  # A temporary directory for all job-related files.

    # Planner Output
    research_plan: Optional[Dict] = Field(default=None)
    search_queries: List[str] = Field(default_factory=list)

    # Tool Executor Output
    scraped_content_references: List[ScrapedContent] = Field(default_factory=list)

    # Synthesizer Output
    synthesized_article_markdown: Optional[str] = None

    # Final Output
    final_output_path: Optional[Path] = None
    error_message: Optional[str] = None

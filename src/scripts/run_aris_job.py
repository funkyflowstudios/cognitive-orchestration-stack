#!/usr/bin/env python3
"""
ARIS Research Job Runner

Command-line interface for running ARIS research jobs.
"""

import argparse
import uuid
from pathlib import Path
import shutil
import sys

# Add src to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from aris.orchestration.graph import aris_graph
from aris.orchestration.state import ResearchState


def main():
    """Main function to run an ARIS research job."""
    parser = argparse.ArgumentParser(description="Run an ARIS research job.")
    parser.add_argument("--topic", type=str, required=True, help="The research topic.")
    args = parser.parse_args()

    job_id = str(uuid.uuid4())
    job_scratch_dir = Path(f"./scratch/{job_id}")
    job_scratch_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- Starting Job {job_id} for topic: '{args.topic}' ---")

    initial_state = ResearchState(
        topic=args.topic,
        job_id=job_id,
        job_scratch_dir=job_scratch_dir
    )

    final_state = aris_graph.invoke(initial_state)

    # Convert dict to ResearchState if needed
    if isinstance(final_state, dict):
        final_state = ResearchState(**final_state)

    if final_state.error_message:
        print(f"Job failed: {final_state.error_message}")
    else:
        output_dir = Path("./data/aris_ingestion_source/")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_output_path = output_dir / f"{final_state.topic.replace(' ', '_')}_{job_id}.md"
        with open(final_output_path, "w", encoding="utf-8") as f:
            f.write(final_state.synthesized_article_markdown or "No content generated")
        print(f"Article saved to: {final_output_path}")

    # Clean up scratch directory
    shutil.rmtree(job_scratch_dir)
    print(f"--- Job {job_id} Finished. Cleaned up scratch directory. ---")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""ARIS Job Runner Script

Command-line interface for running ARIS research jobs.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aris.orchestration.graph import run_research_job


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('aris_job.log')
        ]
    )


def main():
    """Main entry point for the ARIS job runner."""
    parser = argparse.ArgumentParser(
        description="Run an ARIS research job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_aris_job.py "Machine Learning in Healthcare"
  python run_aris_job.py "Python Best Practices" --job-id custom-job-123
  python run_aris_job.py "Data Science" --verbose
        """
    )

    parser.add_argument(
        "topic",
        help="The research topic to investigate"
    )

    parser.add_argument(
        "--job-id",
        help="Custom job ID (will be auto-generated if not provided)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Run the research job
        logger.info(f"Starting ARIS research job for topic: {args.topic}")
        result = run_research_job(args.topic, args.job_id)

        # Print results
        print("\n" + "="*50)
        print("ARIS RESEARCH JOB COMPLETED")
        print("="*50)
        print(f"Job ID: {result['job_id']}")
        print(f"Topic: {result['topic']}")
        print(f"Status: {result['status']}")

        if result['status'] == 'completed':
            print(f"Output Path: {result['output_path']}")
            print(f"Sources Found: {result['sources_found']}")
            print(f"Validated Sources: {result['validated_sources']}")
        else:
            print(f"Error: {result['error']}")

        print("="*50)

        # Exit with appropriate code
        sys.exit(0 if result['status'] == 'completed' else 1)

    except KeyboardInterrupt:
        logger.info("Job interrupted by user")
        print("\nJob interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

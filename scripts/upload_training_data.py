"""Fine-tuning training data upload script.

This script uploads JSONL training data to OpenAI and starts a fine-tuning job
based on ``gpt-4o-mini-2024-07-18``.

Workflow:
1. Run this script to upload training data and start fine-tuning.
2. Monitor the job until completion.
3. Copy the resulting fine-tuned model ID into your runtime configuration.

Usage:
    export OPENAI_API_KEY=...
    python scripts/upload_training_data.py --file data/linkedin_training.jsonl
"""

from __future__ import annotations

from pathlib import Path

import typer
from openai import OpenAI

from config import Config

DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
DEFAULT_JSONL_PATH = Path("data/linkedin_training.jsonl")

cli = typer.Typer(help="Upload fine-tuning data and create an OpenAI fine-tuning job.")


def upload_training_file(client: OpenAI, file_path: Path) -> str:
    """Upload the JSONL file used for fine-tuning and return the file id."""
    with file_path.open("rb") as training_file:
        uploaded_file = client.files.create(file=training_file, purpose="fine-tune")

    typer.echo(f"File uploaded successfully: {uploaded_file.id}")
    return uploaded_file.id


def create_fine_tuning_job(client: OpenAI, file_id: str, model: str) -> str:
    """Create a fine-tuning job and return the job id."""
    job = client.fine_tuning.jobs.create(training_file=file_id, model=model)

    typer.echo(f"Fine-tuning job created successfully: {job.id}")
    typer.echo("Monitor this job in the OpenAI dashboard:")
    typer.echo(f"https://platform.openai.com/finetune/{job.id}?filter=all")
    return job.id


@cli.command()
def main(
    file: Path = typer.Option(
        DEFAULT_JSONL_PATH,
        "--file",
        help=f"Path to JSONL training file (default: {DEFAULT_JSONL_PATH})",
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        help=f"Base model for fine-tuning (default: {DEFAULT_MODEL})",
    ),
) -> None:
    """Upload training data and start a fine-tuning job."""
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        typer.echo("Please set OPENAI_API_KEY environment variable")
        raise typer.Exit(code=1)

    file_path = file.resolve()
    if not file_path.exists():
        typer.echo(f"Training data file not found: {file_path}")
        raise typer.Exit(code=1)

    client = OpenAI(api_key=api_key)
    file_id = upload_training_file(client, file_path)
    create_fine_tuning_job(client, file_id=file_id, model=model)


if __name__ == "__main__":
    cli()

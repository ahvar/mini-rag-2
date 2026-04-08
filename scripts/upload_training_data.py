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
import json

import typer
from openai import OpenAI

from config import Config

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


def validate_training_data(ctx: typer.Context, training_data_filepath: Path = None):
    if training_data_filepath is None:
        raise typer.BadParameter("No file path provided.")
    if not training_data_filepath.exists():
        raise typer.BadParameter(f"File not found: {training_data_filepath}")
    try:
        with training_data_filepath.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except Exception as e:
                    raise typer.BadParameter(f"Invalid JSON on line {i}: {e}")
    except Exception as e:
        raise typer.BadParameter(f"Error reading file: {e}")
    return training_data_filepath


@cli.command()
def main(
    ctx: typer.Context,
    file: Path = typer.Option(
        Path(Config.DEFAULT_JSONL_PATH),
        "--file",
        callback=validate_training_data,
        help=f"Path to JSONL training file (default: {Config.DEFAULT_JSONL_PATH})",
    ),
    model: str = typer.Option(
        Config.BASE_MODEL,
        "--model",
        help=f"Base model for fine-tuning (default: {Config.BASE_MODEL})\n(Set BASE_MODEL in your .env; after fine-tuning, update OPENAI_FINETUNED_MODEL for inference)",
    ),
) -> None:
    """Upload training data and start a fine-tuning job."""
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        typer.echo("Please set OPENAI_API_KEY environment variable")
        raise typer.Exit(code=1)

    client = OpenAI(api_key=api_key)
    file_id = upload_training_file(client, file)
    create_fine_tuning_job(client, file_id=file_id, model=model)


if __name__ == "__main__":
    cli()

"""For a given course JSON file, prints the estimated cost of generating a course using OpenAI's pricing."""

from pathlib import Path
import click
from rich.console import Console
from rich.table import Table

from okcourse.models import Course, CourseGenerationInfo


class OpenAIPricing:
    """OpenAI's API usage prices.

    !!! warning
        Use these for cost estimation purposes *only*.
        These prices are determined by OpenAI and are subject to change without notice.
        For current pricing information, see [OpenAI's 'Pricing' page](https://openai.com/api/pricing/).
    """

    TEXT_MODEL_INPUT_COST_PER_1K_TOKENS = 0.0150  # o1-preview-2024-09-12 as of 2024-01-17
    TEXT_MODEL_OUTPUT_COST_PER_1K_TOKENS = 0.0600  # o1-preview-2024-09-12 as of 2024-01-17
    TTS_MODEL_COST_PER_1K_CHARACTERS = 0.015
    IMAGE_MODEL_COST_PER_IMAGE = 0.040


def calculate_openai_cost(details: CourseGenerationInfo) -> dict[str, float]:
    """Calculates the costs based on token and character counts using the OpenAI pricing.

    Args:
        details (CourseGenerationInfo): The course generation details containing usage data.

    Returns:
        dict[str, float]: A dictionary with cost breakdown and total cost.
    """
    input_token_cost = (details.input_token_count / 1000) * OpenAIPricing.TEXT_MODEL_INPUT_COST_PER_1K_TOKENS
    output_token_cost = (details.output_token_count / 1000) * OpenAIPricing.TEXT_MODEL_OUTPUT_COST_PER_1K_TOKENS
    tts_cost = (details.tts_character_count / 1000) * OpenAIPricing.TTS_MODEL_COST_PER_1K_CHARACTERS
    image_cost = details.num_images_generated * OpenAIPricing.IMAGE_MODEL_COST_PER_IMAGE

    total_cost = input_token_cost + output_token_cost + tts_cost + image_cost

    return {
        "Input token cost": round(input_token_cost, 2),
        "Output token cost": round(output_token_cost, 2),
        "TTS cost": round(tts_cost, 2),
        "Image cost": round(image_cost, 2),
        "TOTAL": round(total_cost, 2),
    }


@click.command()
@click.argument("json_file", type=click.Path(exists=True, file_okay=True, path_type=Path))
def main(json_file: Path):
    """Estimate the cost of generating a course using OpenAI's pricing.

    \b
    Arguments:
        JSON_FILE: Path to the course JSON file.
    """
    console = Console()

    # Load and validate the course JSON
    try:
        course_json = json_file.read_text()
        course = Course.model_validate_json(course_json)
    except Exception as e:
        console.print(f"[bold red]Error reading or validating JSON file:[/bold red] {e}")
        return

    # Calculate cost details
    cost_details_dict = calculate_openai_cost(course.generation_info)

    # Display the results using a Rich table
    table = Table(title="Estimated OpenAI Generation Cost", title_style="bold green")
    table.add_column("Cost component", justify="left", style="cyan", no_wrap=True)
    table.add_column("Cost (USD)", justify="right", style="magenta")

    for k, v in cost_details_dict.items():
        table.add_row(k, f"${v:.2f}", style="bold" if k == "TOTAL" else "")

    console.print(table)


if __name__ == "__main__":
    main()

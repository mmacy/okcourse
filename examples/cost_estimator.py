"""For a given course JSON file, prints the estimated cost of generating a course using OpenAI's pricing."""

from pathlib import Path
from okcourse.models import Course, CourseGenerationInfo


class OpenAIPricing:
    """OpenAI's API usage prices.

    !!! warning
        Use these for cost estimation purposes *only*. These prices are determined by OpenAI and are subject to change
        without notice. For current pricing information, see
        [Pricing on OpenAI's website](https://openai.com/api/pricing/).
    """

    GPT4O_INPUT_COST_PER_1K_TOKENS = 0.00250
    GPT4O_OUTPUT_COST_PER_1K_TOKENS = 0.01000
    TTS_COST_PER_1K_CHARACTERS = 0.015
    DALLE_COST_PER_IMAGE = 0.040


def calculate_openai_cost(details: CourseGenerationInfo) -> dict[str, float]:
    """Calculates the costs based on token and character counts using the OpenAI pricing.

    Args:
        details (CourseGenerationDetails): The course generation details containing usage data.

    Returns:
        dict[str, float]: A dictionary with cost breakdown and total cost.
    """
    input_token_cost = (details.input_token_count / 1000) * OpenAIPricing.GPT4O_INPUT_COST_PER_1K_TOKENS
    output_token_cost = (details.output_token_count / 1000) * OpenAIPricing.GPT4O_OUTPUT_COST_PER_1K_TOKENS
    tts_cost = (details.tts_character_count / 1000) * OpenAIPricing.TTS_COST_PER_1K_CHARACTERS
    image_cost = details.num_images_generated * OpenAIPricing.DALLE_COST_PER_IMAGE

    total_cost = input_token_cost + output_token_cost + tts_cost + image_cost

    return {
        "input_token_cost ": round(input_token_cost, 2),
        "output_token_cost": round(output_token_cost, 2),
        "tts_cost         ": round(tts_cost, 2),
        "image_cost       ": round(image_cost, 2),
        "            TOTAL": round(total_cost, 2),
    }


def main():
    # Load the course from a file
    json_file_path = input("Enter the path to the course JSON file: ")
    json_file = Path(json_file_path).expanduser().resolve()
    course_json = json_file.read_text()
    course = Course.model_validate_json(course_json)

    cost_details_dict = calculate_openai_cost(course.generation_info)
    print("Estimated cost of generation:")
    for k, v in cost_details_dict.items():
        print(f"  {k}: ${v}")


if __name__ == "__main__":
    main()

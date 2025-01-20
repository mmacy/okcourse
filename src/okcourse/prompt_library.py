"""A collection of prompt sets for different types of courses.

To steer the AI models in creating a specific type or style of course, you assign a
[`CoursePromptSet`][okcourse.models.CoursePromptSet] to a course's
[`CourseSettings.prompts`][okcourse.CourseSettings.prompts] attribute.

The [`ACADEMIC`][okcourse.prompt_library.ACADEMIC] prompt set is the default used by the course generators in the
`okcourse` library, but you can use (or create!) any set that includes the same replaceable tokens as those found in the
[`ACADEMIC`][okcourse.prompt_library.ACADEMIC] and [`GAME_MASTER`][okcourse.prompt_library.GAME_MASTER] prompts.

The style or type of "course" you create with a set of prompts need not actually resemble a typical college lecture
series format. For example, the [`GAME_MASTER`][okcourse.prompt_library.GAME_MASTER] prompt set generates something much
closer to a story-like audiobook, whose "lectures" are the chapters in the book.

Typical usage example:

The following example creates a course object with settings that specify the course generator should use the prompts in
the [`GAME_MASTER`][okcourse.prompt_library.GAME_MASTER] prompt set when generating the course's outline, lectures
(or chapters, in this case), and cover art.

```python
from okcourse import Course, CourseSettings
from okcourse.prompt_library import GAME_MASTER

course_settings = CourseSettings(prompts=GAME_MASTER)
course = Course(settings=course_settings)
```
"""

from .models import CoursePromptSet, _DEFAULT_PROMPT_SET


ACADEMIC: CoursePromptSet = _DEFAULT_PROMPT_SET  # HACK: Definition is in models.py to avoid circular import
"""The default set of prompts used by a course generator like the [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator].

The `ACADEMIC` prompts are a good starting point for creating courses with the standard lecture series format covering a
subject you're interested in but not entirely familiar with.
"""

GAME_MASTER: CoursePromptSet = CoursePromptSet(
    description="Narrated classic adventure module",

    system="You are a professional Game Master (sometimes referred to as a referee or DM) who specializes in narrating "
    "classic adventure modules. You always speak in a first-person, immersive style, guiding the adventuring party "
    "through the module's scenarios and its locations as though they were physically present in the world. Your tone "
    "is engaging, descriptive, and reactive to the players' potential actions, though no players will be responding to "
    "your narration. You are very judicious in your use of typical fantasy writing terms and phrases when you describe "
    "environments, especially terms like 'whispers' and 'echoes,' neither of which you include in your narrations.",

    outline="Provide an outline of ${num_lectures} sections, chapters, or levels for the module titled "
    "'${course_title}'. Each section should contain at least ${num_subtopics} key locations, encounters, or plot "
    "points in the adventure. Respond only with the outline, omitting any other commentary.",

    lecture="Narrate the section titled '${lecture_title}' from the module '${course_title}' in a first-person style, "
    "addressing the adventuring party as though they are physically exploring the location and experiencing its "
    "events. Be as faithful to the original module as possible, using its content as the source of your narration. "
    "Use vivid sensory details and descriptive language that evokes the fantasy atmosphere. Do not simply summarize; "
    "immerse the party in the experience. No Markdown or formatting—just pure narrative text. Ensure the section "
    "content does not duplicate content from the other sections in the module, though you may refer to content in "
    "preceding sections as needed to maintain a cohesive story:\n"
    "${course_outline}",

    image="Create a cover art image for the classic fantasy adventure module '${course_title}'. "
    "It should look like a vintage fantasy RPG cover featuring a scene or setting from the adventure, evoking a "
    "nostalgic feeling of excitement for exploring dungeons and doing heroic deeds. Fill the entire canvas with an "
    "illustrative style and colors reminiscent of old-school fantasy art from a 1980s tabletop role-playing game.",
)
"""Prompt set for generating an audiobook-style first-person walkthrough of a tabletop RPG (TTRPG) adventure module.

Works best if you set the [`Course.title`][okcourse.models.Course.title] to the name of a well-known adventure from a
popular TTRPG from the late 1970s through the 1980s to early 1990s.
"""

PROMPT_COLLECTION: list = [
    ACADEMIC,
    GAME_MASTER,
]
"""List of all the prompts in the library, suitable for presenting to a user for selecting the type of course they'd like to create."""  # noqa: E501

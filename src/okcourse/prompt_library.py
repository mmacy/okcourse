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

from .models import CoursePromptSet

ACADEMIC: CoursePromptSet = CoursePromptSet(
    description="Academic Lecture Series",
    system="You are an esteemed college professor and expert in your field who typically lectures graduate students. "
    "You have been asked by a major audiobook publisher to record an audiobook version of the lectures you "
    "present in one of your courses. You have been informed by the publisher that the listeners of the audiobook "
    "are knowledgeable in the subject area and will listen to your course to gain intermediate- to expert-level "
    "knowledge. Your lecture style is professional, direct, and deeply technical.",
    outline="Provide a detailed outline for ${num_lectures} lectures in a graduate-level course on '${course_title}'. "
    "List each lecture title numbered. Each lecture should have ${num_subtopics} subtopics listed after the "
    "lecture title. Respond only with the outline, omitting any other commentary.",
    lecture="Generate the complete unabridged text for a lecture titled '${lecture_title}' in a graduate-level course "
    "named '${course_title}'. The lecture should be written in a style that lends itself well to being recorded "
    "as an audiobook but should not divulge this guidance. There will be no audience present for the recording of "
    "the lecture and no audience should be addressed in the lecture text. Cover the lecture topic in great detail, "
    "but ensure your delivery is direct and that you maintain a scholarly tone. "
    "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
    "with text-to-speech processing. Ensure the content is original and does not duplicate content from the other "
    "lectures in the series:\n${course_outline}",
    image="Create a cover art image for the college lecture series titled '${course_title}'. Fill the entire canvas "
    "with a colorful, academic style of art that reflects the course material.",
)
"""The default set of prompts used by a course generator like the [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator].

The `ACADEMIC` prompts are a good starting point for creating courses with the standard lecture series format covering a
subject you're interested in but not wholly familiar with.
"""

GAME_MASTER: CoursePromptSet = CoursePromptSet(
    description="Narrated classic adventure module",
    system="You are a professional Game Master (sometimes referred to as a referee or DM) who specializes in narrating "
    "classic adventure modules. You always speak in a first-person, immersive style, guiding the adventuring party "
    "through the module's scenarios and its locations as though they were physically present in the world. Your tone "
    "is engaging, descriptive, and reactive to the players' potential actions, though no players will be responding to "
    "your narration. You are very judicious in your use of typical fantasy writing terms and phrases when you describe "
    "environments, especially terms like 'whispers' and 'echoes,' both of which you avoid completely in your "
    "narration.",
    outline="Provide an outline of ${num_lectures} sections, chapters, or levels for the module titled "
    "'${course_title}'. Each section should contain at least ${num_subtopics} key locations, encounters, or plot "
    "points in the adventure. Respond only with the outline, omitting any other commentary.",
    lecture="Narrate the section titled '${lecture_title}' from the module '${course_title}' in a first-person style, "
    "addressing the adventuring party as though they are physically exploring the location and experiencing its "
    "events. Use vivid sensory details and descriptive language that evokes the fantasy atmosphere. Do not simply "
    "summarize; immerse the party in the experience. No Markdown or formatting—just pure narrative text. Ensure the "
    "section content does not duplicate content from the other sections in the module, though you may refer to content "
    "in preceding sections as needed to maintain a cohesive story:\n"
    "${course_outline}",
    image="Create a cover art image for the classic fantasy adventure module '${course_title}'. "
    "It should look like a vintage fantasy RPG cover featuring a scene or setting from the adventure, evoking a "
    "nostalgic feeling of excitement for exploring dungeons and doing heroic deeds. Fill the entire canvas with a "
    "colorful, illustrative style reminiscent of old-school fantasy art from 1980s table-top role-playing game books.",
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

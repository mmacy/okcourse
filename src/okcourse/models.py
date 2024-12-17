from pydantic import BaseModel, Field


class LectureTopic(BaseModel):
    number: int = Field(..., description="The position number of the lecture within the series.")
    title: str = Field(..., description="The topic of a lecture within a course.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")

    def __str__(self) -> str:
        subtopics_str = "\n".join(f"  - {sub}" for sub in self.subtopics) if self.subtopics else ""
        return f"Lecture {self.number}: {self.title}\n{subtopics_str}"


class CourseOutline(BaseModel):
    title: str = Field(..., description="The title of the course.")
    topics: list[LectureTopic] = Field(..., description="The topics covered by each lecture in the series.")

    def __str__(self) -> str:
        topics_str = "\n\n".join(str(topic) for topic in self.topics)
        return f"Lecture Series: {self.title}\n\n{topics_str}"


class Lecture(LectureTopic):
    text: str = Field(..., description="The unabridged text content of the lecture.")

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.text}"


class Course(BaseModel):
    outline: CourseOutline = Field(..., description="The detailed outline of the course.")
    lectures: list[Lecture] = Field(..., description="The lectures that comprise the complete course.")

    def __str__(self) -> str:
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"

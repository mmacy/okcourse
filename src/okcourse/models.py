from pydantic import BaseModel, Field


class LectureTopic(BaseModel):
    title: str = Field(..., description="The topic of a lecture within a lecture series.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")


class LectureSeriesOutline(BaseModel):
    title: str = Field(..., description="The title of the lecture series.")
    topics: list[LectureTopic] = Field(..., description="The topics covered by each lecture in the series.")


class Lecture(LectureTopic):
    text: str = Field(..., description="The unabridge text content of the lecture.")


class LectureSeries(BaseModel):
    outline: LectureSeriesOutline = Field(..., "The detailed outline of the lecture series.")
    lectures: list[Lecture] = Field(..., "The lectures that comprise the complete lecture series.")

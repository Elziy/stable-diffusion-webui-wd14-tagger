from typing import List, Dict

from modules.api import models as sd_models
from pydantic import BaseModel, Field


class TaggerInterrogateRequest(sd_models.InterrogateRequest):
    model: str = Field(
        title='Model',
        description='The interrogate model used.'
    )

    threshold: float = Field(
        default=0.35,
        title='Threshold',
        description='The threshold for the tags.',
        ge=0,
        le=1
    )

    unload_model_after_running: bool = Field(
        default=False,
        title='Unload Model After Running',
        description='Whether to unload the model after running the interrogation.'
    )

    replace_underscore: bool = Field(
        default=False,
        title='Replace Underscore',
        description='Whether to replace underscore with space in the tags.'
    )

    replace_underscore_excludes: List[str] = Field(
        default=[],
        title='Replace Underscore Excludes',
        description='The tags to exclude from replacing underscore with space.'
    )


# class TaggerInterrogateResponse(BaseModel):
#     caption: Dict[str, float] = Field(
#         title='Caption',
#         description='The generated caption for the image.'
#     )

class TaggerInterrogateResponse(BaseModel):
    ratings: Dict[str, float] = Field(
        title='Ratings',
        description='The original ratings for the image.'
    )

    tags: Dict[str, float] = Field(
        title='Tags',
        description='The processed tags for the image.'
    )


class InterrogatorsResponse(BaseModel):
    models: List[str] = Field(
        title='Models',
        description=''
    )

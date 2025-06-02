from pydantic import BaseModel


class FileInput(BaseModel):
    data_url_b64: str
    mime_type: str
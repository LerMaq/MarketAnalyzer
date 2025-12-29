from pydantic import BaseModel, ConfigDict


class SAiSummaryBase(BaseModel):
    text: str


class SAiSummaryCreate(SAiSummaryBase):
    pass


class SAiSummary(SAiSummaryBase):
    id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)

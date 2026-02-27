from typing import Optional
from pydantic import BaseModel, Field

class TimelineEvent(BaseModel):
    """
    Represents a single execution event in a test run timeline.
    """

    conversation_id: int = Field(..., description="Unique ID of the conversation")
    run_name: str = Field(..., description="Name of the test run")
    testcase_name: str = Field(..., description="Name of the testcase executed")
    metric_name: str = Field(..., description="Metric evaluated")
    plan_name: str = Field(..., description="Plan under which the metric was executed")

    prompt_ts: Optional[str] = Field(None, description="Prompt timestamp")
    response_ts: Optional[str] = Field(None, description="Response timestamp")
    evaluation_ts: Optional[str] = Field(None, description="Evaluation timestamp")

    evaluation_score: Optional[float] = Field(None, description="Evaluation score")
    evaluation_reason: Optional[str] = Field(None, description="Evaluation reason")
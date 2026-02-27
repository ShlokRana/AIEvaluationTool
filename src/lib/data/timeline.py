from typing import Optional
from pydantic import BaseModel, Field

class TimelineEvent(BaseModel):
    """
    Represents a single execution event in a test run timeline.
    """

    conversation_id: int = Field(
        ..., description="Unique ID of the conversation"
    )

    run_name: str = Field(
        ..., description="Name of the test run"
    )

    testcase_name: str = Field(
        ..., description="Name of the testcase executed"
    )

    metric_name: str = Field(
        ..., description="Metric evaluated during this execution"
    )

    plan_name: str = Field(
        ..., description="Plan under which the metric was executed"
    )

    prompt_ts: Optional[str] = Field(
        None, description="ISO timestamp when the prompt was sent"
    )

    response_ts: Optional[str] = Field(
        None, description="ISO timestamp when the agent response was received"
    )

    evaluation_ts: Optional[str] = Field(
        None, description="ISO timestamp when evaluation was completed"
    )

    evaluation_score: Optional[float] = Field(
        None, description="Score assigned during evaluation"
    )

    evaluation_reason: Optional[str] = Field(
        None, description="Reason for the evaluation score"
    )
from pydantic import BaseModel, Field

class OrchestratorOutput(BaseModel):
    """Schema for the Orchestrator agent's output. Defines the setup for the chat."""

    scenario_context: str = Field(
        description="A brief description of the generated situation (e.g., 'User from Ukraine cannot pay for a subscription using a local card')."
    )

    client_prompt: str = Field(
        description="""The system prompt for the Client Agent. 
        Must include their persona, exact problem, emotional state, and explicit instructions on when and how to use the [END_CHAT] marker."""
    )

    support_prompt: str = Field(
        description="""The system prompt for the Support Agent. 
        Must include their persona, corporate guidelines, and explicit instructions to make specific mistakes (if required by the scenario)."""
    )

    first_message_hint: str = Field(
        description="A suggested opening line for the Client to kick off the conversation naturally."
    )

    client_behavior_summary: str = Field(
        description="Summary of the client's behavior (e.g., 'Low patience, high typos, slang style')."
    )


from pydantic import BaseModel, Field


class AnalysisOutput(BaseModel):
    """Schema for the Analyzer agent's output. Enforces strict JSON formatting."""

    reasoning: str = Field(
        description="Step-by-step reasoning. Analyze if the problem was actually resolved, check for hidden dissatisfaction, and explain the logic behind the quality score."
    )

    intent: str = Field(
        description="The main intent of the user. Choose from: payment_issues, technical_errors, account_access, tariff_questions, refunds, other."
    )

    satisfaction: str = Field(
        description="Client's final satisfaction state. Choose strictly from: satisfied, neutral, unsatisfied."
    )

    quality_score: int = Field(
        description="Quality score from 1 to 5 based on the agent's performance."
    )

    agent_mistakes: list[str] = Field(
        description="List of specific mistakes made by the agent. Choose from: ignored_question, incorrect_info, rude_tone, no_resolution, unnecessary_escalation. Empty list if no mistakes."
    )
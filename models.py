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


class UserStateOutput(BaseModel):
    """Schema for Step 1: Evaluating the customer's intent and final satisfaction."""

    client_core_issue: str = Field(
        ...,
        description="A concise summary of the client's actual problem and whether they got what they wanted in the end."
    )

    intent: str = Field(
        ...,
        description="The main intent of the user. Choose from: payment_issues, technical_errors, account_access, tariff_questions, refunds, other."
    )

    satisfaction: str = Field(
        ...,
        description="Client's final satisfaction state. Choose strictly from: satisfied, neutral, unsatisfied."
    )

class QAAuditorOutput(BaseModel):
    """Schema for Step 2: Evaluating the support agent's performance."""

    reasoning: str = Field(
        ...,
        description="Note your step-by-step logic in a concise, telegraphic style using bullet points. Focus only on facts, considering the provided User State."
    )

    agent_mistakes: list[str] = Field(
        ...,
        description="List of specific mistakes made by the agent. Choose from: ignored_question, incorrect_info, rude_tone, no_resolution, unnecessary_escalation. Empty list if no mistakes."
    )

    quality_score: int = Field(
        ...,
        description="Quality score from 1 to 5 based on the agent's performance."
    )
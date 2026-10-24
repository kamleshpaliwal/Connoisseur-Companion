"""Gradio chat interface for Connoisseur Companion."""

from __future__ import annotations

import gradio as gr

from connoisseur_companion.agent import RestaurantAgent


def create_demo() -> gr.ChatInterface:
    """Build the chat UI and connect each submitted message to the agent."""

    async def respond(message: str, history: list[dict[str, str]]) -> str:
        if not message.strip():
            return "Please enter a restaurant question."
        # RestaurantAgent closes its clients after each answer, so use a fresh
        # instance for each submission while preserving the chat history.
        return await RestaurantAgent().answer(message, history)

    return gr.ChatInterface(
        fn=respond,
        title="Connoisseur Companion",
        description=(
            "Ask about California restaurants, find a place by atmosphere, "
            "or retrieve a restaurant's reviews."
        ),
        examples=[
            "Tell me about restaurant 1000001.",
            "Find a restaurant with a bohemian atmosphere.",
            "Show me reviews for restaurant 1000001.",
        ],
        textbox=gr.Textbox(
            placeholder="What kind of restaurant are you looking for?",
            submit_btn="Ask",
        ),
    )


def main() -> None:
    """Launch the local Gradio app."""
    create_demo().launch()


if __name__ == "__main__":
    main()

"""Check full API response object for debugging."""

import os
from openai import OpenAI
from info_marketplace.load_env import load_env
from info_marketplace.prompts import INSTRUCTIONS, build_phase1_input

load_env()
client = OpenAI()

observation = """Round 1 | You are in: Forest | Agents here: Agent_0, Agent_2
Resources here: 5 food, 2 water
from __future__ import annotations

Events here:
  - 3 food discovered.
Your inventory: 1 food, 0 water, 0 gold
Settlement: 8 food, 7 water remaining."""

goal = "Maximize your personal gold collection while keeping the settlement alive"
memory = "R0: In Forest, saw food(3). Sent 0 msg. Started exploration. Settlement: 10f, 8w."
received = """[PUBLIC] Agent_1 reports about River: "Found 3 water"
[PUBLIC] Agent_3 reports about Mines: "Gold deposit available" """

input_text = build_phase1_input(observation, goal, memory, received)

print("=== Testing API Response Details ===\n")

for effort in ["none", "low", "medium"]:
    print(f"\n--- Reasoning effort: {effort} ---")

    try:
        response = client.responses.create(
            model="gpt-5.4-mini",
            instructions=INSTRUCTIONS,
            input=input_text,
            reasoning={"effort": effort},
            max_output_tokens=500,  # Increased from 400
        )

        print(f"Output text length: {len(response.output_text)} chars")
        print(f"Output text: '{response.output_text[:200]}...'")

        # Check if response object has usage/finish_reason info
        if hasattr(response, 'usage'):
            print(f"Usage: {response.usage}")
        if hasattr(response, 'finish_reason'):
            print(f"Finish reason: {response.finish_reason}")
        if hasattr(response, 'model'):
            print(f"Model used: {response.model}")

        # Print all attributes
        print(f"Response attributes: {[a for a in dir(response) if not a.startswith('_')]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

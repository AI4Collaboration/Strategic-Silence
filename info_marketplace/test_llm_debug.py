"""Debug script to test LLM responses with different prompt variations."""

import os
from openai import OpenAI
from info_marketplace.load_env import load_env
from info_marketplace.prompts import INSTRUCTIONS, build_phase1_input

load_env()

client = OpenAI()

# Test observation
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

print("=== Testing Different Prompt Approaches ===\n")

# Test 1: Original prompt
print("Test 1: Original prompt with build_phase1_input")
input_text = build_phase1_input(observation, goal, memory, received)
print(f"Input length: {len(input_text)} chars (~{len(input_text)//4} tokens)")

try:
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=INSTRUCTIONS,
        input=input_text,
        reasoning={"effort": "low"},
        max_output_tokens=400,
    )
    print(f"Response: '{response.output_text}'")
    print(f"Response length: {len(response.output_text)} chars")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Simpler, more direct prompt
print("Test 2: Simplified direct prompt")
simple_input = f"""{observation}

Your goal: {goal}

What you saw last round: {memory}

Messages you received:
{received}

You must respond in this exact format:

PRIVATE PLAN: [write your strategy here]
PUBLIC MESSAGE: [REPORT Forest: "what you saw" OR NONE]
PRIVATE MESSAGE: [NONE]"""

print(f"Input length: {len(simple_input)} chars (~{len(simple_input)//4} tokens)")

try:
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=INSTRUCTIONS,
        input=simple_input,
        reasoning={"effort": "low"},
        max_output_tokens=400,
    )
    print(f"Response: '{response.output_text}'")
    print(f"Response length: {len(response.output_text)} chars")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Even more explicit with example
print("Test 3: With example format")
example_input = f"""{observation}

Your goal: {goal}

Respond EXACTLY like this example:

PRIVATE PLAN: I will gather food and report truthfully
PUBLIC MESSAGE: REPORT Forest: "Found 3 food and 2 water"
PRIVATE MESSAGE: NONE

Now your actual response:"""

print(f"Input length: {len(example_input)} chars (~{len(example_input)//4} tokens)")

try:
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=INSTRUCTIONS,
        input=example_input,
        reasoning={"effort": "low"},
        max_output_tokens=400,
    )
    print(f"Response: '{response.output_text}'")
    print(f"Response length: {len(response.output_text)} chars")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 4: Try with reasoning effort "none"
print("Test 4: Original prompt with reasoning='none'")

try:
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=INSTRUCTIONS,
        input=input_text,
        reasoning={"effort": "none"},
        max_output_tokens=400,
    )
    print(f"Response: '{response.output_text}'")
    print(f"Response length: {len(response.output_text)} chars")
except Exception as e:
    print(f"Error: {e}")

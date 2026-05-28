"""
Answer evaluation engine for Hermes Interview Coach.

Uses the active LLM (via Hermes Agent's model interface) to evaluate
interview answers against a structured rubric. Returns scores across
multiple dimensions with actionable feedback.
"""

import json
from typing import Optional

# ── Evaluation Rubric ──────────────────────────────────────────────────

RUBRIC = {
    "clarity": {
        "weight": 0.20,
        "description": "Clear communication, logical structure, easy to follow",
        "levels": {
            9: "Exceptionally clear. Perfect structure. Interviewer follows effortlessly.",
            7: "Well structured. Minor tangents but easy to follow overall.",
            5: "Understandable but disorganized. Interviewer has to work to follow the logic.",
            3: "Confusing. Jumps between ideas. Key points get lost.",
            1: "Incoherent or rambling. No discernible structure.",
        },
    },
    "depth": {
        "weight": 0.25,
        "description": "Technical accuracy, thoroughness, demonstrates real understanding",
        "levels": {
            9: "Expert-level depth. Explores trade-offs, edge cases, and nuances unprompted.",
            7: "Solid understanding. Covers the core well with some exploration of depth.",
            5: "Surface-level but correct. Knows the basics but doesn't go deeper.",
            3: "Shallow or partially incorrect. Missing important aspects.",
            1: "Fundamentally wrong or empty response.",
        },
    },
    "relevance": {
        "weight": 0.20,
        "description": "Directly addresses the question, stays on topic",
        "levels": {
            9: "Directly addresses every part of the question. Nothing superfluous.",
            7: "Addresses the question well. Minor tangents that don't detract.",
            5: "Partially addresses the question. Misses some aspects.",
            3: "Mostly off-topic. Vaguely related but doesn't answer the actual question.",
            1: "Completely off-topic or non-responsive.",
        },
    },
    "examples": {
        "weight": 0.20,
        "description": "Concrete examples, metrics, specific outcomes (not hypotheticals)",
        "levels": {
            9: "Vivid, specific examples with concrete metrics and measurable outcomes.",
            7: "Good examples with some specifics. Mostly concrete, not hypothetical.",
            5: "Generic examples. Says 'we improved performance' without numbers.",
            3: "Hypothetical or extremely vague. 'I would probably...'",
            1: "No examples at all. Pure theory or abstract statements.",
        },
    },
    "growth_signal": {
        "weight": 0.15,
        "description": "Self-awareness, learning demonstrated, intellectual curiosity",
        "levels": {
            9: "Shows deep self-awareness. Clearly articulates what they learned and how they grew.",
            7: "Mentions lessons learned. Shows some reflection on the experience.",
            5: "Acknowledges there were learnings but doesn't articulate them well.",
            3: "No reflection. Just describes what happened without any introspection.",
            1: "Defensive or unable to identify any learnings.",
        },
    },
}

# Company-specific rubric overrides
COMPANY_RUBRICS = {
    "amazon": {
        "name": "Amazon Leadership Principles",
        "extra_dimensions": {
            "ownership": {
                "weight": 0.15,
                "description": "Demonstrates ownership — thinks long-term, acts on behalf of the company",
            },
            "bias_for_action": {
                "weight": 0.10,
                "description": "Shows speed and decisiveness. Calculated risk-taking.",
            },
        },
        "notes": "Amazon heavily weights LP alignment. Every answer should map to 1-2 Leadership Principles.",
    },
    "google": {
        "name": "Google Interview Bar",
        "extra_dimensions": {
            "googleyness": {
                "weight": 0.10,
                "description": "Collaborative, humble, willing to share credit, comfortable with ambiguity",
            },
        },
        "notes": "Google values structured thinking and Googleyness. Show how you navigate ambiguity.",
    },
    "meta": {
        "name": "Meta Core Values",
        "extra_dimensions": {
            "move_fast": {
                "weight": 0.10,
                "description": "Demonstrates velocity, iteration speed, shipping quickly",
            },
            "impact": {
                "weight": 0.10,
                "description": "Focus on high-impact work, prioritization of what matters most",
            },
        },
        "notes": "Meta values impact and velocity. Show concrete metrics and fast iteration.",
    },
    "stripe": {
        "name": "Stripe Engineering Bar",
        "extra_dimensions": {
            "rigor": {
                "weight": 0.15,
                "description": "Intellectual rigor, attention to correctness, thoughtful edge case handling",
            },
        },
        "notes": "Stripe values intellectual rigor and craftsmanship. Precision matters.",
    },
}


# ── Evaluation Prompts ─────────────────────────────────────────────────

def build_evaluation_prompt(
    question: dict,
    answer: str,
    interview_type: str,
    company: str | None = None,
) -> str:
    """Build the evaluation prompt for the LLM."""

    rubric_text = "## Evaluation Rubric\n\n"
    active_rubric = dict(RUBRIC)

    # Add company-specific dimensions if applicable
    if company and company.lower() in COMPANY_RUBRICS:
        company_rubric = COMPANY_RUBRICS[company.lower()]
        rubric_text += f"**Company:** {company_rubric['name']}\n"
        rubric_text += f"**Note:** {company_rubric['notes']}\n\n"
        for dim, config in company_rubric.get("extra_dimensions", {}).items():
            active_rubric[dim] = config

    for dim, config in active_rubric.items():
        rubric_text += f"### {dim.replace('_', ' ').title()} (weight: {config['weight']:.0%})\n"
        rubric_text += f"{config['description']}\n"
        if "levels" in config:
            for score, desc in sorted(config["levels"].items(), reverse=True):
                rubric_text += f"  - **{score}/10**: {desc}\n"
        rubric_text += "\n"

    prompt = f"""You are an expert interview coach evaluating a candidate's answer.
Be honest, specific, and constructive. Don't sugarcoat — the candidate needs
real feedback to improve. But also acknowledge what they did well.

## Interview Context
- **Type:** {interview_type}
- **Company:** {company or 'General'}

## Question Asked
{question['q']}

{rubric_text}

## Candidate's Answer
{answer}

## Your Evaluation

Evaluate the answer across each rubric dimension. For each dimension:
1. Give a score (1-10)
2. Explain why in 1-2 sentences
3. Give one specific suggestion to improve

Then provide:
- An overall weighted score (1-10)
- A "model answer" outline — what a perfect response would cover
- The single most impactful thing the candidate should work on

Respond in this JSON format:
{{
  "dimensions": {{
    "clarity": {{"score": N, "feedback": "...", "suggestion": "..."}},
    "depth": {{"score": N, "feedback": "...", "suggestion": "..."}},
    "relevance": {{"score": N, "feedback": "...", "suggestion": "..."}},
    "examples": {{"score": N, "feedback": "...", "suggestion": "..."}},
    "growth_signal": {{"score": N, "feedback": "...", "suggestion": "..."}}
  }},
  "overall": N.N,
  "model_answer_outline": ["point 1", "point 2", "..."],
  "top_improvement": "The single most impactful thing to work on",
  "what_went_well": "What the candidate did best in this answer"
}}
"""
    return prompt


def format_evaluation(eval_result: dict, question: dict) -> str:
    """Format evaluation results for display in chat."""
    overall = eval_result.get("overall", 0)
    emoji = "🟢" if overall >= 7.5 else "🟡" if overall >= 5.0 else "🔴"

    text = f"\n### Evaluation {emoji} — {overall}/10\n\n"

    # Dimension scores
    for dim, data in eval_result.get("dimensions", {}).items():
        score = data.get("score", 0)
        bar = "█" * int(score) + "░" * (10 - int(score))
        dim_name = dim.replace("_", " ").title()
        text += f"**{dim_name}:** {score}/10 {bar}\n"
        text += f"  _{data.get('feedback', '')}_\n"
        if data.get("suggestion"):
            text += f"  💡 {data['suggestion']}\n"
        text += "\n"

    # What went well
    if eval_result.get("what_went_well"):
        text += f"✅ **What went well:** {eval_result['what_went_well']}\n\n"

    # Top improvement
    if eval_result.get("top_improvement"):
        text += f"🎯 **Focus on:** {eval_result['top_improvement']}\n\n"

    # Model answer outline
    if eval_result.get("model_answer_outline"):
        text += "📋 **A strong answer would cover:**\n"
        for point in eval_result["model_answer_outline"]:
            text += f"  - {point}\n"
        text += "\n"

    # Follow-up question
    if question.get("follow_up"):
        text += f"---\n\n**Follow-up:** {question['follow_up']}\n"

    return text


def compute_weighted_score(dimensions: dict) -> float:
    """Compute overall weighted score from dimension scores."""
    total_weight = 0
    weighted_sum = 0

    for dim, data in dimensions.items():
        weight = RUBRIC.get(dim, {}).get("weight", 0.1)
        score = data.get("score", 5)
        weighted_sum += weight * score
        total_weight += weight

    if total_weight == 0:
        return 5.0

    return round(weighted_sum / total_weight, 1)


# ── Behavioral-Specific Evaluation ────────────────────────────────────

STAR_CHECK_PROMPT = """Analyze this behavioral interview answer for STAR structure:

**Answer:** {answer}

Check each component:
- **Situation**: Did they set the scene? Context, timeline, stakes?
- **Task**: Was their specific role/responsibility clear?
- **Action**: Did they describe specific actions THEY took (not "we")?
- **Result**: Did they give concrete, quantifiable outcomes?

Return JSON:
{{
  "has_situation": true/false,
  "has_task": true/false,
  "has_action": true/false,
  "has_result": true/false,
  "uses_i_vs_we": "mostly I" | "mostly we" | "mixed",
  "has_metrics": true/false,
  "star_score": N (1-10),
  "suggestion": "..."
}}
"""

def build_star_check_prompt(answer: str) -> str:
    """Build a STAR structure check prompt for behavioral answers."""
    return STAR_CHECK_PROMPT.format(answer=answer)


# ── System Design-Specific Evaluation ──────────────────────────────────

def build_system_design_evaluation_prompt(
    question: dict,
    answer: str,
    company: str | None = None,
) -> str:
    """Build evaluation prompt specifically for system design questions."""
    key_areas = question.get("key_areas", [])

    return f"""You are a senior staff engineer evaluating a system design interview answer.

## Question
{question['q']}

## Key Areas Expected
{', '.join(key_areas)}

## Candidate's Answer
{answer}

Evaluate across these system design dimensions:

1. **Requirements Gathering (10%)** — Did they clarify requirements before diving in?
2. **High-Level Design (25%)** — Is the architecture sound? Right components?
3. **Deep Dive (25%)** — Did they go deep on the right areas?
4. **Trade-offs (20%)** — Did they discuss alternatives and why they chose this approach?
5. **Scalability (15%)** — Did they address scale, bottlenecks, and growth?
6. **Communication (5%)** — Was the explanation clear and structured?

Which key areas did they cover vs. miss?

Return JSON:
{{
  "dimensions": {{
    "requirements": {{"score": N, "feedback": "..."}},
    "high_level_design": {{"score": N, "feedback": "..."}},
    "deep_dive": {{"score": N, "feedback": "..."}},
    "trade_offs": {{"score": N, "feedback": "..."}},
    "scalability": {{"score": N, "feedback": "..."}},
    "communication": {{"score": N, "feedback": "..."}}
  }},
  "overall": N.N,
  "key_areas_covered": ["..."],
  "key_areas_missed": ["..."],
  "model_answer_outline": ["..."],
  "top_improvement": "..."
}}
"""

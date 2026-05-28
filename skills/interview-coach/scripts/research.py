"""
Company research module for Hermes Interview Coach.

Uses Hermes Agent's web search tool to gather company-specific
interview intelligence: common questions, interview process,
culture signals, and recent news.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Cache directory for company research
RESEARCH_CACHE = Path.home() / ".hermes" / "memory" / "interview_research"


# ── Research Prompts ───────────────────────────────────────────────────

def build_company_research_queries(company: str, role: str | None = None) -> list[dict]:
    """Build a set of web search queries for company research."""
    role_qualifier = f" {role}" if role else " software engineer"

    return [
        {
            "query": f"{company}{role_qualifier} interview questions 2025 2026",
            "purpose": "recent_questions",
            "description": f"Recent interview questions for {company}",
        },
        {
            "query": f"{company} interview process stages rounds what to expect",
            "purpose": "process",
            "description": f"Interview process and stages at {company}",
        },
        {
            "query": f"{company} engineering culture values what they look for",
            "purpose": "culture",
            "description": f"Engineering culture and values at {company}",
        },
        {
            "query": f"{company}{role_qualifier} salary compensation levels 2026",
            "purpose": "compensation",
            "description": f"Compensation data for {role_qualifier} at {company}",
        },
        {
            "query": f"site:glassdoor.com OR site:teamblind.com {company}{role_qualifier} interview experience",
            "purpose": "experiences",
            "description": f"Interview experiences shared on Glassdoor/Blind",
        },
    ]


def build_research_synthesis_prompt(
    company: str,
    role: str | None,
    search_results: list[dict],
) -> str:
    """Build a prompt to synthesize research results into actionable intel."""
    results_text = ""
    for result in search_results:
        results_text += f"\n### {result['description']}\n{result.get('content', 'No results')}\n"

    return f"""Synthesize this research about interviewing at {company} for a {role or 'software engineering'} position.

{results_text}

Create a structured interview preparation brief with:

1. **Interview Process** — number of rounds, types, timeline
2. **Common Questions** — frequently asked questions with tips
3. **Culture & Values** — what they evaluate beyond technical skills
4. **Red Flags to Avoid** — common reasons candidates get rejected
5. **Pro Tips** — insider advice from real interview experiences
6. **Compensation Range** — if available

Be specific and actionable. Cite sources where possible.

Return as JSON:
{{
  "company": "{company}",
  "role": "{role or 'Software Engineer'}",
  "researched_at": "{datetime.now().isoformat()}",
  "process": {{
    "total_rounds": N,
    "stages": ["phone screen", "technical", "..."],
    "timeline_days": N,
    "notes": "..."
  }},
  "common_questions": [
    {{"question": "...", "category": "behavioral|technical|system-design", "tips": "..."}},
  ],
  "culture_values": ["..."],
  "red_flags": ["..."],
  "pro_tips": ["..."],
  "compensation": {{
    "range_low": N,
    "range_high": N,
    "currency": "USD",
    "notes": "..."
  }}
}}
"""


# ── Research Cache Management ──────────────────────────────────────────

def get_cached_research(company: str) -> Optional[dict]:
    """Load cached research for a company if recent enough."""
    cache_file = RESEARCH_CACHE / f"{company.lower().replace(' ', '_')}.json"
    if not cache_file.exists():
        return None

    try:
        with open(cache_file) as f:
            data = json.load(f)

        # Check if cache is less than 7 days old
        researched_at = datetime.fromisoformat(data.get("researched_at", "2000-01-01"))
        if (datetime.now() - researched_at).days <= 7:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    return None


def save_research_cache(company: str, data: dict):
    """Cache research results for future sessions."""
    RESEARCH_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = RESEARCH_CACHE / f"{company.lower().replace(' ', '_')}.json"
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


def format_research_brief(research: dict) -> str:
    """Format research data into a readable brief for the user."""
    company = research.get("company", "Unknown")
    role = research.get("role", "Software Engineer")

    text = f"""## 🔍 Interview Intel — {company} ({role})

### Interview Process
"""
    process = research.get("process", {})
    if process:
        text += f"- **Rounds:** {process.get('total_rounds', 'Unknown')}\n"
        stages = process.get("stages", [])
        if stages:
            text += f"- **Stages:** {' → '.join(stages)}\n"
        text += f"- **Timeline:** ~{process.get('timeline_days', 'Unknown')} days\n"
        if process.get("notes"):
            text += f"- **Notes:** {process['notes']}\n"

    # Common questions
    questions = research.get("common_questions", [])
    if questions:
        text += "\n### Common Questions\n\n"
        for i, q in enumerate(questions[:10], 1):
            cat_emoji = {"behavioral": "🗣️", "technical": "⚙️", "system-design": "🏗️"}.get(
                q.get("category", ""), "❓"
            )
            text += f"{i}. {cat_emoji} **{q['question']}**\n"
            if q.get("tips"):
                text += f"   💡 {q['tips']}\n"

    # Culture
    values = research.get("culture_values", [])
    if values:
        text += "\n### Culture & Values\n"
        for v in values:
            text += f"- {v}\n"

    # Red flags
    red_flags = research.get("red_flags", [])
    if red_flags:
        text += "\n### ⚠️ Red Flags to Avoid\n"
        for rf in red_flags:
            text += f"- ❌ {rf}\n"

    # Pro tips
    pro_tips = research.get("pro_tips", [])
    if pro_tips:
        text += "\n### 💡 Pro Tips\n"
        for tip in pro_tips:
            text += f"- {tip}\n"

    # Compensation
    comp = research.get("compensation", {})
    if comp and comp.get("range_low"):
        currency = comp.get("currency", "USD")
        text += f"\n### 💰 Compensation Range\n"
        text += f"**{currency} {comp['range_low']:,} — {comp['range_high']:,}** per year\n"
        if comp.get("notes"):
            text += f"_{comp['notes']}_\n"

    text += f"\n---\n_Researched: {research.get('researched_at', 'Unknown')[:10]}_\n"
    return text


# ── Known Company Patterns ─────────────────────────────────────────────

# Offline fallback data for major companies
COMPANY_PATTERNS = {
    "google": {
        "process": {
            "total_rounds": 5,
            "stages": ["Recruiter Screen", "Phone Technical", "Onsite (4-5 rounds)", "Team Match", "Hiring Committee"],
            "timeline_days": 30,
            "notes": "HC is the final decision-maker, not the interviewers. Packet goes through multiple reviews.",
        },
        "culture_values": [
            "Googleyness — collaborative, intellectually humble, comfortable with ambiguity",
            "General cognitive ability — structured thinking, learning ability over rote knowledge",
            "Role-related knowledge — demonstrates expertise but open to new approaches",
            "Leadership — emerges at any level, not just managers",
        ],
        "red_flags": [
            "Jumping to solutions without clarifying requirements",
            "Not considering edge cases or trade-offs",
            "Claiming sole credit for team accomplishments",
            "Being rigid about a single approach",
            "Not asking good questions during the interview",
        ],
        "pro_tips": [
            "Think out loud — the process matters as much as the answer",
            "Always start system design with requirements clarification and back-of-envelope math",
            "Google loves 'what else?' — after answering, proactively explore extensions",
            "Practice on a whiteboard/doc, not just in your head",
            "The team match phase matters — show genuine interest in the team's work",
        ],
    },
    "amazon": {
        "process": {
            "total_rounds": 5,
            "stages": ["OA/Phone Screen", "Virtual Onsite (4-5 rounds)", "Bar Raiser Round", "Debrief"],
            "timeline_days": 14,
            "notes": "Every round maps to specific Leadership Principles. The Bar Raiser has veto power.",
        },
        "culture_values": [
            "Leadership Principles are not suggestions — they're the rubric",
            "Customer Obsession — every decision should trace back to customer impact",
            "Ownership — think long-term, don't sacrifice long-term for short-term",
            "Dive Deep — leaders operate at all levels, stay connected to details",
            "Bias for Action — speed matters, most decisions are reversible",
        ],
        "red_flags": [
            "Not using STAR format for behavioral questions",
            "Saying 'we' instead of 'I' — Amazon wants to know YOUR contribution",
            "Not tying answers back to Leadership Principles",
            "Vague metrics — 'we improved performance' instead of 'reduced latency from 200ms to 50ms'",
        ],
    },
    "meta": {
        "process": {
            "total_rounds": 4,
            "stages": ["Recruiter Screen", "Technical Phone Screen", "Onsite (3-4 rounds)", "Hiring Committee"],
            "timeline_days": 21,
            "notes": "Coding rounds use CoderPad. System design uses a shared doc. Behavioral is 'values interview'.",
        },
        "culture_values": [
            "Move Fast — ship quickly, iterate, don't wait for perfection",
            "Be Bold — take risks, the biggest risk is not taking any risk",
            "Focus on Impact — prioritize high-impact work ruthlessly",
            "Be Open — share information freely, give and receive feedback directly",
            "Build Social Value — consider the broader impact of your work",
        ],
    },
    "stripe": {
        "process": {
            "total_rounds": 5,
            "stages": ["Recruiter Call", "Technical Screen", "Craft Exercise (take-home)", "Onsite (3-4 rounds)", "Offer"],
            "timeline_days": 21,
            "notes": "The craft exercise is unique to Stripe — it's a real-world coding exercise done at home, followed by a live extension.",
        },
        "culture_values": [
            "Users first — deep empathy for developer experience",
            "Move with urgency — ship fast, but never ship bugs to production",
            "Rigor — intellectual honesty, attention to correctness, clear thinking",
            "Craft — code quality matters, good abstractions matter",
        ],
    },
}


def get_company_pattern(company: str) -> Optional[dict]:
    """Get known interview patterns for a major company."""
    return COMPANY_PATTERNS.get(company.lower())

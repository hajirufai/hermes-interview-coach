"""
Hermes Agent tool registration for the Interview Coach skill.

This module registers the interview coach as a callable tool within
Hermes Agent's tool system, making it available via slash commands
and natural language triggers.
"""

import json
import sys
from pathlib import Path

# Add skill scripts to path
SKILL_DIR = Path(__file__).parent.parent / "skills" / "interview-coach" / "scripts"
sys.path.insert(0, str(SKILL_DIR))

from interview import InterviewSession, format_session_summary, load_profile, save_profile
from evaluate import build_evaluation_prompt, format_evaluation, compute_weighted_score
from research import (
    build_company_research_queries,
    build_research_synthesis_prompt,
    format_research_brief,
    get_cached_research,
    get_company_pattern,
    save_research_cache,
)
from progress import generate_report, assess_readiness
from scheduler import (
    generate_daily_challenge,
    format_daily_challenge,
    generate_cron_config,
    generate_weekly_digest,
)


# ── Tool Definitions ───────────────────────────────────────────────────

TOOLS = [
    {
        "name": "interview_start",
        "description": "Start a mock interview session. Supports behavioral, technical, system-design, coding, and mixed types. Optionally target a specific company and role.",
        "parameters": {
            "type": {
                "type": "string",
                "enum": ["behavioral", "technical", "system-design", "coding", "mixed"],
                "default": "mixed",
                "description": "Type of interview to simulate",
            },
            "company": {
                "type": "string",
                "description": "Target company (e.g., Google, Amazon, Stripe)",
                "optional": True,
            },
            "role": {
                "type": "string",
                "description": "Target role (e.g., Senior Backend Engineer)",
                "optional": True,
            },
            "questions": {
                "type": "integer",
                "default": 5,
                "description": "Number of questions (1-10)",
            },
        },
        "triggers": [
            "interview", "mock interview", "practice interview",
            "interview prep", "behavioral practice", "system design practice",
        ],
    },
    {
        "name": "interview_evaluate",
        "description": "Evaluate an interview answer against the scoring rubric. Used internally during sessions.",
        "parameters": {
            "question": {"type": "object", "description": "The question that was asked"},
            "answer": {"type": "string", "description": "The candidate's answer"},
            "interview_type": {"type": "string", "description": "Type of interview"},
            "company": {"type": "string", "optional": True},
        },
    },
    {
        "name": "interview_research",
        "description": "Research a company's interview process, common questions, and culture. Uses web search for fresh data.",
        "parameters": {
            "company": {"type": "string", "description": "Company to research"},
            "role": {"type": "string", "optional": True, "description": "Target role"},
        },
        "triggers": [
            "research company", "interview process at", "what to expect at",
        ],
    },
    {
        "name": "interview_report",
        "description": "Generate a progress report showing score trends, category breakdown, and recommendations.",
        "parameters": {
            "period": {
                "type": "string",
                "enum": ["week", "month", "all"],
                "default": "week",
            },
            "format": {
                "type": "string",
                "enum": ["summary", "detailed"],
                "default": "summary",
            },
        },
        "triggers": [
            "interview report", "interview progress", "how am I doing",
            "interview stats", "practice report",
        ],
    },
    {
        "name": "interview_schedule",
        "description": "Set up daily practice questions via cron. Delivers one question each morning to any connected platform.",
        "parameters": {
            "time": {
                "type": "string",
                "default": "08:30",
                "description": "Time to send daily challenge (HH:MM)",
            },
            "platform": {
                "type": "string",
                "default": "telegram",
                "description": "Platform for delivery",
            },
        },
        "triggers": [
            "schedule practice", "daily practice", "interview schedule",
            "daily questions", "set up reminders",
        ],
    },
    {
        "name": "interview_ready",
        "description": "Assess interview readiness for a target company based on practice history.",
        "parameters": {
            "company": {"type": "string", "optional": True},
        },
        "triggers": [
            "am I ready", "interview readiness", "ready for interview",
        ],
    },
]


# ── Tool Handlers ──────────────────────────────────────────────────────

class InterviewCoachTool:
    """Main tool handler that Hermes Agent calls."""

    def __init__(self):
        self.active_session = None

    async def handle(self, tool_name: str, params: dict, context: dict) -> str:
        """Route tool calls to the appropriate handler."""
        handlers = {
            "interview_start": self._handle_start,
            "interview_evaluate": self._handle_evaluate,
            "interview_research": self._handle_research,
            "interview_report": self._handle_report,
            "interview_schedule": self._handle_schedule,
            "interview_ready": self._handle_ready,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Unknown tool: {tool_name}"

        return await handler(params, context)

    async def _handle_start(self, params: dict, context: dict) -> str:
        """Start a new interview session."""
        interview_type = params.get("type", "mixed")
        company = params.get("company")
        role = params.get("role")
        question_count = min(params.get("questions", 5), 10)

        # Update profile with target company/role if specified
        profile = load_profile()
        if company and company not in profile.get("target_companies", []):
            profile.setdefault("target_companies", []).append(company)
        if role:
            profile["target_role"] = role
        save_profile(profile)

        # Create session
        self.active_session = InterviewSession(
            interview_type=interview_type,
            company=company,
            role=role,
            question_count=question_count,
        )

        # Build intro + first question
        intro = self.active_session.get_intro()
        first_q = self.active_session.get_current_question()

        if first_q:
            intro += "\n" + self.active_session.format_question(first_q)

        return intro

    async def _handle_evaluate(self, params: dict, context: dict) -> str:
        """Evaluate an answer (called during active session)."""
        question = params.get("question", {})
        answer = params.get("answer", "")
        interview_type = params.get("interview_type", "mixed")
        company = params.get("company")

        # Build evaluation prompt for the LLM
        prompt = build_evaluation_prompt(question, answer, interview_type, company)

        # In a real Hermes session, this would call the active model
        # Here we return the prompt for the agent to process
        return prompt

    async def _handle_research(self, params: dict, context: dict) -> str:
        """Research a company's interview process."""
        company = params.get("company", "")
        role = params.get("role")

        # Check cache first
        cached = get_cached_research(company)
        if cached:
            return format_research_brief(cached)

        # Check known patterns
        known = get_company_pattern(company)
        if known:
            known["company"] = company
            known["role"] = role or "Software Engineer"
            known["researched_at"] = "built-in"
            return format_research_brief(known)

        # Build research queries for web search
        queries = build_company_research_queries(company, role)
        return json.dumps({
            "action": "web_search_batch",
            "queries": queries,
            "synthesis_prompt": build_research_synthesis_prompt(company, role, []),
        }, indent=2)

    async def _handle_report(self, params: dict, context: dict) -> str:
        """Generate progress report."""
        period = params.get("period", "week")
        fmt = params.get("format", "summary")
        return generate_report(period, fmt)

    async def _handle_schedule(self, params: dict, context: dict) -> str:
        """Set up daily practice cron."""
        time = params.get("time", "08:30")
        platform = params.get("platform", "telegram")

        config = generate_cron_config(time, platform)
        challenge = generate_daily_challenge()
        sample = format_daily_challenge(challenge)

        return f"""## Daily Practice Scheduled ✅

**Time:** {time} (weekdays)
**Platform:** {platform}

### Cron Configuration
```json
{json.dumps(config, indent=2)}
```

### Sample Daily Challenge
{sample}

To modify: `/interview schedule --time 07:00 --platform discord`
To stop: `/interview schedule --disable`
"""

    async def _handle_ready(self, params: dict, context: dict) -> str:
        """Assess interview readiness."""
        company = params.get("company")
        return assess_readiness(company)


# ── Registration ───────────────────────────────────────────────────────

def register(agent):
    """Register the Interview Coach with Hermes Agent's tool system."""
    tool = InterviewCoachTool()

    for tool_def in TOOLS:
        agent.register_tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def.get("parameters", {}),
            handler=lambda params, ctx, t=tool, tn=tool_def["name"]: t.handle(tn, params, ctx),
            triggers=tool_def.get("triggers", []),
        )

    return tool

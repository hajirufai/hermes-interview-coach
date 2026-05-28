"""
Cron-based daily practice scheduler for Hermes Interview Coach.

Integrates with Hermes Agent's built-in cron system to deliver
daily practice questions via any connected platform (Telegram,
Discord, Slack, WhatsApp, CLI).
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from interview import (
    BEHAVIORAL_QUESTIONS,
    SYSTEM_DESIGN_QUESTIONS,
    TECHNICAL_QUESTIONS,
    load_profile,
)


# ── Daily Challenge Generation ─────────────────────────────────────────

def generate_daily_challenge(profile: dict | None = None) -> dict:
    """
    Generate a single practice question for the daily challenge.
    
    Rotates through categories, weighted toward weak areas.
    Tracks which questions have been sent to avoid repeats.
    """
    if profile is None:
        profile = load_profile()

    weak_areas = profile.get("weak_areas", [])
    sent_questions = _load_sent_questions()

    # Determine today's category
    categories = ["behavioral", "technical", "system-design"]
    day_of_year = datetime.now().timetuple().tm_yday

    # Weight toward weak areas
    if weak_areas:
        # 60% chance of weak area, 40% rotation
        if random.random() < 0.6:
            matching_cats = [c for c in categories if c in weak_areas or
                           any(w in c for w in weak_areas)]
            if matching_cats:
                category = random.choice(matching_cats)
            else:
                category = categories[day_of_year % len(categories)]
        else:
            category = categories[day_of_year % len(categories)]
    else:
        category = categories[day_of_year % len(categories)]

    # Select a question from that category
    question = _select_unseen_question(category, sent_questions)

    if question is None:
        # All questions seen — reset and start over
        sent_questions = []
        question = _select_unseen_question(category, sent_questions)

    if question is None:
        return {
            "category": "behavioral",
            "question": "Tell me about a challenging project you recently worked on.",
            "tips": "Use STAR format. Be specific about your contribution.",
            "difficulty": "medium",
        }

    # Track this question as sent
    _save_sent_question(question["q"])

    return {
        "category": category,
        "question": question["q"],
        "follow_up": question.get("follow_up", ""),
        "difficulty": question.get("difficulty", "medium"),
        "tags": question.get("tags", []),
        "tips": _generate_tips(category, question),
    }


def format_daily_challenge(challenge: dict) -> str:
    """Format a daily challenge for messaging delivery."""
    category = challenge["category"].replace("-", " ").title()
    difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(
        challenge.get("difficulty", "medium"), "🟡"
    )

    text = f"""☀️ **Daily Interview Practice** — {category} {difficulty_emoji}

**{challenge['question']}**
"""
    if challenge.get("tips"):
        text += f"\n💡 *Tip: {challenge['tips']}*\n"

    text += """
Reply with your answer and I'll evaluate it with detailed feedback.

*Consistency beats intensity — even 10 minutes of daily practice builds interview muscle.*
"""
    return text


# ── Cron Configuration ─────────────────────────────────────────────────

CRON_CONFIG_TEMPLATE = {
    "name": "interview-daily-practice",
    "schedule": "30 8 * * 1-5",  # 8:30 AM weekdays
    "description": "Daily interview practice question",
    "platform": "telegram",  # Default, configurable
    "enabled": True,
}


def generate_cron_config(
    time: str = "08:30",
    platform: str = "telegram",
    weekdays_only: bool = True,
) -> dict:
    """Generate Hermes cron configuration for daily practice."""
    hour, minute = time.split(":")
    days = "1-5" if weekdays_only else "*"

    config = CRON_CONFIG_TEMPLATE.copy()
    config["schedule"] = f"{minute} {hour} * * {days}"
    config["platform"] = platform

    return config


def generate_cron_skill_text(config: dict) -> str:
    """Generate the natural language cron instruction for Hermes."""
    schedule_desc = config["schedule"]
    platform = config["platform"]

    return f"""Every weekday at the scheduled time, run the interview-coach daily practice:

1. Load the user's interview profile
2. Generate a practice question weighted toward weak areas
3. Format it as a daily challenge message
4. Send it via {platform}

When the user replies with their answer:
1. Evaluate it using the interview-coach evaluation rubric
2. Provide detailed scored feedback
3. Update the user's profile with the results

Cron schedule: {schedule_desc}
"""


# ── Weekly Digest ──────────────────────────────────────────────────────

def generate_weekly_digest(profile: dict | None = None) -> str:
    """Generate a weekly practice summary for Sunday delivery."""
    if profile is None:
        profile = load_profile()

    history = profile.get("score_history", [])
    if not history:
        return "📊 **Weekly Digest**: No sessions this week. Start practicing with `/interview start`!"

    # Get this week's sessions
    now = datetime.now()
    week_start = now.replace(hour=0, minute=0, second=0) 
    # Simple: last 7 entries
    week_sessions = history[-7:]

    if not week_sessions:
        return "📊 **Weekly Digest**: No sessions this week. Time to get back on track!"

    scores = [s["score"] for s in week_sessions]
    avg = sum(scores) / len(scores)
    best = max(scores)

    emoji = "🔥" if avg >= 8.0 else "💪" if avg >= 6.5 else "📈" if avg >= 5.0 else "💪"

    text = f"""📊 **Weekly Interview Practice Digest** {emoji}

**Sessions this week:** {len(week_sessions)}
**Average score:** {avg:.1f}/10
**Best score:** {best:.1f}/10

"""
    # Quick breakdown
    for s in week_sessions:
        score_emoji = "🟢" if s["score"] >= 7.5 else "🟡" if s["score"] >= 5.0 else "🔴"
        text += f"  {score_emoji} {s['date']} — {s['type']} — {s['score']}/10\n"

    # Encouragement based on performance
    if avg >= 8.0:
        text += "\n🏆 *Outstanding week! You're interview-ready. Consider doing a full mock.*"
    elif avg >= 6.5:
        text += "\n💪 *Good progress! Keep the momentum going next week.*"
    elif avg >= 5.0:
        text += "\n📈 *Building up! Focus on your weak areas for bigger gains.*"
    else:
        text += "\n🌱 *Every session makes you better. Consistency is what wins interviews.*"

    # Next week's focus
    weak = profile.get("weak_areas", [])
    if weak:
        text += f"\n\n🎯 **Next week's focus:** {', '.join(w.replace('-', ' ').title() for w in weak[:2])}"

    return text


# ── Helper Functions ───────────────────────────────────────────────────

SENT_QUESTIONS_PATH = Path.home() / ".hermes" / "memory" / "interview_sent_questions.json"


def _load_sent_questions() -> list[str]:
    """Load the list of previously sent questions."""
    if SENT_QUESTIONS_PATH.exists():
        try:
            with open(SENT_QUESTIONS_PATH) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def _save_sent_question(question: str):
    """Add a question to the sent list."""
    sent = _load_sent_questions()
    sent.append(question)
    SENT_QUESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_QUESTIONS_PATH, "w") as f:
        json.dump(sent, f)


def _select_unseen_question(category: str, sent: list[str]) -> Optional[dict]:
    """Select a question that hasn't been sent yet."""
    candidates = []

    if category == "behavioral":
        for questions in BEHAVIORAL_QUESTIONS.values():
            candidates.extend(questions)
    elif category == "system-design":
        candidates.extend(SYSTEM_DESIGN_QUESTIONS)
    elif category == "technical":
        for questions in TECHNICAL_QUESTIONS.values():
            candidates.extend(questions)

    unseen = [q for q in candidates if q["q"] not in sent]
    if not unseen:
        return None

    return random.choice(unseen)


def _generate_tips(category: str, question: dict) -> str:
    """Generate contextual tips for a question."""
    tips = {
        "behavioral": [
            "Use STAR format: Situation, Task, Action, Result",
            "Be specific — use numbers, timelines, and concrete outcomes",
            "Say 'I' not 'we' — interviewers want YOUR contribution",
            "Keep your answer under 3 minutes",
            "End with what you learned or would do differently",
        ],
        "system-design": [
            "Start with requirements clarification — don't jump to solutions",
            "Do back-of-envelope math before designing",
            "Discuss trade-offs for every major decision",
            "Start high-level, then deep-dive into one area",
            "Consider both reads and writes, peak vs average load",
        ],
        "technical": [
            "Think out loud — show your reasoning process",
            "Consider edge cases before giving your final answer",
            "If you don't know, say so — then reason through it",
            "Give concrete examples, not just theory",
            "Connect concepts to real-world applications you've seen",
        ],
    }

    category_tips = tips.get(category, tips["behavioral"])
    return random.choice(category_tips)

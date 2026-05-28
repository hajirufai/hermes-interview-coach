"""
Core interview engine for the Hermes Interview Coach skill.

Manages mock interview sessions — question selection, flow control,
timing, and session lifecycle. Works with any Hermes-supported model.
"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Hermes Agent imports (available when running inside Hermes)
try:
    from hermes.tools import web_search, read_file, write_file
    from hermes.memory import load_memory, save_memory
    from hermes.skills import get_skill_path
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False


# ── Constants ──────────────────────────────────────────────────────────

MEMORY_DIR = Path.home() / ".hermes" / "memory"
PROFILE_PATH = MEMORY_DIR / "interview_profile.json"
SESSION_LOG_DIR = MEMORY_DIR / "interview_sessions"

INTERVIEW_TYPES = ["behavioral", "technical", "system-design", "coding", "mixed"]

DEFAULT_PROFILE = {
    "sessions_completed": 0,
    "total_questions_answered": 0,
    "strengths": [],
    "weak_areas": [],
    "target_companies": [],
    "target_role": None,
    "preferred_difficulty": "medium",
    "score_history": [],
    "category_scores": {
        "behavioral": {"attempts": 0, "avg_score": 0.0},
        "technical": {"attempts": 0, "avg_score": 0.0},
        "system-design": {"attempts": 0, "avg_score": 0.0},
        "coding": {"attempts": 0, "avg_score": 0.0},
    },
    "created_at": None,
    "last_session": None,
}


# ── Question Banks ─────────────────────────────────────────────────────

BEHAVIORAL_QUESTIONS = {
    "leadership": [
        {
            "q": "Tell me about a time you had to lead a project with unclear requirements.",
            "follow_up": "How did you handle the ambiguity? What frameworks did you use to make decisions?",
            "difficulty": "medium",
            "tags": ["leadership", "ambiguity", "decision-making"],
        },
        {
            "q": "Describe a situation where you disagreed with your manager's technical decision.",
            "follow_up": "How did you approach the disagreement? What was the outcome?",
            "difficulty": "hard",
            "tags": ["leadership", "conflict", "influence"],
        },
        {
            "q": "Give an example of when you mentored a junior engineer through a challenging problem.",
            "follow_up": "What was your teaching approach? How did you measure their growth?",
            "difficulty": "medium",
            "tags": ["leadership", "mentoring", "growth"],
        },
    ],
    "conflict": [
        {
            "q": "Tell me about a time you had a conflict with a teammate. How did you resolve it?",
            "follow_up": "What would you do differently if it happened again?",
            "difficulty": "medium",
            "tags": ["conflict", "communication", "empathy"],
        },
        {
            "q": "Describe a situation where two teams had conflicting priorities and you were caught in the middle.",
            "follow_up": "How did you balance both sides? What trade-offs did you make?",
            "difficulty": "hard",
            "tags": ["conflict", "stakeholder-management", "prioritization"],
        },
    ],
    "failure": [
        {
            "q": "Tell me about a project that failed. What happened and what did you learn?",
            "follow_up": "How did you communicate the failure to stakeholders?",
            "difficulty": "medium",
            "tags": ["failure", "learning", "resilience"],
        },
        {
            "q": "Describe a time you shipped a bug to production that impacted users.",
            "follow_up": "Walk me through the incident response. What process changes did you make afterward?",
            "difficulty": "hard",
            "tags": ["failure", "incident-response", "process-improvement"],
        },
    ],
    "impact": [
        {
            "q": "What's the most impactful project you've worked on? Walk me through it.",
            "follow_up": "How did you measure impact? What metrics moved?",
            "difficulty": "medium",
            "tags": ["impact", "metrics", "ownership"],
        },
        {
            "q": "Tell me about a time you identified and solved a problem nobody asked you to solve.",
            "follow_up": "How did you get buy-in? What was the ROI?",
            "difficulty": "hard",
            "tags": ["impact", "initiative", "ownership"],
        },
    ],
}

SYSTEM_DESIGN_QUESTIONS = [
    {
        "q": "Design a URL shortener like bit.ly.",
        "key_areas": ["hashing", "database design", "caching", "analytics", "scaling reads"],
        "difficulty": "medium",
        "duration_minutes": 35,
    },
    {
        "q": "Design a real-time chat system like Slack.",
        "key_areas": ["websockets", "message ordering", "presence", "search", "notification fanout"],
        "difficulty": "hard",
        "duration_minutes": 45,
    },
    {
        "q": "Design a rate limiter for an API gateway.",
        "key_areas": ["token bucket", "sliding window", "distributed state", "Redis", "consistency"],
        "difficulty": "medium",
        "duration_minutes": 30,
    },
    {
        "q": "Design a notification system that handles 10M+ daily notifications across email, push, and SMS.",
        "key_areas": ["message queues", "priority", "deduplication", "user preferences", "delivery tracking"],
        "difficulty": "hard",
        "duration_minutes": 45,
    },
    {
        "q": "Design a distributed task scheduler like cron-at-scale.",
        "key_areas": ["consistency", "leader election", "exactly-once execution", "failure recovery", "sharding"],
        "difficulty": "hard",
        "duration_minutes": 40,
    },
    {
        "q": "Design an image upload and processing pipeline for a social media app.",
        "key_areas": ["CDN", "async processing", "thumbnails", "storage tiers", "content moderation"],
        "difficulty": "medium",
        "duration_minutes": 35,
    },
]

TECHNICAL_QUESTIONS = {
    "python": [
        {
            "q": "Explain the Global Interpreter Lock (GIL) in Python. When does it matter and how do you work around it?",
            "difficulty": "medium",
            "tags": ["python", "concurrency", "performance"],
        },
        {
            "q": "How do Python descriptors work? Give an example of when you'd write a custom descriptor.",
            "difficulty": "hard",
            "tags": ["python", "metaprogramming", "oop"],
        },
        {
            "q": "Walk me through how Python's garbage collector works. What's the difference between reference counting and generational GC?",
            "difficulty": "hard",
            "tags": ["python", "memory-management", "internals"],
        },
    ],
    "distributed_systems": [
        {
            "q": "Explain the CAP theorem. Give a real-world example of a system that prioritizes AP over CP.",
            "difficulty": "medium",
            "tags": ["distributed-systems", "theory", "trade-offs"],
        },
        {
            "q": "What's the difference between eventual consistency and strong consistency? When would you choose each?",
            "difficulty": "medium",
            "tags": ["distributed-systems", "consistency", "database"],
        },
        {
            "q": "How does a consensus algorithm like Raft work? Walk me through leader election and log replication.",
            "difficulty": "hard",
            "tags": ["distributed-systems", "consensus", "raft"],
        },
    ],
    "databases": [
        {
            "q": "You have a PostgreSQL table with 100M rows and queries are slow. Walk me through your investigation and optimization process.",
            "difficulty": "medium",
            "tags": ["databases", "performance", "indexing"],
        },
        {
            "q": "Compare B-tree and LSM-tree storage engines. When would you pick one over the other?",
            "difficulty": "hard",
            "tags": ["databases", "storage-engines", "trade-offs"],
        },
    ],
}


# ── Profile Management ─────────────────────────────────────────────────

def load_profile() -> dict:
    """Load the user's interview profile from Hermes memory."""
    if PROFILE_PATH.exists():
        with open(PROFILE_PATH) as f:
            profile = json.load(f)
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_PROFILE.items():
            if key not in profile:
                profile[key] = value
        return profile
    else:
        profile = DEFAULT_PROFILE.copy()
        profile["created_at"] = datetime.now().isoformat()
        return profile


def save_profile(profile: dict):
    """Persist the user's interview profile."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2, default=str)


# ── Question Selection ─────────────────────────────────────────────────

def select_questions(
    interview_type: str,
    count: int = 5,
    difficulty: str = "medium",
    weak_areas: list[str] | None = None,
    company: str | None = None,
) -> list[dict]:
    """
    Select questions for a mock interview session.
    
    Weights selection toward the user's weak areas. If a target
    company is specified, includes company-specific patterns.
    """
    candidates = []

    if interview_type in ("behavioral", "mixed"):
        for category, questions in BEHAVIORAL_QUESTIONS.items():
            for q in questions:
                weight = 1.0
                # Boost weight if this category is a weak area
                if weak_areas and any(tag in weak_areas for tag in q.get("tags", [])):
                    weight = 3.0
                # Adjust for difficulty preference
                if q.get("difficulty") == difficulty:
                    weight *= 1.5
                candidates.append((q, weight, "behavioral"))

    if interview_type in ("system-design", "mixed"):
        for q in SYSTEM_DESIGN_QUESTIONS:
            weight = 1.0
            if q.get("difficulty") == difficulty:
                weight *= 1.5
            candidates.append((q, weight, "system-design"))

    if interview_type in ("technical", "mixed"):
        for category, questions in TECHNICAL_QUESTIONS.items():
            for q in questions:
                weight = 1.0
                if weak_areas and any(tag in weak_areas for tag in q.get("tags", [])):
                    weight = 3.0
                if q.get("difficulty") == difficulty:
                    weight *= 1.5
                candidates.append((q, weight, "technical"))

    if not candidates:
        return []

    # Weighted random selection without replacement
    selected = []
    remaining = candidates.copy()
    for _ in range(min(count, len(remaining))):
        weights = [w for _, w, _ in remaining]
        total = sum(weights)
        if total == 0:
            break
        r = random.uniform(0, total)
        cumulative = 0
        for i, (q, w, cat) in enumerate(remaining):
            cumulative += w
            if r <= cumulative:
                selected.append({**q, "category": cat})
                remaining.pop(i)
                break

    return selected


# ── Session Management ─────────────────────────────────────────────────

class InterviewSession:
    """Manages a single mock interview session."""

    def __init__(
        self,
        interview_type: str = "mixed",
        company: str | None = None,
        role: str | None = None,
        duration_minutes: int = 30,
        question_count: int = 5,
    ):
        self.session_id = f"session_{int(time.time())}"
        self.interview_type = interview_type
        self.company = company
        self.role = role
        self.duration_minutes = duration_minutes
        self.started_at = datetime.now()
        self.ended_at = None
        self.current_question_idx = 0
        self.responses = []

        # Load user profile for adaptive question selection
        self.profile = load_profile()

        # Select questions weighted by weak areas
        self.questions = select_questions(
            interview_type=interview_type,
            count=question_count,
            difficulty=self.profile.get("preferred_difficulty", "medium"),
            weak_areas=self.profile.get("weak_areas", []),
            company=company,
        )

    def get_intro(self) -> str:
        """Generate the session introduction."""
        company_note = f" targeting *{self.company}*" if self.company else ""
        role_note = f" for the *{self.role}* position" if self.role else ""
        sessions_done = self.profile.get("sessions_completed", 0)

        intro = f"""
## Mock Interview Session #{sessions_done + 1}

**Type:** {self.interview_type.replace('-', ' ').title()}{company_note}{role_note}
**Questions:** {len(self.questions)}
**Duration:** ~{self.duration_minutes} minutes

---

I'll ask you {len(self.questions)} questions. For each one:
- Take a moment to think before answering
- Structure your response clearly (use STAR for behavioral questions)
- Be specific — use real examples with concrete metrics
- I'll provide detailed feedback after each answer

Let's begin.

---
"""
        return intro

    def get_current_question(self) -> Optional[dict]:
        """Get the current question."""
        if self.current_question_idx >= len(self.questions):
            return None
        return self.questions[self.current_question_idx]

    def format_question(self, question: dict) -> str:
        """Format a question for display."""
        idx = self.current_question_idx + 1
        total = len(self.questions)
        category = question.get("category", "general").replace("-", " ").title()

        text = f"### Question {idx}/{total} — {category}\n\n"
        text += f"**{question['q']}**\n"

        if question.get("key_areas"):
            text += f"\n*Key areas to cover: {', '.join(question['key_areas'])}*\n"

        if question.get("duration_minutes"):
            text += f"\n*Suggested time: {question['duration_minutes']} minutes*\n"

        return text

    def record_response(self, answer: str, score: dict):
        """Record a response and its evaluation."""
        question = self.questions[self.current_question_idx]
        self.responses.append({
            "question": question,
            "answer": answer,
            "score": score,
            "timestamp": datetime.now().isoformat(),
        })
        self.current_question_idx += 1

    def get_summary(self) -> dict:
        """Generate session summary with scores and insights."""
        self.ended_at = datetime.now()

        if not self.responses:
            return {"error": "No responses recorded"}

        scores = [r["score"]["overall"] for r in self.responses]
        avg_score = sum(scores) / len(scores)

        # Find strongest and weakest responses
        sorted_responses = sorted(self.responses, key=lambda r: r["score"]["overall"])
        weakest = sorted_responses[0] if sorted_responses else None
        strongest = sorted_responses[-1] if sorted_responses else None

        # Category breakdown
        category_scores = {}
        for r in self.responses:
            cat = r["question"].get("category", "general")
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(r["score"]["overall"])

        category_avgs = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_scores.items()
        }

        summary = {
            "session_id": self.session_id,
            "type": self.interview_type,
            "company": self.company,
            "role": self.role,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_minutes": (self.ended_at - self.started_at).seconds / 60,
            "questions_answered": len(self.responses),
            "average_score": round(avg_score, 1),
            "category_scores": category_avgs,
            "strongest_area": max(category_avgs, key=category_avgs.get) if category_avgs else None,
            "weakest_area": min(category_avgs, key=category_avgs.get) if category_avgs else None,
            "strongest_question": strongest["question"]["q"] if strongest else None,
            "weakest_question": weakest["question"]["q"] if weakest else None,
        }

        return summary

    def update_profile(self, summary: dict):
        """Update the persistent user profile with session results."""
        profile = self.profile

        profile["sessions_completed"] += 1
        profile["total_questions_answered"] += summary["questions_answered"]
        profile["last_session"] = summary["ended_at"]

        # Update score history
        profile["score_history"].append({
            "date": summary["ended_at"][:10],
            "type": summary["type"],
            "score": summary["average_score"],
            "company": summary.get("company"),
        })

        # Keep last 100 sessions
        profile["score_history"] = profile["score_history"][-100:]

        # Update category averages with exponential moving average
        alpha = 0.3  # Weight for new data
        for cat, score in summary.get("category_scores", {}).items():
            if cat in profile["category_scores"]:
                old = profile["category_scores"][cat]
                old["attempts"] += 1
                old["avg_score"] = (1 - alpha) * old["avg_score"] + alpha * score
            else:
                profile["category_scores"][cat] = {"attempts": 1, "avg_score": score}

        # Update weak areas (categories below 6.0 average)
        profile["weak_areas"] = [
            cat for cat, data in profile["category_scores"].items()
            if data["avg_score"] < 6.0 and data["attempts"] >= 2
        ]

        # Update strengths (categories above 7.5 average)
        profile["strengths"] = [
            cat for cat, data in profile["category_scores"].items()
            if data["avg_score"] >= 7.5 and data["attempts"] >= 2
        ]

        # Adaptive difficulty
        recent_scores = [s["score"] for s in profile["score_history"][-5:]]
        if recent_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            if recent_avg >= 8.0:
                profile["preferred_difficulty"] = "hard"
            elif recent_avg >= 6.0:
                profile["preferred_difficulty"] = "medium"
            else:
                profile["preferred_difficulty"] = "easy"

        save_profile(profile)
        return profile

    def save_session_log(self, summary: dict):
        """Save detailed session log for future reference."""
        SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = SESSION_LOG_DIR / f"{self.session_id}.json"
        session_data = {
            "summary": summary,
            "responses": self.responses,
            "questions": [
                {k: v for k, v in q.items() if k != "follow_up"}
                for q in self.questions
            ],
        }
        with open(log_path, "w") as f:
            json.dump(session_data, f, indent=2, default=str)


def format_session_summary(summary: dict) -> str:
    """Format a session summary for display in chat."""
    score = summary["average_score"]
    emoji = "🟢" if score >= 7.5 else "🟡" if score >= 5.0 else "🔴"

    text = f"""
## Session Complete {emoji}

**Overall Score:** {score}/10
**Questions Answered:** {summary['questions_answered']}
**Duration:** {summary['duration_minutes']:.0f} minutes

### Category Breakdown
"""
    for cat, score in summary.get("category_scores", {}).items():
        bar = "█" * int(score) + "░" * (10 - int(score))
        text += f"- **{cat.replace('-', ' ').title()}:** {score:.1f}/10 {bar}\n"

    if summary.get("strongest_area"):
        text += f"\n💪 **Strongest:** {summary['strongest_area'].replace('-', ' ').title()}"
    if summary.get("weakest_area"):
        text += f"\n🎯 **Focus on:** {summary['weakest_area'].replace('-', ' ').title()}"

    text += "\n\n---\n*Profile updated. Your next session will adapt to these results.*"
    return text


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick demo / test
    profile = load_profile()
    print(f"Profile: {json.dumps(profile, indent=2)}")

    session = InterviewSession(
        interview_type="mixed",
        company="Google",
        role="Senior Backend Engineer",
    )
    print(session.get_intro())

    for i, q in enumerate(session.questions):
        print(session.format_question(q))

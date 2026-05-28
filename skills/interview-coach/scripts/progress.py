"""
Progress tracking and reporting for Hermes Interview Coach.

Generates visual progress reports, identifies trends, and produces
weekly recommendations based on the user's interview history.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from interview import PROFILE_PATH, SESSION_LOG_DIR, load_profile


# ── Progress Report Generation ─────────────────────────────────────────

def generate_report(
    period: str = "week",
    format: str = "summary",
) -> str:
    """
    Generate a progress report for the specified period.
    
    Args:
        period: "week", "month", or "all"
        format: "summary" (quick stats) or "detailed" (full breakdown)
    """
    profile = load_profile()
    history = profile.get("score_history", [])

    if not history:
        return """## No Data Yet

You haven't completed any interview sessions yet. Start one with:
```
/interview start --type behavioral
```
"""

    # Filter to period
    now = datetime.now()
    if period == "week":
        cutoff = now - timedelta(days=7)
        period_label = "This Week"
    elif period == "month":
        cutoff = now - timedelta(days=30)
        period_label = "This Month"
    else:
        cutoff = datetime.min
        period_label = "All Time"

    period_history = [
        s for s in history
        if datetime.fromisoformat(s["date"]) >= cutoff
    ]

    if not period_history:
        return f"## No sessions in the last {period}.\n\nTime to practice! Start a session with `/interview start`"

    # Calculate stats
    scores = [s["score"] for s in period_history]
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    sessions_count = len(period_history)

    # Trend calculation (compare first half vs second half)
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        trend = second_half_avg - first_half_avg
        trend_emoji = "📈" if trend > 0.5 else "📉" if trend < -0.5 else "➡️"
        trend_text = f"{trend_emoji} **Trend:** {'Improving' if trend > 0.5 else 'Declining' if trend < -0.5 else 'Stable'} ({trend:+.1f})"
    else:
        trend_text = "📊 *Need more sessions for trend data*"

    # Category breakdown
    category_data = profile.get("category_scores", {})

    # Build the report
    report = f"""## Interview Progress — {period_label}

### Overview
| Metric | Value |
|--------|-------|
| Sessions | {sessions_count} |
| Average Score | {avg_score:.1f}/10 |
| Best Score | {max_score:.1f}/10 |
| Lowest Score | {min_score:.1f}/10 |
| Total Questions | {profile.get('total_questions_answered', 0)} |

{trend_text}

### Score Chart
```
"""
    # ASCII score chart
    for entry in period_history[-14:]:  # Last 14 sessions
        date = entry["date"][:10]
        score = entry["score"]
        bar = "█" * int(score) + "░" * (10 - int(score))
        label = entry.get("type", "")[:4].upper().ljust(4)
        report += f"  {date} {label} {bar} {score:.1f}\n"

    report += "```\n\n"

    # Category breakdown
    report += "### Category Breakdown\n\n"
    for cat, data in sorted(category_data.items(), key=lambda x: x[1].get("avg_score", 0)):
        score = data.get("avg_score", 0)
        attempts = data.get("attempts", 0)
        bar = "█" * int(score) + "░" * (10 - int(score))
        status = "🟢" if score >= 7.5 else "🟡" if score >= 5.0 else "🔴"
        cat_name = cat.replace("-", " ").title()
        report += f"{status} **{cat_name}:** {score:.1f}/10 ({attempts} sessions) {bar}\n"

    # Strengths and weaknesses
    strengths = profile.get("strengths", [])
    weak_areas = profile.get("weak_areas", [])

    if strengths:
        report += f"\n💪 **Strengths:** {', '.join(s.replace('-', ' ').title() for s in strengths)}\n"
    if weak_areas:
        report += f"🎯 **Focus areas:** {', '.join(w.replace('-', ' ').title() for w in weak_areas)}\n"

    # Recommendations
    report += "\n### Recommendations\n\n"
    recommendations = generate_recommendations(profile, period_history)
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"

    if format == "detailed":
        report += generate_detailed_section(profile, period_history)

    return report


def generate_recommendations(profile: dict, recent_history: list) -> list[str]:
    """Generate actionable recommendations based on performance data."""
    recommendations = []
    weak_areas = profile.get("weak_areas", [])
    category_scores = profile.get("category_scores", {})
    sessions = profile.get("sessions_completed", 0)

    # Low session count
    if sessions < 5:
        recommendations.append(
            "**Build consistency** — aim for at least 3 sessions per week. "
            "Muscle memory matters more than single-session brilliance."
        )

    # Weak areas
    for area in weak_areas[:2]:
        area_name = area.replace("-", " ").title()
        recommendations.append(
            f"**Focus on {area_name}** — your scores here are below 6.0. "
            f"Try a dedicated session: `/interview start --type {area}`"
        )

    # Check if behavioral scores lack examples
    behavioral = category_scores.get("behavioral", {})
    if behavioral.get("avg_score", 10) < 7.0 and behavioral.get("attempts", 0) >= 2:
        recommendations.append(
            "**Sharpen your STAR stories** — prep 5-7 go-to stories that cover "
            "leadership, conflict, failure, and impact. Practice telling each in under 3 minutes."
        )

    # Check for score plateau
    scores = [s["score"] for s in recent_history]
    if len(scores) >= 6:
        recent_avg = sum(scores[-3:]) / 3
        older_avg = sum(scores[-6:-3]) / 3
        if abs(recent_avg - older_avg) < 0.3:
            recommendations.append(
                "**You're plateauing** — try a different interview type or increase difficulty. "
                "Growth happens at the edge of your comfort zone."
            )

    # Suggest company-specific prep
    target_companies = profile.get("target_companies", [])
    if not target_companies and sessions >= 3:
        recommendations.append(
            "**Set a target company** — company-specific prep is 2x more effective than generic practice. "
            "Use: `/interview start --company Google`"
        )

    if not recommendations:
        recommendations.append(
            "**Keep going** — your scores are strong across the board. "
            "Consider stepping up to harder questions or mock-interviewing for a stretch role."
        )

    return recommendations[:5]


def generate_detailed_section(profile: dict, recent_history: list) -> str:
    """Generate the detailed section with session-by-session breakdown."""
    text = "\n---\n\n### Session History\n\n"

    for entry in reversed(recent_history[-20:]):
        score = entry["score"]
        emoji = "🟢" if score >= 7.5 else "🟡" if score >= 5.0 else "🔴"
        company = f" @ {entry['company']}" if entry.get("company") else ""
        text += f"{emoji} **{entry['date']}** — {entry['type'].title()}{company} — {score}/10\n"

    # Session logs with detailed feedback
    if SESSION_LOG_DIR.exists():
        session_files = sorted(SESSION_LOG_DIR.glob("*.json"))[-5:]  # Last 5 sessions
        if session_files:
            text += "\n### Recent Session Details\n\n"
            for sf in session_files:
                try:
                    with open(sf) as f:
                        data = json.load(f)
                    summary = data.get("summary", {})
                    text += f"**Session {sf.stem}**\n"
                    text += f"- Type: {summary.get('type', 'unknown')}\n"
                    text += f"- Score: {summary.get('average_score', 'N/A')}/10\n"
                    text += f"- Questions: {summary.get('questions_answered', 0)}\n"
                    text += f"- Strongest: {summary.get('strongest_area', 'N/A')}\n"
                    text += f"- Weakest: {summary.get('weakest_area', 'N/A')}\n\n"
                except (json.JSONDecodeError, KeyError):
                    continue

    return text


# ── Readiness Assessment ───────────────────────────────────────────────

def assess_readiness(target_company: str | None = None) -> str:
    """Assess overall interview readiness."""
    profile = load_profile()
    category_scores = profile.get("category_scores", {})
    sessions = profile.get("sessions_completed", 0)

    if sessions < 3:
        return "⚠️ **Too early to assess** — complete at least 3 sessions first."

    # Calculate readiness score
    all_scores = [data["avg_score"] for data in category_scores.values() if data["attempts"] >= 1]
    if not all_scores:
        return "⚠️ **No category data** — complete a few more sessions."

    overall = sum(all_scores) / len(all_scores)
    weakest = min(all_scores) if all_scores else 0
    coverage = len([s for s in all_scores if s > 0]) / max(len(category_scores), 1)

    # Readiness tiers
    if overall >= 8.0 and weakest >= 6.5 and coverage >= 0.8:
        readiness = "🟢 **READY** — You're performing at a high level across all categories."
    elif overall >= 6.5 and weakest >= 5.0:
        readiness = "🟡 **ALMOST READY** — Solid foundation but some areas need polishing."
    elif overall >= 5.0:
        readiness = "🟠 **GETTING THERE** — Keep practicing, especially your weak areas."
    else:
        readiness = "🔴 **NEEDS WORK** — Focus on fundamentals before scheduling interviews."

    text = f"""## Interview Readiness Assessment

{readiness}

**Overall:** {overall:.1f}/10
**Weakest Category:** {weakest:.1f}/10
**Coverage:** {coverage:.0%} of categories practiced
**Sessions Completed:** {sessions}
"""

    if target_company:
        text += f"\n**Target:** {target_company}\n"
        if target_company.lower() in ["google", "meta", "amazon", "stripe", "apple"]:
            bar_score = {"google": 7.5, "meta": 7.0, "amazon": 7.0, "stripe": 8.0, "apple": 7.5}
            bar = bar_score.get(target_company.lower(), 7.0)
            text += f"**Estimated bar:** {bar}/10\n"
            if overall >= bar:
                text += f"✅ You're meeting the estimated bar for {target_company}.\n"
            else:
                gap = bar - overall
                text += f"⚠️ You're {gap:.1f} points below the estimated bar. Keep practicing.\n"

    return text


if __name__ == "__main__":
    print(generate_report("all", "detailed"))

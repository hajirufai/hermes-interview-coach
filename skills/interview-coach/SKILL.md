# Interview Coach

A self-improving interview preparation skill for Hermes Agent. Conducts mock interviews, tracks your performance across sessions, adapts question difficulty based on your weak spots, and sends daily practice challenges.

## When to Use

- User says "interview", "practice", "mock interview", "prep for interview"
- User mentions a company name + "interview" (e.g., "Google interview prep")
- User asks about behavioral questions, system design, coding interviews
- Cron-triggered daily practice sessions

## Capabilities

### 1. Mock Interview Sessions

Run a full mock interview tailored to the user's target role and company:

```
/interview start --type behavioral --company Google --role "Senior Backend Engineer"
/interview start --type system-design --duration 45
/interview start --type coding --difficulty hard
```

**Interview Types:**
- `behavioral` — STAR-method questions, leadership principles, conflict resolution
- `technical` — Language-specific, architecture, debugging scenarios
- `system-design` — Distributed systems, scalability, real-world design problems
- `coding` — Algorithm and data structure problems with live evaluation
- `mixed` — Combination round simulating a real interview loop

### 2. Adaptive Difficulty

The skill tracks performance in `~/.hermes/memory/interview_profile.json`:

```json
{
  "sessions_completed": 47,
  "strengths": ["system-design", "python", "behavioral-leadership"],
  "weak_areas": ["concurrency", "behavioral-conflict", "dynamic-programming"],
  "target_companies": ["Google", "Stripe"],
  "target_role": "Senior Backend Engineer",
  "score_history": [
    {"date": "2026-05-28", "type": "behavioral", "score": 7.2, "notes": "Strong STAR structure but vague metrics"}
  ]
}
```

Questions automatically weight toward weak areas. As you improve, difficulty scales up.

### 3. Company-Specific Preparation

When a target company is set, the skill:
- Researches the company's interview process via web search
- Loads company-specific question patterns (e.g., Amazon Leadership Principles, Google's L5 bar)
- Adapts evaluation criteria to match the company's known rubric
- Pulls recent Glassdoor/Blind interview reports for fresh questions

### 4. Daily Practice (Cron)

Set up automated daily challenges:

```
/interview schedule --time 08:30 --platform telegram --type mixed
```

This creates a Hermes cron job that sends one practice question each morning. Reply with your answer and get instant feedback.

### 5. Progress Reports

```
/interview report --period week
/interview report --period month --format detailed
```

Generates visual progress reports with:
- Score trends over time
- Category breakdown (behavioral / technical / system design)
- Weak area improvements
- Suggested focus areas for next week

## Evaluation Rubric

Each answer is scored 1-10 across these dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Clarity | 20% | Clear communication, structured response |
| Depth | 25% | Technical accuracy, thoroughness |
| Relevance | 20% | Directly addresses the question |
| Examples | 20% | Concrete examples, metrics, outcomes |
| Growth Signal | 15% | Self-awareness, learning demonstrated |

## Architecture

```
skills/interview-coach/
├── SKILL.md              # This file — skill definition
├── scripts/
│   ├── interview.py      # Core interview engine
│   ├── evaluate.py       # Answer evaluation with rubric
│   ├── research.py       # Company research via web tools
│   ├── progress.py       # Progress tracking and reporting
│   └── scheduler.py      # Cron-based daily practice
├── references/
│   ├── question_banks/   # Curated question sets by category
│   ├── rubrics/          # Company-specific evaluation rubrics
│   └── patterns.md       # Common interview patterns and frameworks
└── README.md
```

## Self-Improvement Loop

This skill improves itself over time:

1. **After each session:** Updates the user's interview profile with new scores and observations
2. **Weekly self-review:** Analyzes which question types the user improved on vs. plateaued, adjusts the question selection algorithm
3. **Question bank growth:** When researching companies, new questions are added to the reference bank for future sessions
4. **Rubric refinement:** If the user reports that feedback was unhelpful, the evaluation rubric is adjusted

## Dependencies

- Hermes Agent v0.15+
- Web search tool (for company research)
- File system access (for progress persistence)
- Optional: Telegram gateway (for daily challenges)

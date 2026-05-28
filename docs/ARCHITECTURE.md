# Architecture — Hermes Interview Coach

## Overview

The Interview Coach is a Hermes Agent skill — a self-contained module that plugs into the Hermes Agent runtime and extends its capabilities. It doesn't require modifications to Hermes itself; it uses the standard skill API.

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Hermes Agent                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Telegram │  │ Discord  │  │   CLI    │  ← Platforms   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       └──────────────┼─────────────┘                     │
│                      ▼                                   │
│  ┌───────────────────────────────────┐                   │
│  │         Agent Core Loop           │                   │
│  │   (model, tools, memory, skills)  │                   │
│  └───────────────┬───────────────────┘                   │
│                  │                                       │
│  ┌───────────────▼───────────────────┐                   │
│  │     Interview Coach Skill         │  ← This project   │
│  │                                   │                   │
│  │  ┌───────────┐  ┌────────────┐   │                   │
│  │  │ Interview │  │ Evaluation │   │                   │
│  │  │  Engine   │  │   Engine   │   │                   │
│  │  └─────┬─────┘  └─────┬──────┘   │                   │
│  │        │               │          │                   │
│  │  ┌─────▼─────┐  ┌─────▼──────┐   │                   │
│  │  │  Company  │  │  Progress  │   │                   │
│  │  │ Research  │  │  Tracker   │   │                   │
│  │  └─────┬─────┘  └─────┬──────┘   │                   │
│  │        │               │          │                   │
│  │  ┌─────▼───────────────▼──────┐   │                   │
│  │  │     Cron Scheduler         │   │                   │
│  │  │  (daily practice delivery) │   │                   │
│  │  └────────────────────────────┘   │                   │
│  └───────────────────────────────────┘                   │
│                  │                                       │
│  ┌───────────────▼───────────────────┐                   │
│  │   ~/.hermes/memory/               │  ← Persistence    │
│  │   ├── interview_profile.json      │                   │
│  │   ├── interview_sessions/         │                   │
│  │   ├── interview_research/         │                   │
│  │   └── interview_sent_questions.json│                  │
│  └───────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Session Flow

```
User asks for interview practice
        │
        ▼
┌─────────────────┐
│  Load Profile   │ ← ~/.hermes/memory/interview_profile.json
│  (weak areas,   │
│   difficulty,   │
│   history)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select Questions │ ← Weighted by weak areas, filtered by difficulty
│ (from bank +    │    Company-specific if target set
│  researched)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Present Q & A  │────▶│   Evaluate   │ ← LLM scores against rubric
│  (interactive)  │◀────│   Answer     │    Company-specific dimensions
└────────┬────────┘     └──────────────┘
         │
         ▼ (repeat for each question)
         │
┌─────────────────┐
│  Session Summary│ ← Aggregate scores, identify patterns
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Profile  │ ← EMA for category scores
│ (learning loop) │    Auto-adjust difficulty
│                 │    Update weak areas
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save Session   │ ← Full log for future reference
│  Log            │
└─────────────────┘
```

### 2. Adaptive Question Selection

The question selection algorithm uses weighted random sampling:

```python
weight = base_weight
if question.tags overlap user.weak_areas:
    weight *= 3.0  # 3x more likely to appear
if question.difficulty == user.preferred_difficulty:
    weight *= 1.5
if question was recently asked:
    weight *= 0.1  # avoid repeats
```

### 3. Profile Learning Loop

After each session, the profile updates using an Exponential Moving Average:

```
new_score = (1 - α) × old_score + α × session_score
where α = 0.3 (recent performance weighted 30%)
```

This means:
- Recent performance matters more than ancient history
- A single bad session doesn't tank your profile
- Sustained improvement is reflected accurately
- Difficulty auto-scales based on the EMA of last 5 sessions

### 4. Company Research Pipeline

```
User sets target company
        │
        ▼
┌─────────────────┐
│ Check cache     │ ← 7-day TTL
│ (researched?)   │
└────┬───────┬────┘
     │ miss  │ hit
     ▼       ▼
┌─────────┐  Return cached
│ Web     │
│ Search  │  ← 5 parallel queries
│ (batch) │
└────┬────┘
     │
     ▼
┌─────────────────┐
│ LLM Synthesis   │ ← Structured output
│ (interview      │
│  brief format)  │
└────┬────────────┘
     │
     ├──▶ Cache result
     │
     ▼
┌─────────────────┐
│ Update question │ ← New questions added to bank
│ bank            │
└─────────────────┘
```

## Memory Schema

### interview_profile.json

```json
{
  "sessions_completed": 47,
  "total_questions_answered": 235,
  "strengths": ["system-design", "python"],
  "weak_areas": ["concurrency", "behavioral-conflict"],
  "target_companies": ["Google", "Stripe"],
  "target_role": "Senior Backend Engineer",
  "preferred_difficulty": "hard",
  "score_history": [
    {
      "date": "2026-05-28",
      "type": "behavioral",
      "score": 7.2,
      "company": "Google"
    }
  ],
  "category_scores": {
    "behavioral": {"attempts": 15, "avg_score": 7.4},
    "technical": {"attempts": 12, "avg_score": 7.1},
    "system-design": {"attempts": 10, "avg_score": 8.3},
    "coding": {"attempts": 10, "avg_score": 6.8}
  },
  "created_at": "2026-05-01T10:00:00",
  "last_session": "2026-05-28T14:30:00"
}
```

## Hermes Integration Points

| Integration Point | How We Use It |
|---|---|
| `SKILL.md` | Skill definition — Hermes reads this to understand when to activate |
| `~/.hermes/memory/` | Profile, session logs, research cache — persists across sessions |
| `hermes.tools.web_search` | Company research — real-time interview intelligence |
| `hermes.tools.read_file` / `write_file` | Profile and session persistence |
| `hermes.memory` | Hermes native memory API for profile data |
| `hermes.skills` | Skill path resolution and self-registration |
| Cron system | Daily practice delivery via natural language schedule |
| Gateway | Multi-platform delivery (Telegram, Discord, etc.) |
| User modeling (Honcho) | Builds understanding of the user's career goals |

## Design Decisions

### Why a Hermes Skill vs. Standalone App?

1. **Memory is free** — Hermes already handles persistence. We don't need a database.
2. **Multi-platform is free** — Hermes gateway handles Telegram, Discord, etc. We don't write platform code.
3. **The model is free** — User chooses their own LLM. We write prompts, not API calls.
4. **Cron is free** — Built-in scheduler handles daily practice without external infrastructure.
5. **Learning is natural** — Hermes's learning loop philosophy maps perfectly to interview prep.

### Why EMA for Score Tracking?

Exponential Moving Average gives more weight to recent performance while maintaining historical context. This matters because:
- People improve over time (we want to reflect that)
- Bad days happen (one session shouldn't destroy a profile)
- We need a signal for difficulty adjustment (recent trend matters more)

### Why 5 Dimensions in the Rubric?

Based on real FAANG interview rubric research:
- **Clarity** and **Depth** are universal
- **Relevance** catches tangent-prone candidates
- **Examples** separates good from great (specificity matters)
- **Growth Signal** is what distinguishes senior+ candidates

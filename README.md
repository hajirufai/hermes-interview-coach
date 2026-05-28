# Hermes Interview Coach ☤🎯

**A self-improving interview preparation agent built on [Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Most interview prep is broken. You grind LeetCode in isolation, read generic blog posts, and walk into your Google onsite hoping muscle memory kicks in. There's no feedback loop. No one tells you that your STAR stories lack metrics, or that you always skip requirements clarification in system design.

Hermes Interview Coach fixes this. It's a Hermes Agent skill that conducts mock interviews, evaluates your answers against real rubrics, tracks your performance across sessions, and adapts to your weak spots over time. It gets better the more you use it — because Hermes remembers.

**[🌐 Live Demo](https://hermes-interview-coach.vercel.app)** · **[📖 DEV.to Article](https://dev.to/hajirufai)** · **[☤ Hermes Agent](https://github.com/NousResearch/hermes-agent)**

---

## What It Does

### 🎤 Mock Interview Sessions

Run realistic mock interviews tailored to your target role and company:

```bash
hermes> /interview start --type behavioral --company Google --role "Senior Backend Engineer"
```

Choose from five interview types:
- **Behavioral** — STAR-method questions across leadership, conflict, failure, and impact
- **Technical** — Language-specific deep dives, architecture, debugging
- **System Design** — Distributed systems, scalability, real-world design
- **Coding** — Algorithms and data structures with live evaluation
- **Mixed** — Full interview loop simulation

### 📊 Scored Feedback

Every answer is evaluated across five dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Clarity | 20% | Clear structure, logical flow |
| Depth | 25% | Technical accuracy, thoroughness |
| Relevance | 20% | Directly addresses the question |
| Examples | 20% | Concrete examples with metrics |
| Growth Signal | 15% | Self-awareness, learning |

Company-specific rubrics add extra dimensions (e.g., Amazon Leadership Principles, Google Googleyness, Stripe Rigor).

### 🧠 Learning Loop (The Key Differentiator)

This is where Hermes Agent's architecture shines. After each session:

1. **Your profile updates** — scores, weak areas, strengths, preferred difficulty
2. **Questions adapt** — weighted selection favors your weak spots
3. **Difficulty scales** — consistently scoring 8+? Questions get harder automatically
4. **The skill self-improves** — new questions from company research get added to the bank

Your interview profile persists in `~/.hermes/memory/interview_profile.json` — it survives restarts, model switches, and platform changes.

### 🔍 Company Intelligence

Set a target company and get real-time interview intel:

```bash
hermes> /interview research Google --role "L5 Backend"
```

Uses Hermes Agent's web search to gather:
- Interview process and timeline
- Common questions from Glassdoor/Blind
- Culture signals and what they actually evaluate
- Compensation ranges
- Red flags to avoid

Results are cached for a week and feed back into question selection.

### ⏰ Daily Practice (Cron)

Set up automated daily challenges via any Hermes-connected platform:

```bash
hermes> /interview schedule --time 08:30 --platform telegram
```

Every weekday morning, you get one practice question weighted toward your weak areas. Reply with your answer and get instant scored feedback. Consistency > intensity.

### 📈 Progress Reports

Track your improvement over time:

```bash
hermes> /interview report --period month
```

```
## Interview Progress — This Month

Sessions: 23
Average Score: 7.4/10
Trend: 📈 Improving (+1.2)

Category Breakdown:
🟢 System Design: 8.1/10 ████████░░
🟢 Behavioral:    7.8/10 ███████░░░
🟡 Technical:     6.9/10 ██████░░░░
🟡 Coding:        6.2/10 ██████░░░░

💪 Strengths: System Design, Behavioral Leadership
🎯 Focus on: Coding, Concurrency
```

### 🎯 Readiness Assessment

Before scheduling real interviews, check your readiness:

```bash
hermes> /interview ready --company Stripe
```

Compares your scores against estimated interview bars for major companies.

---

## Installation

### Prerequisites
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed and configured
- Any LLM provider (OpenRouter, Nous Portal, OpenAI, Ollama, etc.)
- Web search tool enabled (for company research)

### Install the Skill

```bash
# Clone into your Hermes skills directory
git clone https://github.com/hajirufai/hermes-interview-coach.git \
  ~/.hermes/skills/interview-coach

# Or copy just the skill folder
cp -r skills/interview-coach ~/.hermes/skills/

# Restart Hermes to load the new skill
hermes
```

The skill auto-activates when you mention anything interview-related. Or trigger it directly:

```bash
hermes> /interview-coach
```

### Quick Start

```bash
# 1. Start your first mock interview
hermes> I want to practice for a Google backend interview

# 2. Answer the questions naturally — just type your response

# 3. Check your progress after a few sessions
hermes> /interview report

# 4. Set up daily practice
hermes> /interview schedule --time 08:30 --platform telegram
```

---

## Architecture

```
hermes-interview-coach/
├── skills/interview-coach/
│   ├── SKILL.md                 # Skill definition (Hermes reads this)
│   └── scripts/
│       ├── interview.py         # Core engine — sessions, questions, profiles
│       ├── evaluate.py          # Answer evaluation with rubrics
│       ├── research.py          # Company research via web search
│       ├── progress.py          # Progress tracking and reports
│       └── scheduler.py         # Cron-based daily practice
├── tools/
│   └── interview_tool.py        # Hermes tool registration
├── dashboard/                   # Web dashboard (Next.js)
│   ├── index.html               # Landing page
│   └── ...
├── examples/
│   └── sample_session.md        # Example session transcript
└── docs/
    ├── ARCHITECTURE.md          # Technical deep dive
    └── QUESTION_BANK.md         # Full question bank reference
```

### How It Uses Hermes Agent

| Hermes Feature | How Interview Coach Uses It |
|---------------|---------------------------|
| **Learning Loop** | Profile updates after every session; question selection adapts |
| **Persistent Memory** | Interview profile, session logs, company research cache |
| **Tool Use** | Web search for company research; file I/O for progress |
| **Cron Scheduling** | Daily practice questions on any connected platform |
| **Multi-Platform** | Practice from Telegram, Discord, Slack, or CLI |
| **Skills System** | Self-contained skill with auto-improving question banks |
| **User Modeling** | Tracks strengths, weaknesses, and learning trajectory |
| **Subagent Delegation** | Parallel company research while conducting interviews |

---

## Configuration

### Set Target Company and Role

```bash
hermes> I'm preparing for a Senior Backend Engineer role at Stripe
```

Or set directly in your profile:

```json
// ~/.hermes/memory/interview_profile.json
{
  "target_companies": ["Stripe", "Google"],
  "target_role": "Senior Backend Engineer",
  "preferred_difficulty": "hard"
}
```

### Customize Question Bank

Add your own questions to `references/question_banks/`:

```json
{
  "q": "Design a payment processing system that handles idempotency.",
  "key_areas": ["idempotency keys", "exactly-once", "reconciliation", "failure modes"],
  "difficulty": "hard",
  "duration_minutes": 40,
  "source": "stripe-style"
}
```

### Adjust Evaluation Weights

Edit the rubric in `scripts/evaluate.py` to match your priorities:

```python
RUBRIC = {
    "clarity": {"weight": 0.20},    # Adjust these weights
    "depth": {"weight": 0.30},      # to match your focus
    "relevance": {"weight": 0.15},
    "examples": {"weight": 0.20},
    "growth_signal": {"weight": 0.15},
}
```

---

## Example Session

```
hermes> I want to practice behavioral interviews for Amazon

## Mock Interview Session #12

Type: Behavioral targeting Amazon
Questions: 5
Duration: ~30 minutes

I'll ask you 5 questions mapped to Amazon's Leadership Principles.
Let's begin.

---

### Question 1/5 — Behavioral (Leadership)

Tell me about a time you had to lead a project with unclear requirements.

---

> hermes> At my previous company, we had a client request for a "real-time analytics
> dashboard" with no spec beyond that phrase. The PM had left, so I stepped up.
> First, I scheduled 3 stakeholder interviews to extract actual requirements —
> turns out "real-time" meant "within 5 minutes" not milliseconds, which changed
> everything. I wrote a one-page proposal with two options (WebSocket vs polling),
> got sign-off in a day, and led a 3-person team to ship in 2 weeks.
> We reduced their manual reporting time from 4 hours/day to zero.

### Evaluation 🟢 — 8.2/10

**Clarity:** 9/10 ████████░░
  Clear STAR structure. Easy to follow the narrative.
  💡 Consider signposting: "Let me walk you through the situation, my approach, and the outcome."

**Depth:** 7/10 ███████░░░
  Good technical context. Could go deeper on the WebSocket vs polling trade-off decision.
  💡 Explain WHY you chose polling — what were the constraints?

**Relevance:** 9/10 ████████░░
  Directly addresses ambiguity, decision-making, and execution.

**Examples:** 9/10 ████████░░
  Strong metrics: "4 hours/day to zero", "2 weeks", "3 stakeholder interviews"
  💡 Add team size context and your specific role vs delegation

**Growth Signal:** 7/10 ███████░░░
  Shows initiative but could add what you learned about handling ambiguity going forward.
  💡 End with: "This taught me that unclear requirements are usually a communication gap, not a spec gap."

✅ What went well: Excellent STAR structure with concrete metrics.
🎯 Focus on: Add a reflection on what you learned — Amazon values "Learn and Be Curious."

📋 A strong answer would cover:
  - How you identified the ambiguity
  - Your process for resolving it
  - Specific trade-offs you evaluated
  - Measurable outcome with business impact
  - What you learned and applied to future projects
```

---

## Contributing

Pull requests welcome! Areas where help is needed:

- **Question banks** — especially for companies beyond FAANG
- **Rubric refinements** — if you're an interviewer, your calibration input is gold
- **Language support** — evaluation prompts in other languages
- **Platform integrations** — new Hermes gateway platforms

---

## License

MIT — see [LICENSE](LICENSE).

Built for the [Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15) on DEV.to.

Powered by [Hermes Agent](https://github.com/NousResearch/hermes-agent) from [Nous Research](https://nousresearch.com).

---
title: I Built a Self-Improving Interview Coach With Hermes Agent (And It Already Knows My Weak Spots)
published: false
tags: hermesagentchallenge, devchallenge, agents
---

*This is a submission for the [Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15)*

## What I Built

I got tired of the interview prep cycle. You know how it goes — you buy a LeetCode premium subscription, grind for a week, do a mock with a friend who asks surface-level questions and tells you "that was great" when it wasn't, and then you walk into a Google onsite and blank on a system design question because nobody told you that you *always* skip requirements clarification.

The problem isn't a lack of content. There are millions of interview questions online. The problem is there's no feedback loop. Nobody tracks that you've answered 12 behavioral questions and 11 of them got vague on the "results" part of STAR. Nobody notices you keep saying "we" instead of "I" — which is a red flag at Amazon specifically. Nobody adjusts the next question based on what you just botched.

So I built **Hermes Interview Coach** — a Hermes Agent skill that conducts mock interviews, scores your answers against real rubrics, remembers your weak spots across sessions, and adapts its questions to challenge you where it matters. The key word is *across sessions*. This isn't a one-shot chatbot. It learns.

## Demo

### Starting a Session

```
hermes> I want to practice for a Google backend interview

## Mock Interview Session #12

Type: Behavioral targeting Google
Questions: 5 · Duration: ~30 min
Difficulty: Hard (auto-scaled from your history)

Your profile shows strength in system design (8.1 avg) 
but room to grow in behavioral-conflict (5.8 avg).
I'll weight questions accordingly.
```

The coach noticed I'm weak on conflict-resolution questions. It didn't ask me. It looked at my profile — scores from every previous session, aggregated by category with exponential moving averages — and decided to weight today's questions toward that gap.

### Getting Scored Feedback

After I answer a behavioral question about leading a project with unclear requirements:

```
### Evaluation 🟢 — 8.2/10

Clarity     9/10 ████████░░  Clear STAR structure
Depth       7/10 ███████░░░  Could explore trade-offs deeper
Relevance   9/10 ████████░░  Directly addresses the question
Examples    9/10 ████████░░  Strong metrics: 4hrs → 0
Growth      7/10 ███████░░░  Add what you learned

✅ Strong STAR structure with concrete metrics
🎯 Add a reflection — Google values "Learn and Be Curious"

Profile updated · Weak areas recalculated
Next question weighted toward: concurrency, conflict
```

Five dimensions, each weighted. And because I said "targeting Google," it's also silently checking for *Googleyness* — collaboration, humility, structured thinking. If I'd said Amazon, it'd add Leadership Principle alignment. Stripe adds rigor scoring.

### Progress Over Time

```
hermes> /interview report --period month

Sessions: 23 · Average: 7.4/10 · Trend: 📈 +1.2

🟢 System Design:    8.1/10 ████████░░
🟢 Behavioral:       7.8/10 ███████░░░
🟡 Technical:        6.9/10 ██████░░░░
🟡 Coding:           6.2/10 ██████░░░░

💪 Strengths: System Design, Behavioral Leadership
🎯 Focus on: Coding, Concurrency
```

The ASCII charts are silly but I genuinely love them. At a glance you see where you're strong and where you need work.

### 🌐 Landing Page

**[hermes-interview-coach.vercel.app](https://hermes-interview-coach.vercel.app)**

## Code

**GitHub:** [hajirufai/hermes-interview-coach](https://github.com/hajirufai/hermes-interview-coach)

### My Tech Stack

- **Hermes Agent** — runtime, memory, cron, multi-platform delivery
- **Python** — all skill scripts (interview engine, evaluation, research, scheduling)
- **HTML/CSS** — landing page dashboard
- **Vercel** — hosting for the landing page

The entire interview coach is ~1,800 lines of Python across 5 modules. No database. No API server. No infrastructure to manage. Hermes Agent *is* the infrastructure.

## How I Used Hermes Agent

This is where I need to be honest — and hopefully where this submission stands out from the "I wrapped Hermes in a prompt" entries.

I didn't just use Hermes Agent to make API calls. I built on top of its *architecture*. Every major Hermes feature is doing real, structural work. Here's the breakdown:

### The Learning Loop (The Real Differentiator)

Most AI tools are stateless. You close the tab, and all that context is gone. Hermes Agent has a built-in learning loop — it creates skills from experience, improves them during use, and builds a model of who you are across sessions.

For interview prep, this is *exactly* what you need. Here's what happens after every session:

1. **Profile update** — Your scores get recorded with exponential moving averages (α=0.3, so recent performance matters more but a single bad day doesn't destroy you).
2. **Question adaptation** — Next session, the selection algorithm weights questions 3x toward your weak categories.
3. **Difficulty scaling** — Scoring 8+ consistently? Questions get harder automatically. Plateauing? It suggests switching interview types.
4. **Self-improvement** — When you research a company, the discovered questions get added to the question bank. The skill literally grows.

This is stored in `~/.hermes/memory/interview_profile.json` — it survives restarts, model switches, and even platform changes.

### Persistent Memory

Your interview profile, session logs, company research cache, and daily practice tracker all live in Hermes's persistent memory. I don't manage a database. I don't run a server. I write to `~/.hermes/memory/` and Hermes handles the rest.

Here's what that profile looks like after a few weeks of practice:

```json
{
  "sessions_completed": 47,
  "total_questions_answered": 235,
  "strengths": ["system-design", "python"],
  "weak_areas": ["concurrency", "behavioral-conflict"],
  "target_companies": ["Google", "Stripe"],
  "preferred_difficulty": "hard",
  "category_scores": {
    "behavioral": {"attempts": 15, "avg_score": 7.4},
    "system-design": {"attempts": 10, "avg_score": 8.3}
  }
}
```

### Multi-Platform Delivery

I built this once. But because Hermes Agent supports Telegram, Discord, Slack, WhatsApp, and CLI — users can practice from their phone during commute and pick up on their laptop later. Same profile. Same progress. No extra code from me.

### Cron Scheduling

The daily practice feature uses Hermes's built-in cron system:

```
hermes> /interview schedule --time 08:30 --platform telegram
```

Every weekday morning, it picks a question weighted toward your weak areas and sends it. Reply with your answer, get instant scored feedback. I didn't build a scheduler — Hermes has one. I just told it what to schedule.

### Tool Use

Company research uses Hermes's web search tool. When you say "I'm preparing for Stripe," it runs 5 parallel search queries — interview process, common questions, culture signals, compensation data, and Glassdoor/Blind experiences. Results get synthesized into a structured brief and cached for a week.

```
hermes> /interview research Google --role "L5 Backend"

🔍 Interview Intel — Google (Senior Backend Engineer)

Interview Process:
- Rounds: 5
- Stages: Recruiter → Phone → Onsite (4-5) → Team Match → HC
- Timeline: ~30 days

Common Questions:
1. ⚙️ Design a rate limiter for an API gateway
   💡 Start with requirements, discuss token bucket vs sliding window
2. 🗣️ Tell me about a time you disagreed with a tech decision
   💡 Show you can disagree AND commit. Google values this.
...
```

### Skills System

The interview coach is a self-contained Hermes skill. It auto-activates when you mention anything interview-related. The SKILL.md file defines the capability, and Hermes reads it to understand when to activate. No explicit trigger needed — just start talking about interview prep.

### The Architecture Table

| Hermes Feature | What It Does in Interview Coach |
|---|---|
| Learning Loop | Profile updates, question adaptation, difficulty scaling |
| Persistent Memory | Profile, sessions, research cache — no database needed |
| Tool Use | Web search for company research |
| Cron | Daily practice delivery on any platform |
| Multi-Platform | Practice from Telegram, Discord, Slack, or CLI |
| Skills System | Self-contained, auto-activating skill |
| User Modeling | Tracks career goals, strengths, learning trajectory |
| Subagent Delegation | Parallel company research during sessions |

### What Made This Click

I've tried building interview prep tools before — including a [Gemma 4 Interview Coach](https://dev.to/hajirufai/gemma4-interview-coach) a few weeks back. That one was a browser-based chatbot. It worked, but it was stateless. Every session started fresh. You couldn't track progress. You couldn't adapt.

Hermes Agent made the difference because the problem I was solving is *inherently agentic*. Interview prep isn't about one conversation — it's about a relationship that develops over weeks. A coach that remembers. A system that adapts. A feedback loop that compounds.

That's what Hermes was built for.

---

If you want to try it: [GitHub repo](https://github.com/hajirufai/hermes-interview-coach) · [Landing page](https://hermes-interview-coach.vercel.app)

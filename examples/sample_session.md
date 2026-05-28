# Sample Interview Session — Hermes Interview Coach

This is a transcript of a real mock interview session conducted by the Hermes Interview Coach. The user is preparing for a Senior Backend Engineer position at Google.

---

## Session Setup

```
hermes> I want to practice for my Google interview. Senior Backend Engineer, L5.
```

```
## Mock Interview Session #12

Type: Mixed targeting Google for Senior Backend Engineer
Questions: 5
Duration: ~35 minutes
Difficulty: Hard (auto-scaled — your last 5 sessions averaged 7.8)

Your profile shows strength in system design (8.1 avg) but room to grow in
behavioral-conflict (5.8 avg) and concurrency (6.2 avg).
I'll weight questions accordingly.

Let's begin.
```

---

## Question 1 — Behavioral (Conflict)

```
### Question 1/5 — Behavioral

Describe a situation where two teams had conflicting priorities and you
were caught in the middle.

*This question targets your weak area: conflict resolution*
```

### User's Answer

> At Acme Corp, our platform team wanted to migrate to a new API gateway 
> (6-month project), but the product team needed us to ship a payments 
> integration within 8 weeks for a key enterprise client.
>
> I was the tech lead touching both workstreams. Instead of picking sides,
> I mapped out the actual dependencies. Turns out the gateway migration 
> only blocked payments in one area — webhook routing. So I proposed a 
> tactical solution: build the webhook layer as a standalone service that
> would work with both the old and new gateway. It added 2 weeks to the 
> payments timeline but saved the platform team 3 months of workaround code.
>
> Both teams agreed. We shipped payments in 10 weeks (2 weeks late but the
> client was fine with it since we communicated early), and the gateway 
> migration finished on schedule because they didn't have to maintain 
> compatibility shims.
>
> What I learned: most "conflicting priorities" are actually poorly mapped
> dependencies. If you trace the actual technical overlap, there's usually
> a path that doesn't require choosing sides.

### Evaluation

```
### Evaluation 🟢 — 8.5/10

Clarity     9/10 ████████░░  Perfect narrative arc: conflict → analysis → solution → outcome
Depth       8/10 ████████░░  Good technical detail on the decoupling approach
Relevance   9/10 ████████░░  Directly addresses cross-team conflict resolution
Examples    9/10 ████████░░  Specific timelines: 6mo, 8wk, 10wk. Named the actual technical solution.
Growth      8/10 ████████░░  Strong closing insight about dependency mapping

✅ What went well: Excellent conflict resolution narrative — showed you can find
   creative solutions instead of escalating. The closing insight is a mic drop.

🎯 Focus on: Consider mentioning HOW you got both teams aligned. Did you present
   the proposal in a meeting? Write an RFC? Google values "influence without authority."

📋 A strong answer would cover:
  - The stakes: what was at risk if neither project shipped
  - Your specific influence approach (meeting, doc, 1:1s)
  - How you managed the 2-week delay communication
  - What you'd do differently (shows self-awareness)

🏷️ Googleyness bonus: This answer demonstrates collaboration and structured
   problem-solving — strong Googleyness signals.

Profile updated: behavioral-conflict score improved from 5.8 → 6.6 (EMA)
```

---

## Question 2 — System Design

```
### Question 2/5 — System Design

Design a notification system that handles 10M+ daily notifications 
across email, push, and SMS.

Key areas: message queues, priority, deduplication, user preferences,
delivery tracking
Suggested time: 45 minutes
```

### User's Answer

> *[Abbreviated for sample — user gave a full system design answer covering
> requirements clarification, back-of-envelope math, high-level architecture,
> deep dive on the priority queue system, and trade-off discussions]*

### Evaluation

```
### Evaluation 🟢 — 8.8/10

Requirements    9/10  Started with clarifying questions — exactly right
High-Level     9/10  Clean architecture: ingestion → routing → delivery → tracking
Deep Dive      8/10  Strong on priority queues, good Kafka partition strategy
Trade-offs     9/10  Excellent comparison of push vs pull for delivery workers
Scalability    8/10  Addressed horizontal scaling but could explore geo-distribution
Communication  9/10  Clear, structured walkthrough with good use of diagrams

Key areas covered: ✅ message queues ✅ priority ✅ deduplication ✅ user preferences ✅ delivery tracking
Key areas missed: partial — geo-distribution, retry/backoff strategy

✅ System design remains your strongest category (8.3 running avg)
🎯 Consider discussing: multi-region deployment and how you'd handle
   provider-specific rate limits (Twilio, APNS, FCM all have different limits)
```

---

## Session Summary

```
## Session Complete 🟢

Overall Score: 8.2/10
Questions Answered: 5
Duration: 38 minutes

Category Breakdown:
🟢 System Design:    8.8/10 ████████░░
🟢 Behavioral:       8.0/10 ████████░░
🟡 Technical:        7.8/10 ███████░░░

💪 Strongest: System Design
🎯 Focus on: Behavioral — specifically conflict and failure stories

Trend: 📈 Improving (+0.6 from last week)

Recommendations:
1. Your behavioral-conflict score jumped from 5.8 → 6.6 — great progress.
   Do 2 more conflict-focused sessions this week to lock it in.
2. Consider scheduling your actual Google interview — you're meeting the L5 bar.
3. Set up daily practice to maintain momentum: /interview schedule

Profile updated. Next session will adapt to these results.
```

---

## After the Session

The user's profile at `~/.hermes/memory/interview_profile.json` now reflects:

```json
{
  "sessions_completed": 12,
  "total_questions_answered": 58,
  "strengths": ["system-design"],
  "weak_areas": ["concurrency"],
  "target_companies": ["Google"],
  "target_role": "Senior Backend Engineer",
  "preferred_difficulty": "hard",
  "category_scores": {
    "behavioral": {"attempts": 8, "avg_score": 7.2},
    "system-design": {"attempts": 6, "avg_score": 8.3},
    "technical": {"attempts": 5, "avg_score": 7.1},
    "coding": {"attempts": 3, "avg_score": 6.5}
  }
}
```

Next session, questions will:
- Target concurrency (still a weak area)
- Include harder behavioral questions (score is improving)
- Mix in coding problems (least practiced category)

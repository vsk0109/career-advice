# Scoring Algorithm — Career Suitability

This is the deterministic, explainable "AI" core. It's a weighted matching algorithm, not a trained model — that's a legitimate and honest design choice for a 1-week build, and it's easy to explain and defend to judges.

## Background — the RIASEC model

RIASEC (aka the Holland Code) is a career-psychology model (John Holland,
1950s-70s): people's occupational interests cluster into six orientations.
Each letter describes an interest/personality type, not a skill level, and
most people (and careers) are a blend of 2-3 dimensions rather than one pure
type:

- **R**ealistic — hands-on, mechanical, outdoors → trades, engineering, physical work
- **I**nvestigative — analytical, scientific, curious → research, data, medicine
- **A**rtistic — creative, expressive, unstructured → design, writing, music
- **S**ocial — helping, teaching, communicating → counseling, education, healthcare
- **E**nterprising — leading, persuading, risk-taking → business, sales, entrepreneurship
- **C**onventional — organized, detail-oriented, rule-following → admin, accounting, data entry

This app collects it via 12 fixed Likert-scale (1-5) statements — 2 per
dimension, defined in `backend/app/data/riasec_questions.py` — and matches
`riasec_answers[i]` to the question at that same index, so the answers array
and the question list must stay in the same order.

## Step 1 — RIASEC Personality Score

Use a simplified Holland Code (RIASEC) quiz: 12-18 short statements ("I enjoy fixing or building things", "I like analyzing data and solving puzzles", "I enjoy creative writing or art", etc.), each tagged to one of six dimensions:

- **R**ealistic — hands-on, mechanical, outdoors
- **I**nvestigative — analytical, scientific, research
- **A**rtistic — creative, expressive
- **S**ocial — helping, teaching, communicating
- **E**nterprising — leading, persuading, business
- **C**onventional — organizing, detail-oriented, structured

Each statement rated 1-5 (Likert scale). Sum ratings per dimension → normalize to 0-10 scale. Result: `student_riasec = {"R": 3, "I": 8, "A": 5, "S": 2, "E": 4, "C": 6}`.

Each career in the dataset has an equivalent `career_riasec` profile (assign these manually during data curation, based on how the career is generally understood — e.g., Software Engineer skews I/C, Graphic Designer skews A/E).

**RIASEC match score** = cosine similarity or simple normalized distance between `student_riasec` and `career_riasec` vectors, scaled to 0-100. Cosine similarity (not raw distance) measures the *angle* between the two vectors — whether the student's shape of interests points in the same direction as the career's — rather than penalizing someone who simply rated every dimension more intensely.

```python
def riasec_match(student_vec: dict, career_vec: dict) -> float:
    dims = ["R", "I", "A", "S", "E", "C"]
    dot = sum(student_vec[d] * career_vec[d] for d in dims)
    norm_s = sum(student_vec[d]**2 for d in dims) ** 0.5
    norm_c = sum(career_vec[d]**2 for d in dims) ** 0.5
    if norm_s == 0 or norm_c == 0:
        return 0.0
    cosine = dot / (norm_s * norm_c)
    return round(cosine * 100, 1)  # 0-100
```

## Step 2 — Academic Fit Score

For each career's `relevant_subjects`, compute the student's average mark across those subjects, normalized to 0-100.

```python
def academic_fit(student_academics: dict, relevant_subjects: list) -> float:
    marks = [student_academics[s] for s in relevant_subjects if s in student_academics]
    if not marks:
        return 50.0  # neutral default if no overlap data
    return round(sum(marks) / len(marks), 1)
```

## Step 3 — Interest/Hobby Overlap Score

Simple keyword/tag overlap between student's selected interests+hobbies and the career's associated tags (you'll want a small tag mapping in your dataset, e.g. career "Data Scientist" tagged with interests `["technology", "problem-solving", "research"]`).

```python
def interest_overlap(student_interests: list, student_hobbies: list, career_tags: list) -> float:
    student_tags = set(t.lower() for t in student_interests + student_hobbies)
    career_tag_set = set(t.lower() for t in career_tags)
    if not career_tag_set:
        return 50.0
    overlap = len(student_tags & career_tag_set)
    return round(min(overlap / len(career_tag_set), 1.0) * 100, 1)
```

## Step 4 — Self-Rated Skill Score

Average of the student's self-rated scores (1-5 → scaled to 0-100) for skills the career requires.

```python
def skill_score(student_skills: dict, required_skills: list) -> float:
    ratings = [student_skills[s] for s in required_skills if s in student_skills]
    if not ratings:
        return 50.0
    avg = sum(ratings) / len(ratings)   # 1-5 scale
    return round((avg / 5) * 100, 1)
```

## Step 5 — Weighted Final Score

```python
def career_suitability_score(student, career) -> float:
    riasec = riasec_match(student["riasec_scores"], career["riasec_tags"])
    academic = academic_fit(student["academics"], career["relevant_subjects"])
    interest = interest_overlap(student["interests"], student["hobbies"], career.get("interest_tags", []))
    skill = skill_score(student["self_rated_skills"], career["required_skills"])

    final = (
        0.40 * riasec +
        0.30 * academic +
        0.20 * interest +
        0.10 * skill
    )
    return round(final, 1)
```

Run this across all careers in the dataset, sort descending, return the top 5 as the "Top Recommended Career Paths" with the score shown as the "Career Suitability %."

**Tune the weights during Day 3 testing** — run a few sample profiles through it and sanity-check the output makes intuitive sense (e.g. a student strong in Math/Physics with investigative personality should land Engineering/Data Science near the top).

## Step 6 — Skill Gap Analysis

For the top-ranked career, diff the student's self-rated skills against `required_skills`:

```python
def skill_gap(student_skills: dict, required_skills: list) -> list:
    gaps = []
    for skill in required_skills:
        rating = student_skills.get(skill, 0)
        if rating < 3:   # below "competent" threshold
            gaps.append(skill)
    return gaps
```

This list feeds both the dashboard's skill-gap checklist and the prompt sent to the LLM for the personalized roadmap.

## Step 7 — Handing off to the LLM

Once you have the top 5 careers + scores + skill gaps, send this structured data to the LLM with a prompt like:

> "A student has these top career matches with scores: [...]. Their skill gaps for the top match are: [...]. Their academic strengths are: [...]. Write: (1) a 2-sentence explanation of why each top career fits them, (2) a 3-step personalized learning roadmap to close their skill gaps for the top career, (3) one emerging career trend related to their top match."

This keeps the LLM doing what it's good at (natural language, contextual reasoning) while the actual ranking stays deterministic and explainable — which also protects you from the LLM "hallucinating" a wrong ranking.

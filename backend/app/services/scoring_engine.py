"""
Career suitability scoring engine.

Pure Python — no FastAPI or DB imports here on purpose, so this module can be
unit tested and reasoned about independently. See docs/03_SCORING_ALGORITHM.md
for the full write-up of why each step works this way.
"""

RIASEC_DIMENSIONS = ["R", "I", "A", "S", "E", "C"]

# Weights for the final blended score. Tune these once you've run a few
# sample profiles through and sanity-checked the output (Day 3 task).
WEIGHTS = {
    "riasec": 0.40,
    "academic": 0.30,
    "interest": 0.20,
    "skill": 0.10,
}

SKILL_GAP_THRESHOLD = 3  # self-rating below this (out of 5) counts as a gap


def compute_riasec_scores(riasec_answers: list[int], question_dimension_map: list[str]) -> dict[str, float]:
    """
    Turn raw 1-5 quiz answers into a normalized 0-10 score per RIASEC dimension.

    question_dimension_map[i] tells you which dimension riasec_answers[i] belongs to.
    Both lists must be the same length and in the same fixed question order.
    """
    totals = {d: 0 for d in RIASEC_DIMENSIONS}
    counts = {d: 0 for d in RIASEC_DIMENSIONS}

    for answer, dimension in zip(riasec_answers, question_dimension_map):
        if dimension in totals:
            totals[dimension] += answer
            counts[dimension] += 1

    scores = {}
    for d in RIASEC_DIMENSIONS:
        if counts[d] == 0:
            scores[d] = 0.0
        else:
            avg = totals[d] / counts[d]          # 1-5 scale
            scores[d] = round((avg / 5) * 10, 1)  # normalize to 0-10
    return scores


def riasec_match(student_vec: dict, career_vec: dict) -> float:
    """Cosine similarity between student and career RIASEC vectors, scaled to 0-100."""
    dot = sum(student_vec.get(d, 0) * career_vec.get(d, 0) for d in RIASEC_DIMENSIONS)
    norm_s = sum(student_vec.get(d, 0) ** 2 for d in RIASEC_DIMENSIONS) ** 0.5
    norm_c = sum(career_vec.get(d, 0) ** 2 for d in RIASEC_DIMENSIONS) ** 0.5
    if norm_s == 0 or norm_c == 0:
        return 0.0
    cosine = dot / (norm_s * norm_c)
    return round(max(cosine, 0) * 100, 1)


def academic_fit(student_academics: dict, relevant_subjects: list[str]) -> float:
    """Average of the student's marks in the career's relevant subjects, 0-100."""
    marks = [student_academics[s] for s in relevant_subjects if s in student_academics]
    if not marks:
        return 50.0  # neutral default when there's no overlap data
    return round(sum(marks) / len(marks), 1)


def interest_overlap(student_interests: list[str], student_hobbies: list[str], career_tags: list[str]) -> float:
    """Tag overlap between student interests/hobbies and the career's interest tags, 0-100."""
    student_tags = {t.lower() for t in student_interests + student_hobbies}
    career_tag_set = {t.lower() for t in career_tags}
    if not career_tag_set:
        return 50.0
    overlap = len(student_tags & career_tag_set)
    return round(min(overlap / len(career_tag_set), 1.0) * 100, 1)


def skill_score(student_skills: dict, required_skills: list[str]) -> float:
    """Average self-rated skill level (1-5) across the career's required skills, scaled to 0-100."""
    ratings = [student_skills[s] for s in required_skills if s in student_skills]
    if not ratings:
        return 50.0
    avg = sum(ratings) / len(ratings)
    return round((avg / 5) * 100, 1)


def skill_gap(student_skills: dict, required_skills: list[str]) -> list[str]:
    """Skills required by the career where the student self-rated below the competence threshold."""
    return [
        s for s in required_skills
        if student_skills.get(s, 0) < SKILL_GAP_THRESHOLD
    ]


def career_suitability_score(student: dict, career: dict) -> dict:
    """
    Compute the full breakdown + weighted final score for one student-career pair.

    `student` expects keys: riasec_scores, academics, interests, hobbies, self_rated_skills
    `career` expects keys: riasec_tags, relevant_subjects, interest_tags, required_skills
    """
    riasec = riasec_match(student["riasec_scores"], career["riasec_tags"])
    academic = academic_fit(student["academics"], career["relevant_subjects"])
    interest = interest_overlap(student["interests"], student["hobbies"], career.get("interest_tags", []))
    skill = skill_score(student["self_rated_skills"], career["required_skills"])

    final = (
        WEIGHTS["riasec"] * riasec +
        WEIGHTS["academic"] * academic +
        WEIGHTS["interest"] * interest +
        WEIGHTS["skill"] * skill
    )

    return {
        "score": round(final, 1),
        "riasec_match": riasec,
        "academic_fit": academic,
        "interest_overlap": interest,
        "skill_score": skill,
        "skill_gaps": skill_gap(student["self_rated_skills"], career["required_skills"]),
    }


def rank_careers(student: dict, careers: list[dict], top_n: int = 5) -> list[dict]:
    """Score every career against the student profile and return the top N, sorted descending."""
    results = []
    for career in careers:
        breakdown = career_suitability_score(student, career)
        results.append({
            "career": career["name"],
            **breakdown,
            "courses": career.get("courses", []),
            "colleges": career.get("colleges", []),
            "scholarships": career.get("scholarships", []),
            "certifications": career.get("certifications", []),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]

"""
Fixed-order RIASEC quiz questions and their dimension mapping.

IMPORTANT: the order here must match the order the frontend presents
questions in, since riasec_answers[i] is matched to QUESTION_DIMENSIONS[i]
by position. If you add/reorder questions, update both together.
"""

QUESTIONS = [
    {"text": "I enjoy fixing, building, or working with tools and machines.", "dimension": "R"},
    {"text": "I like working outdoors or with my hands.", "dimension": "R"},
    {"text": "I enjoy solving puzzles, analyzing data, or doing research.", "dimension": "I"},
    {"text": "I like understanding how and why things work.", "dimension": "I"},
    {"text": "I enjoy creative writing, art, music, or design.", "dimension": "A"},
    {"text": "I like expressing myself in original or unconventional ways.", "dimension": "A"},
    {"text": "I enjoy helping, teaching, or counseling other people.", "dimension": "S"},
    {"text": "I like working in teams and communicating with others.", "dimension": "S"},
    {"text": "I enjoy leading projects, persuading people, or starting new ventures.", "dimension": "E"},
    {"text": "I like taking initiative and being in charge.", "dimension": "E"},
    {"text": "I enjoy organizing information, following procedures, and being detail-oriented.", "dimension": "C"},
    {"text": "I like structured tasks with clear rules and steps.", "dimension": "C"},
]

QUESTION_DIMENSIONS = [q["dimension"] for q in QUESTIONS]

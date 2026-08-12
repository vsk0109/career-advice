# Data Model

**Implemented as MySQL** (`backend/database/schema.sql`, applied automatically
on startup by `app/services/db.py:init_db`) — 6 tables. `students` and
`careers` use JSON columns for list/dict fields (denormalized, per the
"Notes on scale" below) rather than the fully-normalized junction tables
originally sketched here; `mentor_chat`, `roadmap_steps`, `insights`, and
`password_resets` back the stateful features (chat history, roadmap
progress tracking, cached AI insights, forgot-password).

## `students`
| Column | Type | Notes |
|---|---|---|
| student_id | INT, PK, AUTO_INCREMENT | |
| name | VARCHAR(150) | |
| email | VARCHAR(255), UNIQUE | identity for login; account created by `/auth/signup` |
| password_hash | VARCHAR(255) | bcrypt hash, never returned by any endpoint |
| interests | JSON | `["technology", "design"]` |
| hobbies | JSON | `["reading", "coding"]` |
| riasec_answers | JSON, nullable | raw 1-5 quiz answers in fixed question order; lets the Assessment page pre-fill the quiz on a retake |
| riasec_scores | JSON | `{"R": 3, "I": 8, "A": 5, "S": 2, "E": 4, "C": 6}` — computed server-side from riasec_answers |
| academics | JSON | `{"Math": 85, "Physics": 78, "English": 65}` |
| self_rated_skills | JSON | `{"communication": 4, "coding": 5}` (1-5 scale) |
| created_at | TIMESTAMP | |

`email`/`password_hash` are nullable at the DB level (existing rows predate
these columns) but required by `/auth/signup` — enforced at the API
boundary, not the schema, so the migration adding them didn't require
dropping existing dev databases. `interests`/`hobbies`/`riasec_answers`/
`riasec_scores`/`academics`/`self_rated_skills` start empty (`[]`/`{}`/`NULL`)
at signup and are filled in by `POST /profile`.

## `careers`
| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(50), PK | slug, e.g. `"data-scientist"` |
| name | VARCHAR(150) | e.g. "Data Scientist" |
| description | TEXT | 1-2 sentence overview |
| riasec_tags | JSON | `{"R": 2, "I": 9, "A": 3, "S": 2, "E": 5, "C": 6}` — ideal profile for this career |
| relevant_subjects | JSON | `["Math", "Computer Science", "Statistics"]` |
| required_skills | JSON | `["Python", "Statistics", "Communication"]` |
| interest_tags | JSON | `["technology", "problem-solving"]` |
| courses | JSON | `[{"name": "B.Sc Statistics", "level": "undergrad"}]` |
| colleges | JSON | `[{"name": "IIT Bombay", "location": "Mumbai"}]` |
| scholarships | JSON | `[{"name": "...", "eligibility": "...", "link": "..."}]` |
| certifications | JSON | `[{"name": "...", "provider": "Coursera"}]` |
| emerging | BOOLEAN | flag for "emerging career" badge in UI |

`app/data/careers_seed.json` is the source of truth for this table — it's
auto-seeded on first startup (empty table check), so editing the JSON file
and clearing the table is how you add/update careers.

## `mentor_chat`
| Column | Type | Notes |
|---|---|---|
| message_id | INT, PK, AUTO_INCREMENT | |
| student_id | INT, FK → students | `ON DELETE CASCADE` |
| sender | ENUM('student', 'ai') | |
| message | TEXT | |
| created_at | TIMESTAMP | |

Full conversation history for `/mentor/chat`; the last 6 turns are fed back
into the LLM prompt as context on each new message.

## `roadmap_steps`
| Column | Type | Notes |
|---|---|---|
| step_id | INT, PK, AUTO_INCREMENT | |
| student_id | INT, FK → students | `ON DELETE CASCADE` |
| career | VARCHAR(150) | career name the roadmap is for (not a FK — matches `careers.name`, not `careers.id`) |
| step_number | INT | 1-indexed order |
| description | TEXT | e.g. "Step 1: Strengthen your foundation in..." |
| completed | BOOLEAN | toggled via `PATCH /roadmap/steps/{step_id}` |
| created_at | TIMESTAMP | |

Populated by `POST /score/insights` for the top-matched career; each call
replaces the prior roadmap for that student+career pair rather than
accumulating duplicates.

## `insights`
| Column | Type | Notes |
|---|---|---|
| student_id | INT, PK, FK → students | one row per student — `ON DUPLICATE KEY UPDATE`, not accumulated |
| top_career | VARCHAR(150) | which career the explanations/roadmap are for |
| explanations | JSON | `{"Data Scientist": "This fits you because...", ...}` |
| emerging_trend | TEXT | |
| updated_at | TIMESTAMP | |

Caches the last `POST /score/insights` result so `GET /score/insights` can
return it without re-hitting the LLM every time the Dashboard reloads. The
roadmap portion of the response is reassembled from `roadmap_steps` for
`top_career`, not duplicated here.

## `password_resets`
| Column | Type | Notes |
|---|---|---|
| reset_id | INT, PK, AUTO_INCREMENT | |
| student_id | INT, FK → students | `ON DELETE CASCADE` |
| token_hash | VARCHAR(64), UNIQUE | sha256 of the raw token — the raw token itself is never stored, same principle as `password_hash` |
| expires_at | TIMESTAMP | 30 minutes after issuing |
| used | BOOLEAN | single-use; set `TRUE` after a successful `POST /auth/reset-password` |
| created_at | TIMESTAMP | |

Backs the forgot-password flow (`POST /auth/forgot-password` creates a row
and returns the raw token; `POST /auth/reset-password` looks it up by
hash, checks `used`/`expires_at`, and consumes it).

## Notes on scale
For a 1-week expo build, `courses`, `colleges`, `scholarships`,
`certifications` live as **nested JSON inside the `careers` row** instead of
separate tables — much faster to seed and query for ~30 careers, and still
fine to describe as "relational design, denormalized for this dataset size"
if asked.


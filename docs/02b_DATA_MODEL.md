# Data Model

## `students`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| name | text | |
| email | text | unique |
| created_at | timestamp | |

## `student_profiles`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| student_id | uuid, FK → students | |
| interests | text[] | multi-select tags, e.g. `["technology", "design"]` |
| hobbies | text[] | |
| riasec_scores | jsonb | `{"R": 3, "I": 8, "A": 5, "S": 2, "E": 4, "C": 6}` — computed from quiz |
| academics | jsonb | `{"Math": 85, "Physics": 78, "English": 65, ...}` |
| self_rated_skills | jsonb | `{"communication": 4, "coding": 5, "leadership": 2}` (1-5 scale) |
| created_at | timestamp | |

## `careers`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| name | text | e.g. "Data Scientist" |
| description | text | 1-2 sentence overview |
| riasec_tags | jsonb | `{"R": 2, "I": 9, "A": 3, "S": 2, "E": 5, "C": 6}` — ideal profile for this career |
| relevant_subjects | text[] | `["Math", "Computer Science", "Statistics"]` |
| required_skills | text[] | `["Python", "Statistics", "Communication"]` |
| emerging | boolean | flag for "emerging career" badge in UI |

## `courses`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| career_id | uuid, FK → careers | |
| name | text | e.g. "B.Tech Computer Science" |
| level | text | undergrad / postgrad / certification |

## `colleges`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| course_id | uuid, FK → courses | |
| name | text | |
| location | text | |
| notes | text | e.g. ranking, fees range — keep static/curated |

## `scholarships`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| career_id | uuid, FK → careers (nullable) | can be general or career-specific |
| name | text | |
| eligibility | text | short description |
| link | text | official info link |

## `certifications`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| career_id | uuid, FK → careers | |
| name | text | e.g. "Google Data Analytics Certificate" |
| provider | text | e.g. Coursera, edX |

## Notes on scale
For a 1-week expo build, `courses`, `colleges`, `scholarships`, `certifications` can live as **nested JSON inside the `careers` row** instead of separate tables — much faster to seed and query for ~30 careers, and still fine to describe as "relational design, denormalized for this dataset size" if asked. Use real separate tables only if the team has time to spare after Day 5.

Example denormalized `careers` row:
```json
{
  "name": "Data Scientist",
  "description": "Analyzes data to drive business and research decisions.",
  "riasec_tags": {"R": 2, "I": 9, "A": 3, "S": 2, "E": 5, "C": 6},
  "relevant_subjects": ["Math", "Computer Science", "Statistics"],
  "required_skills": ["Python", "Statistics", "Machine Learning", "Communication"],
  "courses": [{"name": "B.Sc Statistics", "level": "undergrad"}, {"name": "B.Tech CSE", "level": "undergrad"}],
  "colleges": [{"name": "IIT Bombay", "location": "Mumbai"}],
  "scholarships": [{"name": "AICTE Pragati Scholarship", "eligibility": "Girl students in technical courses"}],
  "certifications": [{"name": "Google Data Analytics Certificate", "provider": "Coursera"}],
  "emerging": true
}
```

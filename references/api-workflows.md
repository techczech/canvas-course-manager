# Canvas API Workflows

Use this only when the task requires Canvas API changes or student-view checks.

## Contents
- Workflow: Configure Course via API
- Workflow: Student View (Check Grades, Assignments, Updates)

## Workflow: Configure Course via API

Read `api_url` and `course_id` from the project's `src/_data/site.json`. The API token comes from the `CANVAS_API_TOKEN` environment variable.

```python
from canvasapi import Canvas
canvas = Canvas(api_url, token)
course = canvas.get_course(course_id)

# Set front page
page = course.get_page("page-slug")
page.edit(wiki_page={"front_page": True, "published": True})
course.update(course={"default_view": "wiki"})

# Hide all nav tabs except Home
for tab in course.get_tabs():
    if tab.id not in ("home", "settings"):
        try: tab.update(hidden=True)
        except: pass

# Make course public
course.update(course={"event": "offer", "is_public": True, "is_public_to_auth_users": True})
```

## Workflow: Student View (Check Grades, Assignments, Updates)

The Canvas API works with student tokens too. Any user can generate a personal access token.

```python
from canvasapi import Canvas
canvas = Canvas(api_url, token)

# List enrolled courses
for course in canvas.get_current_user().get_courses(enrollment_state="active"):
    print(f"{course.name} (id={course.id})")

# Check grades for a course
enrollments = canvas.get_current_user().get_enrollments(type=["StudentEnrollment"])
for e in enrollments:
    if hasattr(e, "grades"):
        print(f"{e.course_id}: current={e.grades.get('current_score')}, final={e.grades.get('final_score')}")

# List upcoming assignments
course = canvas.get_course(course_id)
for a in course.get_assignments(order_by="due_at", bucket="upcoming"):
    print(f"  {a.name} — due {a.due_at}")

# List recent announcements
for ann in course.get_discussion_topics(only_announcements=True):
    print(f"  {ann.title} ({ann.posted_at})")

# Get assignment submission status
for a in course.get_assignments():
    sub = a.get_submission("self")
    status = "submitted" if sub.workflow_state == "submitted" else "missing"
    print(f"  {a.name}: {status}, grade={getattr(sub, 'grade', 'n/a')}")
```

Student API requires `canvasapi` — install with `uv pip install canvasapi`. Token resolution same as deploy script.

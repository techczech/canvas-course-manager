---
name: canvas-course-manager
description: |
  Manage Canvas LMS courses from a local folder — or interact with Canvas as a student. Course management:
  scaffold a project, author pages in Markdown, build self-contained HTML via Eleventy, deploy via REST API.
  Student use: check grades, list assignments, view course updates, all from the CLI.

  TRIGGERS: Use when:
  - User asks to create, update, or deploy Canvas course pages
  - User wants to set up a new Canvas course project folder
  - User says "canvas course", "deploy to canvas", "canvas page", "canvas site"
  - User asks to manage Canvas course settings (nav, front page, visibility)
  - User mentions Canvas LMS in a course-management context
  - User wants to convert existing HTML course pages to the Eleventy pipeline

  - User wants to check grades, assignments, or course updates as a student
  - User asks "what's due", "check my grades", "list my courses"

  DO NOT USE when:
  - User is asking about HTML Canvas element (the drawing API) — that's a different thing
  - User wants a generic static site not destined for Canvas LMS
---

# Canvas Course Manager

Manage Canvas LMS courses entirely from a local folder. The agent scaffolds the project, writes Markdown content, builds self-contained HTML, and deploys to Canvas via API.

## Bundled Resources

| Path | Purpose |
|------|---------|
| `scripts/scaffold.sh` | Scaffold a new project from templates |
| `scripts/deploy-to-canvas.py` | Upload HTML + create Canvas pages via API (copied into each project) |
| `assets/scaffold/` | Complete Eleventy project template (CSS, layouts, partials, config) |
| `references/canvas-api-constraints.md` | Canvas API gotchas — read before any API work |

## Critical Canvas Constraints

Read [references/canvas-api-constraints.md](references/canvas-api-constraints.md) for full details. The essentials:

1. **Canvas strips `<script>` and `<style>`** from page content. Interactive pages must be uploaded as files and embedded via `<iframe src="/courses/:id/files/:file_id/download">`.
2. **Files are locked after upload.** Must call `PUT /courses/:id/usage_rights` before unlocking.
3. **Right sidebar** (calendar, To Do) cannot be hidden at course level.

## Workflow: Scaffold a New Course Project

Before scaffolding, **ask the user** for the following details (they are stored in the project's `src/_data/site.json` and are not committed to this skill repo):

1. **Canvas URL** — the base URL of their Canvas instance (e.g. `https://canvas.example.com`)
2. **Course ID** — the numeric ID from the course URL (e.g. `12345` from `.../courses/12345`)
3. **Organisation name** — displayed in the page footer (e.g. `"My University"`)
4. **Target folder** — where to create the project

Then run the scaffold script:

```bash
bash /path/to/skill/scripts/scaffold.sh <target-folder> <canvas-url> <course-id> <org-name>
```

Example:
```bash
bash scripts/scaffold.sh ~/my-canvas-course https://canvas.example.com 12345 "My University"
cd ~/my-canvas-course
npm install
uv venv .venv && source .venv/bin/activate && uv pip install canvasapi
npm run build   # verify build works
```

The scaffold creates:

```
project/
├── src/
│   ├── courses/              # Markdown source — one .md per page
│   ├── _data/site.json       # Canvas URL, course ID, org name
│   ├── _data/slides/         # Base64 slide data (generated)
│   └── _includes/
│       ├── css/              # 5 CSS modules: base, layout, tabs, content, a11y
│       ├── layouts/          # simple-video.njk, tabbed-course.njk
│       └── partials/         # header, footer, tab-js, skip-link
├── scripts/deploy-to-canvas.py
├── .eleventy.js
└── package.json
```

## Workflow: Author Pages

### Frontmatter template

```yaml
---
title: "Course Title"
layout: layouts/tabbed-course.njk   # or layouts/simple-video.njk
audience: "Open to all"
speaker: "Speaker Name"
permalink: "course-slug.html"
tabs:                                # omit for simple-video layout
  - id: overview
    label: Overview
  - id: video
    label: Video
---
```

### Tab content structure

First tab: `class="tab-content active"`. Others: `hidden` attribute.

```html
<div id="overview" class="tab-content active">
    <h2>Overview</h2>
    <p>Content...</p>
</div>
<div id="video" class="tab-content" hidden>
    <h2>Video</h2>
    <div class="embed-shell">
        <iframe class="embed-frame recording-frame" src="https://video-url"
            allowfullscreen loading="lazy" title="Title"></iframe>
    </div>
</div>
```

### CRITICAL: No blank lines between grid/flex siblings in Markdown

Markdown inserts `<p>` tags between blank-line-separated `<div>` elements, breaking CSS grid/flex. Write sibling divs on consecutive lines:

```html
<!-- WRONG -->
<div class="grid"><div class="left">...</div>

<div class="right">...</div></div>

<!-- CORRECT -->
<div class="grid"><div class="left">...</div><div class="right">...</div></div>
```

### Available CSS classes

| Class | Purpose |
|-------|---------|
| `.content-panel` | White panel (simple-video wraps content in this) |
| `.embed-shell` | Iframe container |
| `.embed-frame.recording-frame` | Video iframe (min-height: 315px) |
| `.embed-frame.slides-frame` | Slides iframe (min-height: 760px) |
| `.tip-box` | Pink-bordered callout |
| `.resource-link` | Pink button link |
| `.video-placeholder` | Video container in simple layouts |

## Workflow: Build and Deploy

```bash
npm run build                                          # build all pages
npm run dev                                            # dev server with live reload
python scripts/deploy-to-canvas.py --dry-run           # preview what would happen
python scripts/deploy-to-canvas.py                     # deploy all
python scripts/deploy-to-canvas.py --file page.html    # deploy one page
python scripts/deploy-to-canvas.py --course-id 12345   # different course
python scripts/deploy-to-canvas.py --publish           # publish immediately
```

The deploy script reads `src/_data/site.json` for defaults. Token via `CANVAS_API_TOKEN` env var or `--token` flag. Generate at: Canvas Settings > Approved Integrations > New Access Token.

The script is idempotent — safe to re-run. It replaces existing files and updates existing pages.

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

## Eleventy Layout Rules

- Each layout is **self-contained** (own `<!DOCTYPE>`, `<head>`, `<style>`, `<body>`). Eleventy layout chaining uses `{{ content | safe }}`, NOT Nunjucks `{% block %}` inheritance.
- CSS composed via `{% include "css/base.css" %}` etc. inside each layout's `<style>` tag.
- Tabbed layouts include `tab-js.njk` in `<head>` for keyboard-accessible tab navigation.
- Built-in a11y: skip link, landmark roles, ARIA tabs, reduced-motion, print stylesheet, focus-visible.

## Converting Existing HTML Pages

1. Extract metadata from `<header>`: title, audience, speaker
2. Identify layout: tabbed (has `role="tablist"`) or simple
3. Extract each `.tab-content` div as a content section
4. Extract video iframe `src` URLs
5. If `const slideImages = [...]` exists, save to `_data/slides/{slug}.json`
6. Create `.md` file with frontmatter + HTML content
7. Build and visually compare against original

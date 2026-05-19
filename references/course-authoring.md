# Canvas Course Authoring

Use this when creating or editing the static course project.

## Contents
- Bundled Resources
- Critical Canvas Constraints
- Workflow: Scaffold a New Course Project
- Workflow: Author Pages
  - Frontmatter template
  - Tab content structure
  - CRITICAL: No blank lines between grid/flex siblings in Markdown
  - Available CSS classes
- Workflow: Build and Deploy
- Eleventy Layout Rules
- Converting Existing HTML Pages

## Bundled Resources

- `scripts/scaffold.sh`: scaffold a new project from templates.
- `scripts/deploy-to-canvas.py`: upload HTML and create Canvas pages via API; copied into each project.
- `assets/scaffold/`: complete Eleventy project template with CSS, layouts, partials, config.
- `references/canvas-api-constraints.md`: Canvas API gotchas; read before any API work.

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

- `.content-panel`: white panel; `simple-video` wraps content in this.
- `.embed-shell`: iframe container.
- `.embed-frame.recording-frame`: video iframe; min-height 315px.
- `.embed-frame.slides-frame`: slides iframe; min-height 760px.
- `.tip-box`: pink-bordered callout.
- `.resource-link`: pink button link.
- `.video-placeholder`: video container in simple layouts.

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

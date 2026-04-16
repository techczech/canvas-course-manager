# Canvas Course Manager

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for managing Canvas LMS courses from a local folder. Scaffold a project, author pages in Markdown, build self-contained HTML via Eleventy, and deploy to Canvas via the REST API. Also supports student use: check grades, list assignments, view course updates — all from the CLI.

## What it does

- **Scaffolds** a complete Eleventy project wired to your Canvas instance
- **Builds** self-contained HTML pages (CSS inlined, accessible tabs, responsive) that survive Canvas's HTML sanitizer
- **Deploys** pages to Canvas via API — uploads files, sets permissions, creates/updates wiki pages with iframe embeds
- **Student mode** — check grades, upcoming assignments, announcements, and submission status

## Quick start

### Install as a Claude Code skill

Copy or symlink this folder into your Claude Code skills directory, or point to it from your `settings.json`.

### Scaffold a new course project

When you ask Claude to set up a Canvas course, the skill will prompt you for:

1. **Canvas URL** — your institution's Canvas domain (e.g. `https://canvas.example.com`)
2. **Course ID** — from the course URL (e.g. `12345` from `.../courses/12345`)
3. **Organisation name** — shown in the page footer
4. **Target folder** — where to create the project

Or run the scaffold script directly:

```bash
bash scripts/scaffold.sh ~/my-course https://canvas.example.com 12345 "My University"
cd ~/my-course
npm install
uv venv .venv && source .venv/bin/activate && uv pip install canvasapi
npm run build
```

### Author pages

Write Markdown files in `src/courses/` with YAML frontmatter. Two layouts are included:

- `layouts/tabbed-course.njk` — multi-tab pages with accessible keyboard navigation
- `layouts/simple-video.njk` — single-panel pages for video content

### Build and deploy

```bash
npm run build                           # build HTML
npm run dev                             # local dev server
python scripts/deploy-to-canvas.py --dry-run   # preview changes
python scripts/deploy-to-canvas.py              # deploy to Canvas
```

The deploy script reads your Canvas URL and course ID from `src/_data/site.json`. The API token is read from the `CANVAS_API_TOKEN` environment variable. Generate one at: Canvas Settings > Approved Integrations > New Access Token.

## Project structure (scaffolded project)

```
project/
├── src/
│   ├── courses/              # Markdown source — one .md per page
│   ├── _data/site.json       # Canvas URL, course ID, org name
│   ├── _data/slides/         # Base64 slide data (generated)
│   └── _includes/
│       ├── css/              # CSS modules: base, layout, tabs, content, a11y
│       ├── layouts/          # Nunjucks layouts
│       └── partials/         # Header, footer, tab JS, skip link
├── scripts/deploy-to-canvas.py
├── .eleventy.js
└── package.json
```

## Canvas API constraints

Canvas strips `<script>` and `<style>` tags from page content. This skill works around that by uploading self-contained HTML as course files and embedding them via `<iframe>`. See [references/canvas-api-constraints.md](references/canvas-api-constraints.md) for the full list of gotchas.

## Requirements

- [Node.js](https://nodejs.org/) (for Eleventy)
- [Python 3.10+](https://www.python.org/) with [canvasapi](https://pypi.org/project/canvasapi/)
- A Canvas LMS API token

## License

MIT

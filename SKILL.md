---
name: canvas-course-manager
description: "Manage Canvas courses."
---

# Canvas Course Manager

## First Move

- Decide whether the task is static course authoring or Canvas API work.

## Use

- Build Canvas-compatible course pages.
- Deploy static assets and update Canvas pages.
- Use API workflows only for course configuration or student-view checks.

## References

- `references/workflow.md`: choose which reference to load
- `references/course-authoring.md`: scaffold, author pages, build, deploy, or convert HTML
- `references/api-workflows.md`: configure Canvas or inspect student-view data through the API
- `references/canvas-api-constraints.md`: check sanitizer, iframe, upload, nav, slug, rate-limit, and auth constraints

## Scripts

- `scripts/scaffold.sh`: create a new course project
- `scripts/deploy-to-canvas.py`: publish built pages and assets

## Verification

- Build locally before deploy.
- Check Canvas sanitizer and iframe constraints.
- Verify changed Canvas pages in the target course.

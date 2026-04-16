# Canvas API Constraints and Gotchas

Quick reference for Canvas LMS API behaviour that is not obvious from the docs.

## HTML Sanitizer

Canvas strips from page content: `<script>`, `<style>`, `<head>`, `<body>`, `<form>`, `<input>`, `<meta>`, `<link>`.

Allowed: inline `style=""` attributes, `<iframe>` (http/https src), all semantic HTML5 elements, ARIA attributes, `data-*` attributes.

**Consequence:** Interactive pages (tabs, slide viewers) must be uploaded as files and embedded via iframe.

## Iframe Embedding

```html
<iframe src="/courses/COURSE_ID/files/FILE_ID/download"
        style="width:100%;height:2000px;border:none;"
        allowfullscreen></iframe>
```

- Use `/download` endpoint, NOT `/preview` (preview wraps in Canvas file viewer UI)
- Iframe height must be set explicitly (no auto-resize to content)

## File Upload and Permissions

1. `course.upload(filepath, parent_folder_path="folder/")` handles 3-step upload
2. Files are `locked=True` after upload
3. **Must set usage_rights before unlocking:**
   ```
   PUT /api/v1/courses/:id/usage_rights
   { "file_ids[]": [ID], "usage_rights[use_justification]": "own_copyright" }
   ```
4. Then unlock: `file.update(locked=False, visibility_level="public")`
5. Without step 3, Canvas returns: "This file must have usage_rights set before it can be published"

## Course Configuration

| Operation | API |
|-----------|-----|
| Set front page | `page.edit(wiki_page={"front_page": True, "published": True})` |
| Set home view | `course.update(course={"default_view": "wiki"})` |
| Publish course | `course.update(course={"event": "offer"})` |
| Make public | `course.update(course={"is_public": True, "is_public_to_auth_users": True})` |
| Hide nav tab | `tab.update(hidden=True)` — works for all except Home |
| Disable course summary | `PUT /courses/:id/settings {"syllabus_course_summary": false}` |

## Limitations

- **Right sidebar** (calendar, To Do, stream): cannot be hidden at course level, requires admin CSS
- **Home tab**: cannot be hidden
- **File MIME types**: Canvas may serve CSS/JS files with wrong Content-Type; inline everything instead
- **Safari iframe bug**: known Canvas issue where iframed HTML files may not render in Safari

## Page URL Slugs

Canvas auto-generates page slugs from titles. When using `course.get_page(slug)`, the slug is the kebab-case URL path segment (e.g., `my-course-page`). The deploy script derives slugs from HTML filenames.

## Rate Limiting

Canvas API uses rate limiting with `X-Rate-Limit-Remaining` headers. The canvasapi library does not auto-retry on 403 rate limit responses. For bulk operations (50+ pages), add delays between requests.

## Authentication

- Generate token: Canvas Settings > Approved Integrations > New Access Token
- Pass as: `Authorization: Bearer <token>` header
- Personal tokens don't expire until revoked
- Developer key tokens expire after 1 hour (need refresh tokens)
- **Student tokens work too** — same generation process, scoped to enrolled courses

## Student API Endpoints

| Operation | API |
|-----------|-----|
| List courses | `canvas.get_current_user().get_courses(enrollment_state="active")` |
| Check grades | `canvas.get_current_user().get_enrollments(type=["StudentEnrollment"])` → `.grades` |
| Upcoming assignments | `course.get_assignments(order_by="due_at", bucket="upcoming")` |
| Submission status | `assignment.get_submission("self")` → `.workflow_state`, `.grade` |
| Announcements | `course.get_discussion_topics(only_announcements=True)` |
| Course modules | `course.get_modules()` → `module.get_module_items()` |
| Course files | `course.get_files()` (only files visible to the student) |

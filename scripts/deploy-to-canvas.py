#!/usr/bin/env python3
"""
Deploy built HTML course pages to Canvas LMS.

For each HTML file in dist/:
1. Upload the HTML file to Canvas Course Files (under /course-pages/)
2. Set usage_rights and unlock the file
3. Create or update a Canvas page with an iframe pointing to the uploaded file

Usage:
    python scripts/deploy-to-canvas.py --dry-run
    python scripts/deploy-to-canvas.py
    python scripts/deploy-to-canvas.py --file codex-video.html
    python scripts/deploy-to-canvas.py --course-id 12345

Environment variables:
    CANVAS_API_URL    Canvas instance URL (reads from src/_data/site.json if not set)
    CANVAS_API_TOKEN  API token from Canvas Settings > Approved Integrations
    CANVAS_COURSE_ID  Course ID (reads from src/_data/site.json if not set)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from canvasapi import Canvas
    from canvasapi.exceptions import ResourceDoesNotExist
except ImportError:
    print("Error: canvasapi not installed. Run: uv pip install canvasapi")
    sys.exit(1)


PROJECT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_DIR / "dist"
SITE_JSON = PROJECT_DIR / "src" / "_data" / "site.json"
UPLOAD_FOLDER = "course-pages"
IFRAME_HEIGHT = 2000


def load_site_config():
    """Load defaults from src/_data/site.json if it exists."""
    if SITE_JSON.exists():
        with open(SITE_JSON) as f:
            return json.load(f)
    return {}


def get_config(args):
    """Resolve configuration from args, environment, or site.json."""
    site = load_site_config()

    api_url = (
        args.api_url
        or os.environ.get("CANVAS_API_URL")
        or site.get("canvasUrl", "https://canvas.instructure.com")
    )
    course_id = (
        args.course_id
        or os.environ.get("CANVAS_COURSE_ID")
        or str(site.get("courseId", ""))
    )
    api_token = args.token or os.environ.get("CANVAS_API_TOKEN")

    if not api_token:
        print("Error: No Canvas API token found.")
        print()
        print("Set it via environment variable:")
        print("  export CANVAS_API_TOKEN='your-token-here'")
        print()
        print("Or pass it as an argument:")
        print("  python scripts/deploy-to-canvas.py --token 'your-token-here'")
        print()
        print("To generate a token:")
        print(f"  1. Go to {api_url}/profile/settings")
        print("  2. Scroll to 'Approved Integrations'")
        print("  3. Click '+ New Access Token'")
        sys.exit(1)

    if not course_id:
        print("Error: No course ID found. Set CANVAS_COURSE_ID or update src/_data/site.json")
        sys.exit(1)

    return {
        "api_url": api_url.rstrip("/"),
        "api_token": api_token,
        "course_id": int(course_id),
        "org_name": site.get("orgName", ""),
    }


def get_html_files(specific_file=None):
    """Get list of HTML files to deploy from dist/."""
    if not DIST_DIR.exists():
        print(f"Error: dist/ directory not found at {DIST_DIR}")
        print("Run 'npm run build' first.")
        sys.exit(1)

    if specific_file:
        path = DIST_DIR / specific_file
        if not path.exists():
            print(f"Error: {specific_file} not found in dist/")
            sys.exit(1)
        return [path]

    files = sorted(DIST_DIR.glob("*.html"))
    if not files:
        print("Error: No HTML files found in dist/")
        print("Run 'npm run build' first.")
        sys.exit(1)

    return files


def ensure_folder(course, folder_name):
    """Get or create a folder in Canvas Course Files."""
    folders = list(course.get_folders())
    for folder in folders:
        if folder.name == folder_name:
            return folder

    root = None
    for folder in folders:
        if folder.full_name == "course files":
            root = folder
            break

    if root:
        return root.create_folder(folder_name)
    return course.create_folder(folder_name)


def find_existing_file(course, folder, filename):
    """Check if a file already exists in the given folder."""
    try:
        for f in folder.get_files():
            if f.display_name == filename:
                return f
    except Exception:
        pass
    return None


def upload_html_file(course, html_path, folder, org_name="", dry_run=False):
    """Upload an HTML file to Canvas Course Files."""
    filename = html_path.name
    size_kb = html_path.stat().st_size / 1024

    existing = find_existing_file(course, folder, filename)

    if dry_run:
        action = "UPDATE" if existing else "UPLOAD"
        print(f"  [{action}] {filename} ({size_kb:.1f} KB) -> {UPLOAD_FOLDER}/")
        return existing

    if existing:
        print(f"  Replacing existing file: {filename}")
        existing.delete()

    print(f"  Uploading {filename} ({size_kb:.1f} KB)...")
    success, response = course.upload(
        str(html_path),
        parent_folder_path=UPLOAD_FOLDER,
    )

    if not success:
        print(f"  ERROR: Upload failed for {filename}")
        print(f"  Response: {response}")
        return None

    file_id = response.get("id") if isinstance(response, dict) else response.id
    print(f"  Uploaded: file_id={file_id}")

    # Set usage rights and unlock (required on Canvas instances with usage_rights_required)
    try:
        import requests
        api_url = course._requester.original_url
        token = course._requester.access_token
        requests.put(
            f"{api_url}/api/v1/courses/{course.id}/usage_rights",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "file_ids[]": [file_id],
                "usage_rights[use_justification]": "own_copyright",
                "usage_rights[legal_copyright]": org_name or "Course Author",
            },
        )
        file_obj = course.get_file(file_id)
        file_obj.update(locked=False, hidden=False, visibility_level="public")
        print(f"  File unlocked and public")
    except Exception as e:
        print(f"  Warning: could not set file permissions: {e}")

    return response


def make_page_slug(filename):
    return filename.replace(".html", "")


def make_page_title(filename):
    slug = filename.replace(".html", "")
    return slug.replace("-", " ").title()


def make_iframe_body(course_id, file_id, iframe_height=IFRAME_HEIGHT):
    return (
        f'<p><iframe '
        f'src="/courses/{course_id}/files/{file_id}/download" '
        f'style="width:100%;height:{iframe_height}px;border:none;" '
        f'allowfullscreen="allowfullscreen" '
        f'allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media; web-share"'
        f'></iframe></p>'
    )


def create_or_update_page(course, filename, file_id, dry_run=False, publish=False, iframe_height=IFRAME_HEIGHT):
    slug = make_page_slug(filename)
    title = make_page_title(filename)

    if dry_run:
        print(f"  [CREATE/UPDATE] Page: '{title}' (/{slug})")
        return

    existing_page = None
    try:
        existing_page = course.get_page(slug)
    except ResourceDoesNotExist:
        pass

    body = make_iframe_body(course.id, file_id, iframe_height)

    if existing_page:
        print(f"  Updating page: '{title}'")
        existing_page.edit(wiki_page={"title": title, "body": body})
    else:
        print(f"  Creating page: '{title}'")
        course.create_page(wiki_page={
            "title": title,
            "body": body,
            "published": publish,
        })

    print(f"  Page ready: {slug}")


def main():
    parser = argparse.ArgumentParser(description="Deploy built HTML course pages to Canvas LMS")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--file", type=str, metavar="FILENAME", help="Deploy a single file")
    parser.add_argument("--course-id", type=str, help="Canvas course ID")
    parser.add_argument("--api-url", type=str, help="Canvas API URL")
    parser.add_argument("--token", type=str, help="Canvas API token")
    parser.add_argument("--publish", action="store_true", help="Publish pages immediately")
    parser.add_argument("--iframe-height", type=int, default=IFRAME_HEIGHT, help=f"Iframe height (default: {IFRAME_HEIGHT})")
    args = parser.parse_args()

    html_files = get_html_files(args.file)

    if args.dry_run:
        site = load_site_config()
        api_url = args.api_url or os.environ.get("CANVAS_API_URL") or site.get("canvasUrl", "?")
        course_id = args.course_id or os.environ.get("CANVAS_COURSE_ID") or site.get("courseId", "?")
        print(f"Canvas URL:  {api_url}")
        print(f"Course ID:   {course_id}")
        print(f"Files to deploy: {len(html_files)}")
        print("Mode: DRY RUN (no changes will be made)")
        print()
        for html_path in html_files:
            filename = html_path.name
            print(f"--- {filename} ---")
            upload_html_file(None, html_path, None, dry_run=True)
            create_or_update_page(None, filename, None, dry_run=True)
            print()
        print("Done! (dry run)")
        return

    config = get_config(args)
    print(f"Canvas URL:  {config['api_url']}")
    print(f"Course ID:   {config['course_id']}")
    print(f"Files to deploy: {len(html_files)}")
    print()

    canvas = Canvas(config["api_url"], config["api_token"])
    course = canvas.get_course(config["course_id"])
    print(f"Course: {course.name}")

    folder = ensure_folder(course, UPLOAD_FOLDER)
    print(f"Upload folder: {folder.full_name}")
    print()

    for html_path in html_files:
        filename = html_path.name
        print(f"--- {filename} ---")

        result = upload_html_file(course, html_path, folder, org_name=config["org_name"])
        if result is None:
            print(f"  SKIPPING page creation (upload failed)")
            continue

        file_id = result.get("id") if isinstance(result, dict) else result.id
        create_or_update_page(
            course, filename, file_id,
            publish=args.publish,
            iframe_height=args.iframe_height,
        )
        print()

    print("Done!")


if __name__ == "__main__":
    main()

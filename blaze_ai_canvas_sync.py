"""
canvas_sync.py
Blaze AI — Canvas LMS Content Exporter

Pulls course content from Canvas via the REST API and saves it as
plain text files for upload into Open WebUI's RAG knowledge base.

Dependencies:
    pip install requests

Usage:
    1. Set CANVAS_URL to your school's Canvas domain
    2. Set API_TOKEN (or use environment variable — see below)
    3. Run: python canvas_sync.py
    4. Upload generated files from canvas_export/ into Open WebUI > Workspace > Knowledge
"""

import requests
import os
import re
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

CANVAS_URL = "https://concordiashanghai.instructure.com"

# Option 1: Set token directly (do NOT commit this to GitHub)
# Option 2: Use environment variable — recommended
#   Mac/Linux: export CANVAS_TOKEN=your_token_here
#   Then set API_TOKEN = os.environ.get("CANVAS_TOKEN", "")
API_TOKEN = os.environ.get("CANVAS_TOKEN", "YOUR_API_TOKEN_HERE")

OUTPUT_DIR = "canvas_export"
ACTIVE_COURSES_ONLY = True  # Only export courses where you're enrolled as teacher

# =============================================================================
# API HELPERS
# =============================================================================

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


def api_get(endpoint, params=None):
    """GET request to Canvas API with automatic pagination."""
    url = f"{CANVAS_URL}/api/v1{endpoint}"
    all_results = []

    while url:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 401:
            print("ERROR: Authentication failed. Check your API token.")
            return []
        elif response.status_code == 403:
            print(f"  WARNING: Access denied for {endpoint} — skipping.")
            return []
        elif response.status_code != 200:
            print(f"  WARNING: Status {response.status_code} for {endpoint}")
            return []

        data = response.json()
        if isinstance(data, list):
            all_results.extend(data)
        else:
            return data

        # Follow pagination links
        links = response.headers.get("Link", "")
        url = None
        for link in links.split(","):
            if 'rel="next"' in link:
                url = link.split("<")[1].split(">")[0]
                params = None

    return all_results


def clean_html(html_text):
    """Strip HTML tags and normalize whitespace for plain text output."""
    if not html_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_filename(name):
    """Convert a string to a safe directory/file name."""
    return re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")


def write_file(directory, filename, content):
    """Write content to a text file, creating directories as needed."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"    Saved: {filepath}")


# =============================================================================
# DATA FETCHERS
# =============================================================================

def get_courses():
    """Return courses where the user has a teacher enrollment."""
    params = {"enrollment_type": "teacher", "per_page": 50}
    if ACTIVE_COURSES_ONLY:
        params["enrollment_state"] = "active"
    courses = api_get("/courses", params=params)
    print(f"\nFound {len(courses)} course(s).")
    return courses


def export_course_info(course, course_dir):
    """Export course name, code, and syllabus."""
    course_id = course["id"]
    detail = api_get(f"/courses/{course_id}", params={"include[]": "syllabus_body"})

    lines = [
        f"COURSE: {course.get('name', 'Unknown')}",
        f"Code: {course.get('course_code', 'N/A')}",
        f"Exported: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "SYLLABUS",
        "--------",
        clean_html(detail.get("syllabus_body", "No syllabus available.")),
    ]
    write_file(course_dir, "course_info.txt", "\n".join(lines))


def export_assignments(course, course_dir):
    """Export all assignments including descriptions and rubrics."""
    course_id = course["id"]
    assignments = api_get(f"/courses/{course_id}/assignments", params={"per_page": 50})

    if not assignments:
        print("    No assignments found.")
        return

    lines = [
        f"ASSIGNMENTS — {course.get('name', 'Unknown')}",
        f"Exported: {datetime.now().strftime('%Y-%m-%d')}",
        "",
    ]

    for a in assignments:
        lines.append(f"ASSIGNMENT: {a.get('name', 'Unnamed')}")
        lines.append(f"Points: {a.get('points_possible', 'N/A')}")

        due = a.get("due_at")
        if due:
            lines.append(f"Due: {due[:10]}")

        description = clean_html(a.get("description", ""))
        if description:
            lines.append(f"Description: {description}")

        # Rubric
        rubric = a.get("rubric", [])
        if rubric:
            lines.append("Rubric:")
            for criterion in rubric:
                desc = criterion.get("description", "")
                pts = criterion.get("points", "")
                lines.append(f"  - {desc} ({pts} pts)")

        lines.append("")

    write_file(course_dir, "assignments.txt", "\n".join(lines))


def export_modules(course, course_dir):
    """Export module structure and page content."""
    course_id = course["id"]
    modules = api_get(
        f"/courses/{course_id}/modules",
        params={"include[]": "items", "per_page": 50},
    )

    if not modules:
        print("    No modules found.")
        return

    lines = [
        f"MODULES & PAGES — {course.get('name', 'Unknown')}",
        f"Exported: {datetime.now().strftime('%Y-%m-%d')}",
        "",
    ]

    for module in modules:
        lines.append(f"MODULE: {module.get('name', 'Unnamed')}")
        items = module.get("items", [])

        for item in items:
            item_type = item.get("type", "")
            title = item.get("title", "Untitled")
            lines.append(f"  [{item_type}] {title}")

            # Pull full text for Page items
            if item_type == "Page":
                page_url = item.get("page_url") or item.get("url", "")
                if page_url:
                    # Extract just the slug from a full URL if needed
                    slug = page_url.rstrip("/").split("/")[-1]
                    page_data = api_get(f"/courses/{course_id}/pages/{slug}")
                    if isinstance(page_data, dict):
                        body = clean_html(page_data.get("body", ""))
                        if body:
                            lines.append(f"    Content: {body[:2000]}")

        lines.append("")

    write_file(course_dir, "modules.txt", "\n".join(lines))


# =============================================================================
# MAIN
# =============================================================================

def main():
    if API_TOKEN == "YOUR_API_TOKEN_HERE" or not API_TOKEN:
        print("ERROR: No API token set.")
        print("Set the CANVAS_TOKEN environment variable or edit API_TOKEN in the script.")
        print("Canvas: Account → Settings → New Access Token")
        return

    print("\nBlaze AI — Canvas Sync")
    print("=" * 50)
    print(f"Instance: {CANVAS_URL}")

    # Verify connection
    user = api_get("/users/self")
    if not user or isinstance(user, list):
        print("ERROR: Could not connect. Check your Canvas URL and token.")
        return
    print(f"Authenticated as: {user.get('name', 'Unknown')}")

    courses = get_courses()
    if not courses:
        print("No courses found.")
        return

    for course in courses:
        course_name = safe_filename(course.get("name", "Unknown"))
        course_dir = os.path.join(OUTPUT_DIR, course_name)

        print(f"\n{'=' * 50}")
        print(f"Processing: {course.get('name')}")
        print("=" * 50)

        export_course_info(course, course_dir)
        export_assignments(course, course_dir)
        export_modules(course, course_dir)

    print(f"\n{'=' * 50}")
    print("Done.")
    print(f"Files saved to: ./{OUTPUT_DIR}/")
    print("\nNext: Open WebUI → Workspace → Knowledge → upload the .txt files")


if __name__ == "__main__":
    main()

#!/bin/bash
# Scaffold a new Canvas course project from the skill's template.
#
# Usage: bash scaffold.sh <target-folder> <canvas-url> <course-id> <org-name>
#
# Example:
#   bash scaffold.sh ~/my-canvas-course https://canvas.example.com 12345 "My Organisation"

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCAFFOLD_DIR="$SKILL_DIR/assets/scaffold"

TARGET="${1:?Usage: scaffold.sh <target-folder> <canvas-url> <course-id> <org-name>}"
CANVAS_URL="${2:?Missing canvas-url}"
COURSE_ID="${3:?Missing course-id}"
ORG_NAME="${4:?Missing org-name}"

if [ -d "$TARGET" ] && [ "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    echo "Error: $TARGET already exists and is not empty"
    exit 1
fi

echo "Scaffolding Canvas course project..."
echo "  Target: $TARGET"
echo "  Canvas: $CANVAS_URL/courses/$COURSE_ID"
echo "  Org:    $ORG_NAME"
echo

# Copy scaffold template
mkdir -p "$TARGET"
cp -R "$SCAFFOLD_DIR/"* "$TARGET/"
cp "$SCAFFOLD_DIR/.gitignore" "$TARGET/"
cp "$SCAFFOLD_DIR/.eleventy.js" "$TARGET/"

# Copy deploy script
mkdir -p "$TARGET/scripts"
cp "$SKILL_DIR/scripts/deploy-to-canvas.py" "$TARGET/scripts/"
chmod +x "$TARGET/scripts/deploy-to-canvas.py"

# Substitute placeholders in site.json
sed -i '' \
    -e "s|CANVAS_URL|$CANVAS_URL|g" \
    -e "s|COURSE_ID|$COURSE_ID|g" \
    -e "s|ORG_NAME|$ORG_NAME|g" \
    "$TARGET/src/_data/site.json"

# Substitute placeholders in package.json
COURSE_SLUG=$(echo "$COURSE_ID" | tr '[:upper:]' '[:lower:]')
sed -i '' \
    -e "s|COURSE_SLUG|$COURSE_SLUG|g" \
    -e "s|COURSE_NAME|$ORG_NAME course $COURSE_ID|g" \
    "$TARGET/package.json"

# Create empty slides directory
mkdir -p "$TARGET/src/_data/slides"

# Create dist directory
mkdir -p "$TARGET/dist"

echo "Project scaffolded. Next steps:"
echo
echo "  cd $TARGET"
echo "  npm install"
echo "  uv venv .venv && source .venv/bin/activate && uv pip install canvasapi"
echo "  npm run build"
echo "  npm run dev    # preview at http://localhost:8080"
echo
echo "To deploy:"
echo "  export CANVAS_API_TOKEN='your-token'"
echo "  npm run deploy:dry"
echo "  npm run deploy"

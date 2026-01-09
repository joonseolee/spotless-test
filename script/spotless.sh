#!/usr/bin/env bash
set -euo pipefail

BASE_SHA=${1:-}
HEAD_SHA=${2:-HEAD}

if [[ -z "$BASE_SHA" ]]; then
  echo "Usage: $0 <base-sha> [head-sha]" >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "$REPO_ROOT" ]]; then
  echo "Not a git repository; run from within the repo." >&2
  exit 1
fi

CHANGED_FILES=$(git -C "$REPO_ROOT" diff --name-only "$BASE_SHA" "$HEAD_SHA")

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected; skipping spotlessCheck."
  exit 0
fi

SETTINGS_FILE="$REPO_ROOT/settings.gradle"
if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo "settings.gradle not found; run from repo root." >&2
  exit 1
fi

modules=()
while IFS= read -r line; do
  modules+=("$line")
done < <(grep -oE 'include\("([^"]+)"\)' "$SETTINGS_FILE" | sed -E 's/include\("([^"]+)"\)/\1/')

if [[ ${#modules[@]} -eq 0 ]]; then
  echo "No modules found in settings.gradle." >&2
  exit 1
fi

run_all=false
module_set_str=""

while IFS= read -r file; do
  case "$file" in
    build.gradle|settings.gradle|gradle.properties|gradlew|gradlew.bat) run_all=true ;;
    gradle/*) run_all=true ;;
  esac

  for module in "${modules[@]}"; do
    if [[ "$file" == "$module/"* ]]; then
      if [[ " $module_set_str " != *" $module "* ]]; then
        module_set_str+=" $module"
      fi
    fi
  done
done <<< "$CHANGED_FILES"

selected_modules=()
for module in "${modules[@]}"; do
  if $run_all || [[ " $module_set_str " == *" $module "* ]]; then
    selected_modules+=("$module")
  fi
done

if [[ ${#selected_modules[@]} -eq 0 ]]; then
  echo "No module changes detected; skipping spotlessCheck."
  exit 0
fi

tasks=()
for module in "${selected_modules[@]}"; do
  tasks+=(":${module}:spotlessCheck")
done

echo "Running spotlessCheck for modules: ${selected_modules[*]}"
chmod +x "$REPO_ROOT/gradlew"
"$REPO_ROOT/gradlew" "${tasks[@]}"

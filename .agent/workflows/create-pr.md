---
description: Generates a PR description using the create-pr skill logic
---

1. Run the `create-pr` generation script to create the PR body.
// turbo
2. run_command ".agent/workflows/scripts/generate_pr_body.py"

3. The script outputs the PR Title on the first line prefixed with `TITLE:`. Parsing this to suggest as the title.
4. Print the output to the user. Ask if they want to create the PR using the generated title.
5. If yes, run `gh pr create --title "<GENERATED_TITLE>" --body "<GENERATED_BODY>"`

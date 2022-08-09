#!/usr/bin/env bash
find . -name "*.py" -exec autopep8 -i --max-line-length 120 {} \;

# Print the changed files
git status --porcelain

# Return the number of lines changed
exit $(git status --porcelain | wc -l)

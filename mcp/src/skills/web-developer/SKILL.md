---
name: web-developer
description: Agent skill for web development tasks
allowed-tools: calculate_sum, write_file, list_files, read_file, patch_file, read_api_docs
---

Web Developer

## When developing web sites
- If the user request includes an API documentation URL, use read_api_docs tool.
- make the UI design intuitive and user-friendly.
- do not over engineer, do only what the user said.

## When updating existing scripts
- read the existing file and apply the necessary patch. Do not re-write the whole file.
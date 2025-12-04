---
name: "\U0001F41B Bug report"
about: Create a report to help us improve
title: ''
labels: bug
assignees: mahdijafaridev

---

**Describe the bug**
A clear and concise description of what the bug is.

## 📝 Steps to Reproduce
```python
from fastapi import FastAPI
from middlewares import add_essentials

app = FastAPI()
add_essentials(app)

# Minimal code that reproduces the issue
# Step 1: ...
# Step 2: ...
# Step 3: See error
```

**Expected behavior**
A clear and concise description of what you expected to happen.

## Actual Behavior
What actually happened instead.

##  Environment
**Required:**
- **OS**: [e.g., Ubuntu 22.04, macOS 14.1, Windows 11]
- **Python version**: [e.g., 3.11.5] (run `python --version`)
- **FastAPI version**: [e.g., 0.104.1] (run `pip show fastapi`)
- **fastapi-middlewares version**: [e.g., 0.1.0] (run `pip show fastapi-middlewares`)

## Error Messages
```
Paste full error messages and tracebacks here
```

## Screenshots
If applicable, add screenshots to help explain your problem.

## 📚Additional Context
Add any other context about the problem here.
- Have you tried the latest version?
- Does it happen consistently or intermittently?
- Any recent changes to your setup?

**Optional (if relevant):**
- **Web server**: [e.g., uvicorn 0.24.0, gunicorn]

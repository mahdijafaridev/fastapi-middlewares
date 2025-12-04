---
name: Feature request
about: Suggest an idea for this project
title: ''
labels: enhancement
assignees: mahdijafaridev

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear description of what you want to happen.
```python
# Example of how the feature might work
from fastapi import FastAPI
from middlewares import NewFeature

app = FastAPI()
app.add_middleware(NewFeature, option="value")

# Usage example
@app.get("/")
def root():
    return {"message": "Hello World"}
```

**Describe alternatives you've considered**
Describe any alternative solutions or features you've considered.
- Alternative 1: ...
- Alternative 2: ...

## Use Case
Describe your specific use case:
- What are you trying to accomplish?
- Why is this feature important to you?
- How would this benefit other users?

## Additional Context
Add any other context, screenshots, examples, or references about the feature request here.
- Links to similar features in other libraries
- Relevant documentation or articles
- Visual mockups (if applicable)

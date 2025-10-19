### Project Layout (Beta)

```bash
/backend
  app.py
  requirements.txt
  /templates
    base.html
    home.html
  /static
    /assets                # built bundle from /frontend/dist (vite build copies here)
  /api                     # (optional) Flask/FastAPI endpoints
  /models                  # ORM / schema definitions
  /services                # business logic / integrations
  /tests
    mock_test_only/        # temporary fixtures ONLY for tests

/frontend
  package.json
  vite.config.ts
  /src
    material.setup.ts      # imports vendored MD3 + theme
    theme.css              # Section 13.2 tokens (Light/Dark) + typography

/packages
  /material-web            # vendored MD3 submodule (pinned commit)

/docs
  rules-to-follow.md
  policy_matrix.yaml
  project_layout_beta.md
  lrbf_data_reference.md

Makefile

```

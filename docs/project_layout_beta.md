# Project Layout (Beta)

This layout represents the **Flask + Material Web (MD3)** structure for the Railyard Markets beta environment.  
It maintains full vertical integration — backend → API → frontend → MD3 components — while enforcing clean separation between code, assets, and documentation.

---

## Directory Structure

```bash
/backend
  app.py                     # Flask entry point and route definitions
  /templates                 # Jinja2 templates (HTML files using <md-*> tags)
    base.html                # Root template (loads material.setup.js + theme.css)
    home.html                # Example page or dashboard view
  /static
    /assets                  # Compiled frontend bundle (JS/CSS) from /frontend/dist
  /api                       # (Optional) Python API endpoints for live data
  /models                    # ORM/database models, schema definitions
  /services                  # Core business logic, integrations, analytics
  /tests                     # Unit and integration tests
    mock_test_only/           # Temporary mock data fixtures (never for production)

/frontend
  package.json               # Build config for Vite + TypeScript
  vite.config.ts             # Defines build output + vendored alias
  /src
    material.setup.ts        # Imports MD3 components from @lrbf/material-web
    theme.css                # Contains Section 13.2 color + typography tokens
    index.ts                 # Optional additional JS entry points

/packages
  /material-web              # Vendored Git submodule (MD3 official repo, pinned commit)

/workers
  # Asynchronous or background jobs (e.g., data sync, queue consumers)

/etl
  # Extract–Transform–Load scripts and data ingestion pipelines

/infra
  # Infrastructure as code (Dockerfiles, Terraform, CI/CD pipelines)

/docs
  rules-to-follow.md         # Authoritative engineering standards
  policy_matrix.yaml         # Executable policy rules for LLM + CI
  project_layout_beta.md     # This document (layout reference)
  lrbf_data_reference.md     # Canonical data model + ETL schema reference
````

---

## Key Relationships

| Layer          | Description                                 | Source of Truth                                             | Notes                                                        |
| -------------- | ------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| **Frontend**   | UI built with Material Web (MD3) components | `/frontend/src`                                             | Uses only `<md-*>` tags. Bundled → `/backend/static/assets/` |
| **Backend**    | Flask routes, APIs, services                | `/backend/`                                                 | Provides live data consumed by MD3 components                |
| **Packages**   | Vendored MD3 components                     | `/packages/material-web`                                    | Never imported from CDN or NPM                               |
| **Data Layer** | Schema, models, ETL definitions             | `/etl/`, `/backend/models/`, `/docs/lrbf_data_reference.md` | Unaffected by UI framework                                   |
| **Docs**       | Governance, phase plans, architecture       | `/docs/`                                                    | Every engineer must read `rules-to-follow.md` before coding  |

---

## Build → Serve Flow

1. **Build frontend assets**

   ```bash
   cd frontend && npm run build
   ```

   * Compiles MD3 components + theme.
   * Outputs to `/frontend/dist`.
   * Copies to `/backend/static/assets`.

2. **Run backend server**

   ```bash
   cd backend && flask run
   ```

   * Serves Jinja2 templates (`/templates`) which import the compiled MD3 bundle.
   * Fetches real data via Flask API routes.

3. **View in browser**

   * Open [http://localhost:5000](http://localhost:5000).
   * Verify light/dark themes, typography, and MD3 components render correctly.

---

## Developer Notes

* Always edit or add components using **vendored MD3 imports** (`@lrbf/material-web`) only.
* Never hand-code MD3 lookalikes in HTML or CSS.
* All data rendered must come from live endpoints or sanctioned fixtures in `/tests/mock_test_only`.
* Follow the [Policy Matrix](./policy_matrix.yaml) for all edit rules and vertical-integration checks.
* Reference [rules-to-follow.md](./rules-to-follow.md) before any commit or PR.

---

✅ **This layout defines the canonical structure for all future phases of the Railyard Markets platform.**

```


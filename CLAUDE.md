# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server
reflex run

# Type checking
pyright

# Initial deployment (creates admin user, syncs actions to DB)
python deploy.py

# Sync Actions enum to DB after adding new actions
python update.py
```

Package manager is **uv** (Python 3.13.12). Database is SQLite at `reflex.db` (configured in `rxconfig.py`).

## Architecture

This is a **Reflex** (Python full-stack) web application — a university dean's office management system. UI, state, and backend are all Python.

### Layer structure (per domain entity)

Every domain entity follows this four-layer pattern:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Model | `Dekanat/models.py` | SQLModel ORM class registered with `@rx.ModelRegistry.register` |
| DAO | `Dekanat/dao/<entity>.py` | Static methods accepting a `Session`, raw DB queries only |
| Service | `Dekanat/services/<entity>.py` | Opens `rx.session()`, calls DAO, commits, raises on error |
| State | `Dekanat/states/<entity>.py` | `rx.State` subclass — holds UI state, calls Service |
| View | `Dekanat/views/<entity>.py` | Pure Reflex component functions, uses State vars/events |

Pages are registered in `Dekanat/Dekanat.py` with `app.add_page(...)`.

### Auth & permissions

- `AppState` (`states/app.py`) is the base state all page states inherit from.
- Auth uses an `auth_token` cookie. `require_login` decorator (`views/auth.py`) wraps all protected pages — it renders a loading spinner while `AppState.require_auth` validates the token, then redirects to login if invalid.
- `Actions` (`actions.py`) is a `StrEnum` where each member's value is the permission code string. Every action has `title_attr` and `description_attr` attributes.
- `AppState.has_permission(action: Actions)` checks whether the authenticated worker holds that action (via direct assignment or through a role).
- Permissions must be checked at the start of every `on_load` handler and before mutating events.

### Adding a new domain entity

1. Add model to `Dekanat/models.py`.
2. Add `Actions` constants to `Dekanat/actions.py` following the `entity:operation` code format (`list`, `add`, `edit`, `delete`, `view`).
3. Add route constants to `Dekanat/routes.py`.
4. Create `Dekanat/dao/<entity>.py` with a DAO class (static methods, session-injected).
5. Create `Dekanat/services/<entity>.py` wrapping DAO calls in `with rx.session()`.
6. Create `Dekanat/states/<entity>.py` with State classes (`List*State`, `Add*State`, `Edit*State`, `View*State`) all inheriting `AppState`.
7. Create `Dekanat/views/<entity>.py` with page component functions decorated with `@require_login`.
8. Register pages in `Dekanat/Dekanat.py`.
9. Run `python update.py` to sync new Actions to the database.

### Navigation / layout

- `declared/submenu.py` defines sidebar menus as lists of `(label, icon_name, route)` tuples (`MAIN`, `BASE`, `ADMIN`, `CONTINGENT`).
- `views/tamplates/layouts.py` provides `base_layout(page_header, page_content, global_title, sidebar_menu)` — used by every protected page. `header_subpage(title, *action_buttons)` creates the in-page header with a gradient underline.
- Soft-delete pattern: all deletable models have `is_deleted: bool = False`. Services set `is_deleted = True` and call `edit_one` rather than deleting rows.

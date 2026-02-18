# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pipenv install

# Run development server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test store
python manage.py test notetaker
python manage.py test core

# Apply migrations
python manage.py migrate

# Create and apply new migrations after model changes
python manage.py makemigrations
python manage.py migrate
```

## Architecture

**Hermes** is a Django REST Framework API ("storefront" project namespace) combining two distinct domains in one codebase:

1. **E-commerce store** (`store/`) — products, collections, carts, orders, customer membership tiers (Bronze/Silver/Gold), product images and reviews. Uses DRF nested routers (`drf-nested-routers`) for endpoints like `/store/products/{id}/reviews/`.

2. **D&D session transcription platform** (`notetaker/`) — the primary feature. Hierarchical data model: `Subscription → Campaign → Session → Recording → Transcription → Summary`. Integrates AssemblyAI for audio transcription and Gemini AI for summary generation. Subscription tiers (Free, Basic, Pro) enforce per-user usage quotas tracked on the `Subscription` model.

**Supporting apps:**
- `core/` — Custom `User` model (extends `AbstractUser`, unique email), JWT auth via Djoser + SimpleJWT (30-day access / 60-day refresh tokens).
- `tags/` — Generic tagging via `ContentType` framework (`TaggedItem` with `GenericForeignKey`).
- `likes/` — Generic likes via `ContentType` framework (`LikedItem` with `GenericForeignKey`).
- `playground/` — Development/demo sandbox.

## Key Configuration

- **Settings:** `storefront/settings.py`
- **Database:** MySQL (`storefront2` on localhost); credentials in `.env`
- **Custom User model:** `AUTH_USER_MODEL = 'core.User'`
- **REST Framework:** `COERCE_DECIMAL_TO_STRING = False` — decimals stay as numbers in JSON responses
- **AssemblyAI API key** loaded from `.env` as `ASSEMBLYAI_API_KEY`
- **Auth endpoints:** `/auth/` (djoser), JWT tokens at `/auth/jwt/create/`, `/auth/jwt/refresh/`
- **Debug toolbar:** enabled in development at `/__debug__/`

## Notetaker Domain Details

The `notetaker/` app has a service layer (`services.py`) that wraps AssemblyAI SDK calls. Custom vocabulary (`CustomVocabulary` model) supplies D&D-specific word boosts (character names, locations) to improve transcription accuracy. Speaker labels are enabled by default.

`Summary` supports multiple summary types per transcription. Subscription quota fields track `audio_minutes_used` and `summaries_generated` against monthly limits.

## URL Structure

```
/admin/          — Django admin
/auth/           — Djoser auth + JWT endpoints
/store/          — E-commerce API
/notetaker/      — Transcription platform API
/playground/     — Demo views
/__debug__/      — Django debug toolbar
```

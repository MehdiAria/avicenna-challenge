# Avicenna Take-Home: Notification Lifecycle

## Running the project

**Prerequisites:** Docker and Docker Compose.

```bash
# 1. Start the app and database
docker compose up --build

# 2. In another terminal, seed the sample data
docker compose exec web .venv/bin/python manage.py load_samples

# 3. Hit the read endpoint
curl http://localhost:8000/api/notifications/

# 4. Or POST a state report manually
curl -X POST http://localhost:8000/api/notifications/ \
  -H "Content-Type: application/json" \
  -d '[{"tracking_id": "em_a1f0c97d2b3e", "status": "opened", "occurred_at": "2026-06-01T10:10:00Z", "received_at": "2026-06-01T10:10:10Z"}]'
```

The API docs are available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

## Submitting

When you're done, provide an archive of your project, make sure it includes the `.git/` folder so the commit history comes with it. Your git history is part of the submission.

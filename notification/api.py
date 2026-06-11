from ninja import Router

router = Router()


@router.get("/")
def list_notifications(request):
    """List notifications, each with a single status (see CHALLENGE.md, Task 3)."""
    return []


@router.post("/")
def update_notifications(request):
    """Ingest a lifecycle state report or a list of them (see CHALLENGE.md, Task 2).

    Report shape: see ``samples/state_reports.json``.
    """
    return []

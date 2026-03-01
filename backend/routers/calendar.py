"""Google Calendar proxy endpoints — OAuth tokens stay server-side."""
from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import (
    CalendarStatusResponse,
    CalendarEventResponse,
    CreateEventRequest,
    UpdateEventRequest,
)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


def _svc():
    from integrations.gcalendar import CalendarService
    return CalendarService()


@router.get("/status", response_model=CalendarStatusResponse)
def get_calendar_status():
    try:
        return CalendarStatusResponse(authenticated=_svc().service is not None)
    except Exception:
        return CalendarStatusResponse(authenticated=False)


@router.get("/events", response_model=List[CalendarEventResponse])
def get_events_for_date(target_date: date = Query(..., alias="date")):
    svc = _svc()
    if not svc.service:
        raise HTTPException(status_code=401, detail="Calendar not authenticated.")
    try:
        return [
            CalendarEventResponse(
                id=str(e.get("id", "")),
                title=e.get("title", "No Title"),
                description=e.get("description"),
                start_time=e.get("start_time"),
                end_time=e.get("end_time"),
                is_all_day=bool(e.get("is_all_day", False)),
                recurrence=e.get("recurrence"),
            )
            for e in svc.get_events_for_date(target_date)
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events", status_code=201)
def create_event(body: CreateEventRequest):
    svc = _svc()
    if not svc.service:
        raise HTTPException(status_code=401, detail="Calendar not authenticated.")
    try:
        ev = svc.service.events().insert(
            calendarId="primary",
            body={
                "summary": body.title,
                "description": body.description or "",
                "start": {"dateTime": body.start_time.isoformat(), "timeZone": "UTC"},
                "end":   {"dateTime": body.end_time.isoformat(),   "timeZone": "UTC"},
            },
        ).execute()
        return {"id": ev.get("id"), "title": ev.get("summary"), "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/events/{event_id}")
def update_event(event_id: str, body: UpdateEventRequest):
    svc = _svc()
    if not svc.service:
        raise HTTPException(status_code=401, detail="Calendar not authenticated.")
    try:
        ev = svc.service.events().get(calendarId="primary", eventId=event_id).execute()
        if body.title       is not None: ev["summary"]                         = body.title
        if body.description is not None: ev["description"]                     = body.description
        if body.start_time  is not None: ev["start"] = {"dateTime": body.start_time.isoformat(), "timeZone": "UTC"}
        if body.end_time    is not None: ev["end"]   = {"dateTime": body.end_time.isoformat(),   "timeZone": "UTC"}
        updated = svc.service.events().update(calendarId="primary", eventId=event_id, body=ev).execute()
        return {"id": updated.get("id"), "title": updated.get("summary"), "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
def delete_event(event_id: str):
    svc = _svc()
    if not svc.service:
        raise HTTPException(status_code=401, detail="Calendar not authenticated.")
    try:
        svc.service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {"success": True, "deleted_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

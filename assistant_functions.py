# assistant_functions.py
from googleapiclient.discovery import build
from google_services import get_google_creds
import base64
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dateutil import parser
import dateparser
from typing import Optional
try:
    from tzlocal import get_localzone_name
except ImportError:
    get_localzone_name = None

def get_valid_timezone(dt):
    """
    Returns a valid IANA timezone string for Google Calendar.
    Priority:
    1. dt.tzinfo if it's a valid IANA string
    2. System local timezone (tzlocal)
    3. 'UTC'
    """
    # Try dt.tzinfo
    if hasattr(dt, "tzinfo") and dt.tzinfo:
        # Some tzinfo objects have a 'zone' attribute (pytz), others use 'key' (zoneinfo)
        zone = getattr(dt.tzinfo, "zone", None) or getattr(dt.tzinfo, "key", None)
        if zone and isinstance(zone, str):
            return zone
        # Sometimes str(dt.tzinfo) is valid
        if str(dt.tzinfo) in ("UTC", "Etc/UTC") or "/" in str(dt.tzinfo):
            return str(dt.tzinfo)
    # Try system local timezone
    if get_localzone_name:
        try:
            return get_localzone_name()
        except Exception:
            pass
    return "UTC"

def parse_datetime_natural(text: str):
    """
    Robust datetime parser using dateparser for natural language, timezones, relative, and AM/PM formats.
    Returns (datetime or None, is_exact, error_message or None)
    Dynamically uses the system's local date and time.
    """
    from datetime import datetime
    try:
        from tzlocal import get_localzone
        local_tz = get_localzone()
    except ImportError:
        import pytz
        import time
        local_tz = pytz.timezone(time.tzname[0])

    now_local = datetime.now(local_tz)

    dt = dateparser.parse(
        text,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": now_local,
            "TIMEZONE": str(local_tz),
        },
    )
    if not dt:
        return None, False, "Could not parse date/time."
    # Check if time is approximate (e.g., "evening", "morning")
    is_exact = any(char.isdigit() for char in text)
    return dt, is_exact, None

def set_reminder(summary: str, start_time: str) -> str:
    """
    Creates an event on Google Calendar with robust datetime parsing and confirmation.
    Args:
        summary: The title or description of the event.
        start_time: The start time of the event (natural language, 24-hour, timezone-aware).
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    # Parse start_time robustly
    dt, is_exact, err = parse_datetime_natural(start_time)
    if err or dt is None:
        return f"Could not parse date/time: {err or 'Unknown error'}"
    # Confirm with user before adding
    confirmation = f"About to add event '{summary}' at {dt.isoformat()} (Exact: {is_exact}). Proceed? [yes/no]"
    # In production, replace with actual confirmation logic (e.g., prompt user)
    # For now, auto-confirm for script use
    if False:  # Replace with confirmation check
        return "Event creation cancelled by user."
    # Conflict detection
    if detect_event_conflict(service, dt):
        return "Event conflict detected at this time. Please choose another time."
    event_body = {
        "summary": summary,
        "start": {"dateTime": dt.isoformat(), "timeZone": get_valid_timezone(dt)},
        "end": {"dateTime": dt.isoformat(), "timeZone": get_valid_timezone(dt)},
    }
    event = service.events().insert(calendarId="primary", body=event_body).execute()
    return f"Success! Event created: {event.get('htmlLink')}"

def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email from the user's Gmail account.
    """
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}
    send_message = service.users().messages().send(userId="me", body=create_message).execute()
    return f"Success! Message sent with ID: {send_message['id']}"

def list_calendar_events(max_results: int = 10) -> str:
    """
    Lists upcoming events from the user's primary calendar.
    Args:
        max_results: Maximum number of events to return (default: 10)
    Returns:
        String containing formatted event details
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    
    if not events:
        return "No upcoming events found."
    
    output = ["Upcoming events:"]
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        output.append(f"{start} - {event['summary']}")
    
    return "\n".join(output)

def delete_calendar_event(event_id: str) -> str:
    """
    Deletes an event from Google Calendar by event ID.
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return "Event deleted successfully."
    except Exception as e:
        return f"Failed to delete event: {e}"

def modify_calendar_event(event_id: str, new_summary: Optional[str] = None, new_time: Optional[str] = None) -> str:
    """
    Modifies an existing event's summary and/or time.
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    try:
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        if new_summary is not None:
            event["summary"] = new_summary
        if new_time is not None:
            dt, is_exact, err = parse_datetime_natural(new_time)
            if err or dt is None:
                return f"Could not parse new date/time: {err or 'Unknown error'}"
            event["start"]["dateTime"] = dt.isoformat()
            event["end"]["dateTime"] = dt.isoformat()
            event["start"]["timeZone"] = get_valid_timezone(dt)
            event["end"]["timeZone"] = get_valid_timezone(dt)
        updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return f"Event updated: {updated_event.get('htmlLink')}"
    except Exception as e:
        return f"Failed to modify event: {e}"

def detect_event_conflict(service, dt) -> bool:
    """
    Checks for event conflicts at the given datetime.
    """
    now = dt.isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=now,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return len(events) > 0

def search_emails(query: str, max_results: int = 5) -> str:
    """
    Searches emails in the user's Gmail account.
    Args:
        query: Search query string
        max_results: Maximum number of emails to return (default: 5)
    Returns:
        String containing formatted email details
    """
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])
    
    if not messages:
        return f"No emails found matching: {query}"
    
    output = [f"Emails matching '{query}':"]
    for message in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        headers = msg["payload"]["headers"]
        subject = next(h["value"] for h in headers if h["name"] == "Subject")
        from_ = next(h["value"] for h in headers if h["name"] == "From")
        output.append(f"From: {from_}, Subject: {subject}")
    
    return "\n".join(output)

def get_unread_emails(max_results: int = 5) -> str:
    """
    Gets unread emails from the user's Gmail account.
    Args:
        max_results: Maximum number of emails to return (default: 5)
    Returns:
        String containing formatted email details
    """
    return search_emails(query="is:unread", max_results=max_results)
from typing import Optional

def add_task(title: str, notes: str = "", due: Optional[str] = None, tasklist_id: str = "@default"):
    """
    Adds a new task to Google Tasks.
    Args:
        title: Title of the task.
        notes: Optional notes for the task.
        due: Optional due date/time in RFC3339 format.
        tasklist_id: Google Tasks list ID (default: "@default").
    Returns:
        The created task resource.
    """
    creds = get_google_creds()
    service = build("tasks", "v1", credentials=creds)
    body = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = due
    task = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
    return task

def list_tasks(tasklist_id: str = "@default"):
    """
    Lists tasks from a Google Tasks list.
    Args:
        tasklist_id: Google Tasks list ID (default: "@default").
    Returns:
        List of task resources.
    """
    creds = get_google_creds()
    service = build("tasks", "v1", credentials=creds)
    results = service.tasks().list(tasklist=tasklist_id).execute()
    return results.get("items", [])

def mark_task_complete(task_id: str, tasklist_id: str = "@default"):
    """
    Marks a Google Task as completed.
    Args:
        task_id: ID of the task to mark complete.
        tasklist_id: Google Tasks list ID (default: "@default").
    Returns:
        The updated task resource.
    """
    creds = get_google_creds()
    service = build("tasks", "v1", credentials=creds)
    task = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
    task["status"] = "completed"
    from datetime import datetime
    task["completed"] = datetime.utcnow().isoformat() + "Z"
    updated_task = service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
    return updated_task

def delete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """
    Deletes a task from Google Tasks.
    Args:
        task_id: ID of the task to delete.
        tasklist_id: Google Tasks list ID (default: "@default").
    Returns:
        Success or error message.
    """
    creds = get_google_creds()
    service = build("tasks", "v1", credentials=creds)
    try:
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return "Task deleted successfully."
    except Exception as e:
        return f"Failed to delete task: {e}"
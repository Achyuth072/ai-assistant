# assistant_functions.py
# type: ignore
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
    🌍 Timezone Resolver
    
    Returns a valid IANA timezone string for Google Calendar, prioritizing:
    1. dt.tzinfo if it's a valid IANA string
    2. System local timezone (tzlocal)
    3. 'UTC' as fallback
    
    This ensures your calendar events are always in the correct timezone!
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

def parse_datetime_natural(text: str) -> tuple[Optional[datetime], bool, Optional[str]]:
    from datetime import datetime
    from typing import Optional, Tuple
    """
    Enhanced datetime parser using dateparser for natural language, timezones, relative, and AM/PM formats.
    Returns (datetime or None, is_exact, error_message or None)
    Dynamically uses the system's local date and time.
    
    Handles cases like:
    - Explicit times: "3pm tomorrow", "9:30 AM next Monday"
    - Natural language: "evening", "morning", "noon", "midnight"
    - Relative times: "in 2 hours", "next week"
    - Date expressions: "June 21st", "next Tuesday"
    """
    from datetime import datetime, timedelta
    import dateparser
    from dateparser.conf import Settings
    try:
        from tzlocal import get_localzone
        local_tz = get_localzone()
    except ImportError:
        import pytz
        import time
        local_tz = pytz.timezone(time.tzname[0])

    now_local = datetime.now(local_tz)

    # Enhanced settings for dateparser using proper Settings type
    settings = Settings({
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': now_local,
        'TIMEZONE': str(local_tz),
        'PREFER_DAY_OF_MONTH': 'first',
        'STRICT_PARSING': False,
        'REQUIRE_PARTS': ['hour']  # Ensure time component is present
    })

    # Handle special time expressions
    text_lower = text.lower()
    if "noon" in text_lower:
        text = text.replace("noon", "12:00")
    elif "midnight" in text_lower:
        text = text.replace("midnight", "00:00")
    elif any(period in text_lower for period in ["morning", "dawn"]):
        settings["PREFER_MORNING_TO_AFTERNOON"] = True

    # Parse using settings
    dt = dateparser.parse(text, settings=settings)
    
    if not dt:
        return None, False, "Could not parse date/time. Please provide a more specific time."
        
    # Validate reasonable date range (not too far in future)
    max_future = now_local + timedelta(days=365)
    if dt > max_future:
        return None, False, "Date is too far in the future (maximum 1 year ahead)."
    
    # More sophisticated exact time check
    is_exact = bool(
        any(char.isdigit() for char in text) and
        any(marker in text_lower for marker in [
            ":", "am", "pm", "noon", "midnight",
            "o'clock", "sharp", "exactly"
        ])
    )
    
    # For non-exact times, apply reasonable defaults
    if not is_exact:
        hour = dt.hour
        if "morning" in text_lower and hour < 7:
            dt = dt.replace(hour=9)  # Default morning to 9 AM
        elif "afternoon" in text_lower and hour < 12:
            dt = dt.replace(hour=14)  # Default afternoon to 2 PM
        elif "evening" in text_lower and hour < 17:
            dt = dt.replace(hour=18)  # Default evening to 6 PM
        elif "night" in text_lower and hour < 20:
            dt = dt.replace(hour=20)  # Default night to 8 PM
            
    return dt, is_exact, None

def set_reminder(summary: str, start_time: str) -> str:
    """
    📅 Calendar Event Creator
    
    Creates a new event on your Google Calendar with smart scheduling features.
    
    Args:
        summary: Event title or description - make it clear and descriptive!
        start_time: When should it start? Use natural language like:
                   - "3pm tomorrow"
                   - "next Monday at 9:30 AM"
                   - "in 2 hours"
                   - "June 21st at noon"
    
    Returns:
        A confirmation message with the event link if successful, or a helpful
        error message if something goes wrong.
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    # Parse start_time robustly
    dt, is_exact, err = parse_datetime_natural(start_time)
    if err or dt is None:
        return f"❌ Invalid date/time format: {err or 'Unknown error'}. Please try using a more specific time like '3pm tomorrow' or '9:30 AM next Monday'."
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
    ✉️ Email Sender
    
    Composes and sends an email directly from your Gmail account.
    
    When to use:
    - ✓ Sending quick messages
    - ✓ Composing formal emails
    - ✓ Reaching out to contacts
    - ✗ Not for scheduling meetings (use create_instant_meeting instead)
    
    Args:
        to: Recipient's email address
        subject: Clear, concise email subject
        body: Your message content
        
    Returns:
        Confirmation with message ID when sent successfully
    """
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}
    send_message = service.users().messages().send(userId="me", body=create_message).execute()
    return f"✉️ Message sent successfully! (ID: {send_message['id']})"

def list_calendar_events(max_results: int = 10) -> str:
    """
    📅 Calendar Viewer
    
    Shows your upcoming schedule in a beautifully formatted list.
    
    Perfect for:
    - 👀 Checking your day's agenda
    - 📊 Planning your week
    - 🗓️ Viewing upcoming appointments
    
    Args:
        max_results: How many events to show (default: 10)
                    Set higher for a broader view of your schedule
                    
    Returns:
        A nicely formatted list of your upcoming events with dates and times
        
    Note: For video meetings specifically, use join_next_meeting() instead!
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
        return "📅 No upcoming events found on your calendar."
    
    output = ["📅 Upcoming Events", "═══════════════"]
    for event in events:
        start_dt = parser.parse(event["start"].get("dateTime", event["start"].get("date")))
        formatted_time = start_dt.strftime("%I:%M %p on %B %d")  # e.g. "2:30 PM on June 21"
        output.append(f"• {formatted_time}")
        output.append(f"  └─ {event['summary']}")
    
    return "\n".join(output)

def delete_calendar_event(title_or_id: str) -> str:
    """
    🗑️ Calendar Event Remover
    
    Safely removes events from your Google Calendar with smart matching.
    
    Features:
    - 🔍 Find by title or event ID
    - 📋 Lists multiple matches for you to choose
    - ✅ Confirms successful deletion
    
    Args:
        title_or_id: Event to delete (title or ID)
                    Pro tip: Use the event ID for precise deletion!
                    
    Returns:
        Success message or list of matching events to choose from
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)

    # Try direct ID deletion first
    try:
        service.events().delete(calendarId="primary", eventId=title_or_id).execute()
        return "✅ Event deleted successfully!"
    except:
        # If ID deletion fails, search by title
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            future = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                timeMax=future,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            matching_events = [
                event for event in events_result.get("items", [])
                if event.get("summary", "").lower() == title_or_id.lower()
            ]

            if not matching_events:
                return f"❌ No events found with title: {title_or_id}"
            
            if len(matching_events) == 1:
                event = matching_events[0]
                service.events().delete(calendarId="primary", eventId=event["id"]).execute()
                return f"✅ Event '{title_or_id}' deleted successfully!"
            
            # Multiple matches found - list them for selection
            event_list = ["🔍 Multiple matching events found:", "══════════════════════════"]
            for i, event in enumerate(matching_events, 1):
                start = event["start"].get("dateTime", event["start"].get("date"))
                event_list.append(f"{i}. {start} - {event['summary']} (ID: {event['id']})")
            event_list.append("\nPlease delete using a specific event ID.")
            return "\n".join(event_list)

        except Exception as e:
            return f"Failed to search/delete events: {e}"

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
        return f"🔍 No emails found matching: {query}"
    
    output = [f"📧 Emails matching '{query}':", "═══════════════════════"]
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
    📫 Unread Email Checker
    
    Quickly see what's new in your inbox! Fetches your latest unread emails
    and presents them in an easy-to-read format.
    
    Args:
        max_results: Number of unread emails to show (default: 5)
                    Increase this to see more of your inbox
                    
    Returns:
        A clean summary of your unread emails with sender and subject info
    """
    return search_emails(query="is:unread", max_results=max_results)
from typing import Optional
def get_email_metadata(query: str, max_results=1) -> list:
    """Fetch email metadata matching query"""
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    
    results = service.users().messages().list(
        userId="me", 
        q=query, 
        maxResults=max_results
    ).execute()
    
    emails = []
    for msg in results.get("messages", []):
        msg_data = service.users().messages().get(
            userId="me", 
            id=msg["id"]
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "No Subject"),
            "sender": headers.get("From", "Unknown Sender")
        })
    
    return emails

def summarize_latest_unread_email() -> str:
    """Summarizes the most recent unread email"""
    emails = get_email_metadata("is:unread", 1)
    if not emails:
        return "📫 Your inbox is all caught up - no unread emails!"
    email = emails[0]
    summary = summarize_email_by_id(email["id"])
    return f"Latest Unread Email Summary:\nFrom: {email['sender']}\nSubject: {email['subject']}\n{summary}"

def summarize_email_by_query(query: str) -> str:
    """Summarizes the first email matching search query"""
    emails = get_email_metadata(query, 1)
    if not emails:
        return f"No emails found matching: {query}"
    email = emails[0]
    summary = summarize_email_by_id(email["id"])
    return f"Email Summary for '{query}':\nFrom: {email['sender']}\nSubject: {email['subject']}\n{summary}"
from google_services import generate_gemini_summary

def summarize_email_by_id(email_id: str) -> str:
    """
    📧 Smart Email Summarizer
    
    Let AI do the reading for you! Uses Google's Gemini Flash AI to create
    quick, intelligent summaries of your emails.
    
    Features:
    - 🤖 AI-powered understanding
    - 📝 Key points extraction
    - ⚡ Fast processing
    - 📊 Smart formatting
    
    Args:
        email_id: The unique ID of the email to summarize
        
    Returns:
        A concise, well-structured summary of the email's content
    """
    creds = get_google_creds()
    service = build("gmail", "v1", credentials=creds)
    
    try:
        msg = service.users().messages().get(userId="me", id=email_id, format="full").execute()
        payload = msg["payload"]
        
        # Extract email body
        body_content = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "body" in part and "data" in part["body"]:
                    body_content = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
                elif part["mimeType"] == "text/html" and "body" in part and "data" in part["body"]:
                    html_content = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    soup = BeautifulSoup(html_content, 'html.parser')
                    body_content = soup.get_text()
                    break
        elif "body" in payload and "data" in payload["body"]:
            body_content = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
            
        if not body_content:
            return "❌ Could not extract readable content from the email. The email may be empty or in an unsupported format."
            
        # Generate summary using Gemini Flash
        summary = generate_gemini_summary(body_content, model_name="gemini-2.5-flash")
        return f"Email Summary (ID: {email_id}):\n{summary}"
        
    except Exception as e:
        return f"Failed to summarize email {email_id}: {e}"

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

def create_instant_meeting(title: str = "Instant Meeting", start_time: Optional[str] = None) -> str:
    """
    🎥 Video Meeting Creator
    
    Instantly set up professional video conferences with Google Meet!
    
    Features:
    - ⚡ Quick instant meetings
    - 📅 Scheduled future meetings
    - 🔗 Shareable meeting links
    - 📨 Calendar integration
    
    Use when you need to:
    - 👥 Host team meetings
    - 🤝 Meet with clients
    - 🌐 Set up remote calls
    - 📞 Start quick video chats
    
    Args:
        title: Meeting name (default: "Instant Meeting")
               Make it descriptive for participants!
        start_time: When to schedule the meeting (optional)
                   - Leave empty for instant meetings
                   - Use natural language like "tomorrow 2pm"
                   
    Returns:
        Everything you need:
        - 🔗 Google Meet link
        - 📅 Calendar event details
        - ⏰ Scheduled time (if applicable)
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    
    # Parse start time if provided, otherwise use current time
    if start_time:
        dt, is_exact, err = parse_datetime_natural(start_time)
        if err or dt is None:
            return f"Could not parse start time: {err or 'Unknown error'}"
        start_dt = dt
        # Use the parsed datetime's timezone
        timezone = get_valid_timezone(dt)
    else:
        # For instant meetings, use UTC
        start_dt = datetime.datetime.now(datetime.timezone.utc)
        timezone = "UTC"
    
    # Set end time 1 hour after start
    end_dt = start_dt + datetime.timedelta(hours=1)
    
    # Check for conflicts
    if detect_event_conflict(service, start_dt):
        return "Meeting conflict detected at this time. Please choose another time."
    
    # Create event with Google Meet conferencing
    event = {
        'summary': title,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': timezone
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': timezone
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"{title}-{datetime.datetime.utcnow().timestamp()}",
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                }
            }
        }
    }
    
    try:
        event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        # Extract the meeting link
        meet_link = event.get('hangoutLink') or event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
        if not meet_link:
            return "Failed to create meeting link."
            
        return f"Meeting created successfully!\nTitle: {title}\nMeet Link: {meet_link}\nCalendar: {event.get('htmlLink')}"
    except Exception as e:
        return f"Failed to create meeting: {e}"

def join_next_meeting() -> str:
    """
    🎯 Next Meeting Finder
    
    Never miss a video call! Quickly locate your upcoming video meetings
    with their join links.
    
    Perfect for:
    - 🏃‍♂️ Quick meeting access
    - 📱 One-click joining
    - 🗓️ Video call schedule check
    - ⏰ Meeting time verification
    
    Smart Features:
    - Shows only video meetings
    - Includes instant join links
    - Lists meeting times & titles
    - Sorts by schedule
    
    Pro Tip: For regular calendar events, use list_calendar_events() instead!
    
    Returns:
        Your upcoming video meetings with:
        - ⏱️ Start times
        - 📝 Meeting titles
        - 🔗 Join links
    """
    creds = get_google_creds()
    service = build("calendar", "v3", credentials=creds)
    
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    try:
        # Get upcoming calendar events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Find all upcoming meetings with video conference links
        meetings = []
        for event in events:
            meet_link = event.get('hangoutLink') or event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
            if meet_link:
                start = event['start'].get('dateTime', event['start'].get('date'))
                meetings.append(f"• {start} - {event['summary']}\n  Join Link: {meet_link}")
        
        if meetings:
            return "Upcoming video conferences:\n" + "\n\n".join(meetings)
        return "No upcoming video conferences found in your calendar."
    except Exception as e:
        return f"Failed to check for video conferences: {e}"
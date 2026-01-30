"""Google Calendar API: auth, events, create/update/delete."""
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pathlib import Path

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser
from dateutil import tz

from config import TOKEN_FILE, CALENDAR_SCOPE


class RequestsHttpAdapter:
    """
    HTTP adapter that uses requests instead of httplib2.
    googleapiclient expects (uri, method, body, headers) -> (response, content)
    where response has .status. This avoids SSL errors (WRONG_VERSION_NUMBER, etc.)
    that occur with httplib2 in some environments.
    """

    def __init__(self, session: AuthorizedSession):
        self._session = session

    def request(
        self,
        uri: str,
        method: str = "GET",
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> tuple:
        headers = headers or {}
        if body and "Content-Length" not in headers:
            headers["Content-Length"] = str(len(body))
        resp = self._session.request(
            method=method,
            url=uri,
            data=body,
            headers=headers,
            timeout=kwargs.get("timeout", 60),
        )
        content = resp.content
        resp.status = resp.status_code  # type: ignore[attr-defined]
        return (resp, content)


class CalendarService:
    """Service for interacting with Google Calendar API."""
    
    def __init__(self, token_file: Path = TOKEN_FILE, require_auth: bool = True):
        """
        Initialize the calendar service with authentication.
        
        Args:
            token_file: Path to token file
            require_auth: If True, raises error on auth failure. If False, allows unauthenticated state.
        """
        self.token_file = token_file
        self.credentials = None
        self.service = None
        self.require_auth = require_auth
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate and build calendar service."""
        creds = None
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_file), CALENDAR_SCOPE
                )
            except Exception as e:
                print(f"Error loading credentials: {e}")
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                print("Token refreshed successfully")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                print("Token refresh failed. Re-authentication required.")
                creds = None
        if not creds or not creds.valid:
            error_msg = "Invalid or expired credentials. Please re-authenticate."
            if not self.token_file.exists():
                error_msg += "\n\nToken file not found. Run: python integrations/gcal_authentication.py"
            else:
                error_msg += "\n\nRun: python integrations/gcal_authentication.py to re-authenticate"
            
            if self.require_auth:
                raise ValueError(error_msg)
            else:
                # Return without raising error - let UI handle it
                self.credentials = None
                self.service = None
                return
        if creds.scopes and set(creds.scopes) != set(CALENDAR_SCOPE):
            print(f"Warning: Token scopes ({creds.scopes}) don't match required scopes ({CALENDAR_SCOPE})")
            print("Re-authentication required with new scopes.")
            raise ValueError(
                "Token scopes don't match. Please re-authenticate with: python integrations/gcal_authentication.py"
            )
        self.credentials = creds
        session = AuthorizedSession(creds)
        http = RequestsHttpAdapter(session)
        self.service = build('calendar', 'v3', http=http)
        
        if self.service is None:
            raise ValueError("Failed to build calendar service")
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        existing_data = {}
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as token:
                    existing_data = json.load(token)
            except Exception:
                pass
        
        # Update with current credentials
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
        }
        for key in ['universe_domain', 'account', 'expiry']:
            if key in existing_data:
                token_data[key] = existing_data[key]
        
        # Update expiry if available from credentials
        if creds.expiry:
            token_data['expiry'] = creds.expiry.isoformat()
        
        with open(self.token_file, 'w') as token:
            json.dump(token_data, token)
    
    def get_events_for_date(self, target_date: date) -> List[Dict]:
        """Fetch events for target_date; returns parsed event dicts."""
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz.tzlocal())
            end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=tz.tzlocal())
            # Set end time to 23:59:59.999999
            end_of_day = end_of_day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Convert to RFC3339 format for API
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
            if self.service is None:
                raise ValueError("Calendar service not initialized")
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,  # Expand recurring events to get today's instances
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Get unique recurring event IDs to fetch master events for recurrence info
            recurring_event_ids = set()
            for event in events:
                recurring_id = event.get('recurringEventId')
                if recurring_id:
                    recurring_event_ids.add(recurring_id)
            master_events = {}
            for recurring_id in recurring_event_ids:
                try:
                    if self.service is None:
                        raise ValueError("Calendar service not initialized")
                    master_event = self.service.events().get(
                        calendarId='primary',
                        eventId=recurring_id
                    ).execute()
                    master_events[recurring_id] = master_event
                except Exception as e:
                    print(f"Error fetching master event {recurring_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Parse and format events
            parsed_events = []
            for event in events:
                # If this is an instance of a recurring event, get recurrence from master
                recurring_id = event.get('recurringEventId')
                if recurring_id:
                    if recurring_id in master_events:
                        # Merge recurrence info from master event
                        master_event = master_events[recurring_id]
                        recurrence_list = master_event.get('recurrence', [])
                        if recurrence_list:
                            event['recurrence'] = recurrence_list
                    else:
                        try:
                            if self.service is None:
                                raise ValueError("Calendar service not initialized")
                            master_event = self.service.events().get(
                                calendarId='primary',
                                eventId=recurring_id
                            ).execute()
                            recurrence_list = master_event.get('recurrence', [])
                            if recurrence_list:
                                event['recurrence'] = recurrence_list
                                master_events[recurring_id] = master_event
                        except Exception as e:
                            print(f"Error fetching master event {recurring_id}: {e}")
                # Also check if the event itself has recurrence (for non-expanded events)
                elif 'recurrence' in event and event.get('recurrence'):
                    # Event already has recurrence, keep it
                    pass
                
                parsed_event = self._parse_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)
            parsed_events.sort(key=lambda x: x.get('start_time') or datetime.min.replace(tzinfo=tz.tzlocal()))
            
            return parsed_events
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    def get_today_events(self) -> List[Dict]:
        """
        Fetch all events for the current day.
        
        Returns:
            List of event dictionaries with parsed details.
        """
        from datetime import date
        return self.get_events_for_date(date.today())
    
    def create_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: Optional[str] = None,
        repeat_daily: bool = False
    ) -> Optional[Dict]:
        """Create a new calendar event."""
        try:
            if self.service is None:
                raise ValueError("Calendar service not initialized")
            
            # Build event body
            # Google Calendar API requires:
            # - dateTime: RFC3339 format without timezone (YYYY-MM-DDTHH:MM:SS)
            # - timeZone: IANA timezone name (e.g., "America/New_York")
            # 
            # The datetime should represent the local time in the specified timezone
            
            # Get IANA timezone name for Google Calendar API
            timezone_name = 'UTC'  # Default fallback
            
            try:
                # Use tzlocal to get proper IANA timezone name
                from tzlocal import get_localzone
                local_tz = get_localzone()
                if hasattr(local_tz, 'key'):
                    timezone_name = local_tz.key
                else:
                    # Extract from string representation
                    tz_str = str(local_tz)
                    import re
                    match = re.search(r'([A-Za-z_]+/[A-Za-z_/]+)', tz_str)
                    if match:
                        timezone_name = match.group(1)
            except Exception as e:
                print(f"Warning: Could not get timezone from tzlocal: {e}")
                import time
                import os
                tz_env = os.getenv('TZ')
                if tz_env and '/' in tz_env:
                    timezone_name = tz_env
                else:
                    # Default to a common timezone (you can change this)
                    timezone_name = 'America/New_York'  # Change to your default timezone
            
            # Validate timezone name
            if not timezone_name or '/' not in timezone_name:
                print(f"Warning: Invalid timezone '{timezone_name}', using America/New_York")
                timezone_name = 'America/New_York'

            def format_datetime_for_api(dt: datetime) -> str:
                if dt.tzinfo:
                    naive_dt = dt.replace(tzinfo=None)
                else:
                    naive_dt = dt
                return naive_dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            start_dt_str = format_datetime_for_api(start_datetime)
            end_dt_str = format_datetime_for_api(end_datetime)
            
            # Build event body with proper typing
            event_body: Dict[str, Any] = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_dt_str,
                    'timeZone': timezone_name
                },
                'end': {
                    'dateTime': end_dt_str,
                    'timeZone': timezone_name
                }
            }
            if repeat_daily:
                event_body['recurrence'] = ['RRULE:FREQ=DAILY']
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event
            
        except HttpError as error:
            print(f"An error occurred creating event: {error}")
            raise
        except Exception as e:
            print(f"Unexpected error creating event: {e}")
            raise
    
    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        repeat_daily: Optional[bool] = None
    ) -> Optional[Dict]:
        """Update an existing calendar event."""
        try:
            if self.service is None:
                raise ValueError("Calendar service not initialized")
            
            # Get existing event first
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            updated_body = {}
            
            if title is not None:
                updated_body['summary'] = title
            else:
                updated_body['summary'] = existing_event.get('summary', '')
            
            if description is not None:
                updated_body['description'] = description
            else:
                updated_body['description'] = existing_event.get('description', '')
            
            # Handle start and end times
            if start_datetime is not None or end_datetime is not None:
                # Get timezone name
                timezone_name = 'UTC'
                try:
                    from tzlocal import get_localzone
                    local_tz = get_localzone()
                    if hasattr(local_tz, 'key'):
                        timezone_name = local_tz.key
                    else:
                        import re
                        tz_str = str(local_tz)
                        match = re.search(r'([A-Za-z_]+/[A-Za-z_/]+)', tz_str)
                        if match:
                            timezone_name = match.group(1)
                except Exception:
                    timezone_name = 'America/New_York'

                def format_datetime_for_api(dt: datetime) -> str:
                    if dt.tzinfo:
                        naive_dt = dt.replace(tzinfo=None)
                    else:
                        naive_dt = dt
                    return naive_dt.strftime('%Y-%m-%dT%H:%M:%S')
                if start_datetime is not None:
                    updated_body['start'] = {
                        'dateTime': format_datetime_for_api(start_datetime),
                        'timeZone': timezone_name
                    }
                else:
                    updated_body['start'] = existing_event.get('start', {})
                if end_datetime is not None:
                    updated_body['end'] = {
                        'dateTime': format_datetime_for_api(end_datetime),
                        'timeZone': timezone_name
                    }
                else:
                    # Keep existing end time
                    updated_body['end'] = existing_event.get('end', {})
            else:
                # Keep existing times
                updated_body['start'] = existing_event.get('start', {})
                updated_body['end'] = existing_event.get('end', {})
            if repeat_daily is not None:
                if repeat_daily:
                    updated_body['recurrence'] = ['RRULE:FREQ=DAILY']
                else:
                    updated_body['recurrence'] = []
            else:
                updated_body['recurrence'] = existing_event.get('recurrence', [])
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=updated_body
            ).execute()
            
            print(f"Event updated: {updated_event.get('htmlLink')}")
            return updated_event
            
        except HttpError as error:
            print(f"An error occurred updating event: {error}")
            raise
        except Exception as e:
            print(f"Unexpected error updating event: {e}")
            raise
    
    def delete_event(self, event_id: str) -> bool:
        """Delete event (recurring: deletes only this instance)."""
        try:
            if self.service is None:
                raise ValueError("Calendar service not initialized")
            
            # Delete the event (for recurring events, this deletes only the instance)
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            print(f"Event {event_id} deleted successfully")
            return True
            
        except HttpError as error:
            print(f"An error occurred deleting event: {error}")
            raise
        except Exception as e:
            print(f"Unexpected error deleting event: {e}")
            raise
    
    def _parse_event(self, event: Dict) -> Optional[Dict]:
        """Parse raw API event into structured dict."""
        try:
            title = event.get('summary', 'No Title')
            description = event.get('description', '')
            event_id = event.get('id', '')
            
            # Parse start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            start_time = None
            end_time = None
            is_all_day = False
            
            if 'dateTime' in start:
                start_time = date_parser.parse(start['dateTime'])
                end_time = date_parser.parse(end['dateTime'])
            elif 'date' in start:
                # All-day event
                start_time = date_parser.parse(start['date'])
                end_time = date_parser.parse(end['date'])
                is_all_day = True
            recurrence_info = self._parse_recurrence(event.get('recurrence', []))
            return {
                'id': event_id,
                'title': title,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'is_all_day': is_all_day,
                'recurrence': recurrence_info,
                'raw_event': event  # Keep raw event for reference
            }
            
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None
    
    def _parse_recurrence(self, recurrence: List[str]) -> Optional[str]:
        """Parse RRULE list into human-readable string."""
        if not recurrence:
            return None
        
        # Parse the first RRULE (most common case)
        rrule = recurrence[0] if recurrence else None
        if not rrule or not rrule.startswith('RRULE:'):
            return None
        rrule = rrule[6:]
        params = {}
        for part in rrule.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key] = value
        
        freq = params.get('FREQ', '').upper()
        
        # Build human-readable string
        if freq == 'DAILY':
            interval = params.get('INTERVAL', '1')
            if interval == '1':
                return "Repeats daily"
            else:
                return f"Repeats every {interval} days"
        
        elif freq == 'WEEKLY':
            interval = params.get('INTERVAL', '1')
            byday = params.get('BYDAY', '')
            if byday:
                day_map = {
                    'MO': 'Monday', 'TU': 'Tuesday', 'WE': 'Wednesday',
                    'TH': 'Thursday', 'FR': 'Friday', 'SA': 'Saturday', 'SU': 'Sunday'
                }
                days = [day_map.get(d, d) for d in byday.split(',')]
                # Filter out None values
                days = [d for d in days if d is not None]
                if len(days) == 1:
                    day_str = days[0]
                elif len(days) == 2:
                    day_str = f"{days[0]} and {days[1]}"
                else:
                    day_str = ', '.join(days[:-1]) + f", and {days[-1]}"
                
                if interval == '1':
                    return f"Repeats every {day_str}"
                else:
                    return f"Repeats every {interval} weeks on {day_str}"
            else:
                if interval == '1':
                    return "Repeats weekly"
                else:
                    return f"Repeats every {interval} weeks"
        
        elif freq == 'MONTHLY':
            interval = params.get('INTERVAL', '1')
            bymonthday = params.get('BYMONTHDAY', '')
            
            if bymonthday:
                if interval == '1':
                    return f"Repeats monthly on the {bymonthday}"
                else:
                    return f"Repeats every {interval} months on the {bymonthday}"
            else:
                if interval == '1':
                    return "Repeats monthly"
                else:
                    return f"Repeats every {interval} months"
        
        elif freq == 'YEARLY':
            interval = params.get('INTERVAL', '1')
            if interval == '1':
                return "Repeats yearly"
            else:
                return f"Repeats every {interval} years"
        return f"Repeats ({freq.lower()})"


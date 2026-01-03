"""
Google Calendar Service
Handles authentication and fetching events from Google Calendar API.
"""
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser
from dateutil import tz

from config import TOKEN_FILE, CALENDAR_SCOPE


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
        """Authenticate and build the calendar service."""
        creds = None
        
        # Load existing token if available
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
        
        # Check if credentials are valid and have the right scope
        if not creds or not creds.valid:
            error_msg = "Invalid or expired credentials. Please re-authenticate."
            if not self.token_file.exists():
                error_msg += "\n\nToken file not found. Run: python scripts/authenticate.py"
            else:
                error_msg += "\n\nRun: python scripts/authenticate.py to re-authenticate"
            
            if self.require_auth:
                raise ValueError(error_msg)
            else:
                # Return without raising error - let UI handle it
                self.credentials = None
                self.service = None
                return
        
        # Verify scope matches (in case scope was changed)
        if creds.scopes and set(creds.scopes) != set(CALENDAR_SCOPE):
            print(f"Warning: Token scopes ({creds.scopes}) don't match required scopes ({CALENDAR_SCOPE})")
            print("Re-authentication required with new scopes.")
            raise ValueError(
                "Token scopes don't match. Please re-authenticate with: python scripts/authenticate.py"
            )
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
        
        if self.service is None:
            raise ValueError("Failed to build calendar service")
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        # Load existing token to preserve additional fields
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
        
        # Preserve additional fields from existing token
        for key in ['universe_domain', 'account', 'expiry']:
            if key in existing_data:
                token_data[key] = existing_data[key]
        
        # Update expiry if available from credentials
        if creds.expiry:
            token_data['expiry'] = creds.expiry.isoformat()
        
        with open(self.token_file, 'w') as token:
            json.dump(token_data, token)
    
    def get_today_events(self) -> List[Dict]:
        """
        Fetch all events for the current day.
        
        Returns:
            List of event dictionaries with parsed details.
        """
        try:
            # Get start and end of today in UTC
            now = datetime.now(tz.tzlocal())
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Convert to RFC3339 format for API
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
            
            # Fetch events with singleEvents=True to get today's instances
            # For recurring events, we'll check for recurringEventId and fetch master event
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
            
            # Fetch master recurring events to get recurrence patterns
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
                        # Try to fetch the master event if we don't have it
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
            
            # Sort by start time
            parsed_events.sort(key=lambda x: x.get('start_time') or datetime.min.replace(tzinfo=tz.tzlocal()))
            
            return parsed_events
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    def create_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: Optional[str] = None,
        repeat_daily: bool = False
    ) -> Optional[Dict]:
        """
        Create a new event in Google Calendar.
        
        Args:
            title: Event title
            start_datetime: Start date and time
            end_datetime: End date and time
            description: Optional event description
            repeat_daily: Whether to repeat the event daily
            
        Returns:
            Created event dictionary or None if failed
        """
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
                # Get the timezone name
                if hasattr(local_tz, 'key'):
                    # zoneinfo format (Python 3.9+)
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
                # Fallback: use common timezones based on system
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
            
            # Format datetime - use naive datetime (no timezone) since we specify timeZone separately
            # The datetime represents the local time in the specified timezone
            def format_datetime_for_api(dt: datetime) -> str:
                """Format datetime for Google Calendar API.
                Returns naive datetime string (YYYY-MM-DDTHH:MM:SS) without timezone.
                """
                # Remove timezone info - Google Calendar uses the timeZone field for that
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
            
            # Add recurrence if daily repeat is requested
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
        """
        Update an existing event in Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            title: Updated event title (if provided)
            start_datetime: Updated start date and time (if provided)
            end_datetime: Updated end date and time (if provided)
            description: Updated description (if provided)
            repeat_daily: Updated recurrence setting (if provided)
            
        Returns:
            Updated event dictionary or None if failed
        """
        try:
            if self.service is None:
                raise ValueError("Calendar service not initialized")
            
            # Get existing event first
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Build update body with only provided fields
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
                except:
                    timezone_name = 'America/New_York'  # Default fallback
                
                # Format datetime helper
                def format_datetime_for_api(dt: datetime) -> str:
                    if dt.tzinfo:
                        naive_dt = dt.replace(tzinfo=None)
                    else:
                        naive_dt = dt
                    return naive_dt.strftime('%Y-%m-%dT%H:%M:%S')
                
                # Update start time
                if start_datetime is not None:
                    updated_body['start'] = {
                        'dateTime': format_datetime_for_api(start_datetime),
                        'timeZone': timezone_name
                    }
                else:
                    # Keep existing start time
                    updated_body['start'] = existing_event.get('start', {})
                
                # Update end time
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
            
            # Handle recurrence
            if repeat_daily is not None:
                if repeat_daily:
                    updated_body['recurrence'] = ['RRULE:FREQ=DAILY']
                else:
                    # Remove recurrence if setting to False
                    updated_body['recurrence'] = []
            else:
                # Keep existing recurrence
                updated_body['recurrence'] = existing_event.get('recurrence', [])
            
            # Update the event
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
        """
        Delete an event from Google Calendar.
        For recurring events, this deletes only the specific instance.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
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
        """
        Parse a raw event from Google Calendar API into a structured format.
        
        Args:
            event: Raw event dictionary from API
            
        Returns:
            Parsed event dictionary or None if invalid
        """
        try:
            # Extract basic info
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
            
            # Parse recurrence
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
        """
        Parse RRULE recurrence pattern into human-readable format.
        
        Args:
            recurrence: List of recurrence rules (RRULE format)
            
        Returns:
            Human-readable recurrence string or None
        """
        if not recurrence:
            return None
        
        # Parse the first RRULE (most common case)
        rrule = recurrence[0] if recurrence else None
        if not rrule or not rrule.startswith('RRULE:'):
            return None
        
        rrule = rrule[6:]  # Remove 'RRULE:' prefix
        
        # Parse RRULE parameters
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
                # Map day abbreviations to full names
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
        
        # Fallback for complex patterns
        return f"Repeats ({freq.lower()})"


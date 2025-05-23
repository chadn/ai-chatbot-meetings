"""
Cal.com API service for managing calendar events and bookings.
"""
import requests
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
from config import CalComConfig
from utils.utils import convert_to_timezone, convert_local_to_utc

# Set up logger for this module
logger = logging.getLogger(__name__)

"""
Examples from docs

https://cal.com/docs/api-reference/v2/bookings/create-a-booking
curl --request POST \
  --url https://api.cal.com/v2/bookings \
  --header 'Content-Type: application/json' \
  --header 'cal-api-version: 2024-08-13' \
  --data '{
  "start": "2024-08-13T09:00:00Z",
  "attendee": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "timeZone": "America/New_York",
    "phoneNumber": "+919876543210",
    "language": "it"
  },
  "bookingFieldsResponses": {
    "customField": "customValue"
  },
  "eventTypeId": 123,
  "eventTypeSlug": "my-event-type",
  "username": "john-doe",
  "teamSlug": "john-doe",
  "organizationSlug": "acme-corp",
  "guests": [
    "guest1@example.com",
    "guest2@example.com"
  ],
  "meetingUrl": "https://example.com/meeting",
  "location": {
    "type": "address"
  },
  "metadata": {
    "key": "value"
  },
  "lengthInMinutes": 30
}'
RESPONSE:
{
  "status": "success",
  "data": {
    "id": 123,
    "uid": "booking_uid_123",
    "title": "Consultation",
    "description": "Learn how to integrate scheduling into marketplace.",
    "hosts": [
      {
        "id": 1,
        "name": "Jane Doe",
        "email": "jane100@example.com",
        "username": "jane100",
        "timeZone": "America/Los_Angeles"
      }
    ],
    "status": "accepted",
    "cancellationReason": "User requested cancellation",
    "cancelledByEmail": "canceller@example.com",
    "reschedulingReason": "User rescheduled the event",
    "rescheduledByEmail": "rescheduler@example.com",
    "rescheduledFromUid": "previous_uid_123",
    "start": "2024-08-13T15:30:00Z",
    "end": "2024-08-13T16:30:00Z",
    "duration": 60,
    "eventTypeId": 50,
    "eventType": {
      "id": 1,
      "slug": "some-event"
    },
    "meetingUrl": "https://example.com/recurring-meeting",
    "location": "https://example.com/meeting",
    "absentHost": true,
    "createdAt": "2024-08-13T15:30:00Z",
    "updatedAt": "2024-08-13T15:30:00Z",
    "metadata": {
      "key": "value"
    },
    "rating": 4,
    "icsUid": "ics_uid_123",
    "attendees": [
      {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "timeZone": "America/New_York",
        "phoneNumber": "+919876543210",
        "language": "it"
      }
    ],
    "guests": [
      "guest1@example.com",
      "guest2@example.com"
    ],
    "bookingFieldsResponses": {
      "customField": "customValue"
    }
  }
}

https://cal.com/docs/api-reference/v2/bookings/get-all-bookings

curl --request GET \
  --url https://api.cal.com/v2/bookings \
  --header 'Authorization: <authorization>' \
  --header 'cal-api-version: 2024-08-13'
  
curl -v 'https://api.cal.com/v2/bookings?attendeeEmail=dev@chadnorwood.com' \
  -H 'cal-api-version: 2024-08-13' \
  -H 'Authorization: Bearer <authorization>' \
  -H 'Content-Type: application/json' | jq .

{
  "status": "success",
  "data": [
    {
      "id": 8152896,
      "uid": "mS4ebKVyrN3wUHyXXPMFYy",
      "title": "30 Min Meeting between Chad Norwood (aww yeah) and Chad Dev",
      "description": "Interview Prep",
      "hosts": [
        {
          "id": 1546495,
          "name": "Chad Norwood",
          "email": "chad.norwood@gmail.com",
          "username": "chadn",
          "timeZone": "America/Los_Angeles"
        }
      ],
      "status": "accepted",
      "start": "2025-05-28T20:00:00.000Z",
      "end": "2025-05-28T20:30:00.000Z",
      "duration": 30,
      "eventTypeId": 2520314,
      "eventType": {
        "id": 2520314,
        "slug": "30min"
      },
      "meetingUrl": "https://app.cal.com/video/mS4ebKVyrN3wUHyXXPMFYy",
      "location": "https://app.cal.com/video/mS4ebKVyrN3wUHyXXPMFYy",
      "absentHost": false,
      "createdAt": "2025-05-28T00:12:54.525Z",
      "updatedAt": "2025-05-28T00:12:55.091Z",
      "metadata": {},
      "rating": null,
      "icsUid": "mS4ebKVyrN3wUHyXXPMFYy@Cal.com",
      "attendees": [
        {
          "name": "Chad Dev",
          "email": "dev@chadnorwood.com",
          "timeZone": "America/Los_Angeles",
          "language": "en",
          "absent": false
        }
      ],
      "bookingFieldsResponses": {
        "email": "dev@chadnorwood.com",
        "name": "Chad Dev",
        "notes": "Interview Prep"
      }
    }
  ],
  "pagination": {
    "returnedItems": 1,
    "totalItems": 1,
    "itemsPerPage": 100,
    "remainingItems": 0,
    "currentPage": 1,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  }
}




https://cal.com/docs/api-reference/v2/slots/find-out-when-is-an-event-type-ready-to-be-booked

curl -v 'https://api.cal.com/v2/slots?eventTypeId=2520314&start=2025-05-28&end=2025-05-28&timeZone=America%2FLos_Angeles&' \
  -H 'cal-api-version: 2024-09-04' \
  -H 'Authorization: Bearer <authorization>' \
  -H 'Content-Type: application/json' | jq .

RESPONSE:
{
  "status": "success",
  "data": {
    "2025-05-28": [
      {
        "start": "2025-05-28T11:00:00.000-07:00"
      },
      {
        "start": "2025-05-28T11:30:00.000-07:00"
      },
      {
        "start": "2025-05-28T12:00:00.000-07:00"
      },
      {
        "start": "2025-05-28T12:30:00.000-07:00"
      },
      {
        "start": "2025-05-28T13:00:00.000-07:00"
      },
      {
        "start": "2025-05-28T13:30:00.000-07:00"
      },
      {
        "start": "2025-05-28T14:00:00.000-07:00"
      },
      {
        "start": "2025-05-28T14:30:00.000-07:00"
      }
    ]
  }
}

curl -v 'https://api.cal.com/v2/event-types?username=chadn' \
  -H 'cal-api-version: 2024-06-14' \
  -H 'Authorization: Bearer <authorization>' \
  -H 'Content-Type: application/json' | jq .
...
      "id": 2520314,
      "ownerId": 1546495,
      "lengthInMinutes": 30,
      "title": "30 Min Meeting",
      "slug": "30min",

"""
class CalComService:
    """Service for interacting with Cal.com API for calendar management."""
    
    def __init__(self, config: CalComConfig) -> None:
        """
        Initialize CalCom service with configuration.
        
        Args:
            config: CalCom configuration object
        """
        self.config = config
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.event_type_id = config.event_type_id
        self.timezone = config.timezone
        
        logger.info(f"CalComService initialized with timezone: {self.timezone}")
        
        # Set up headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    
    def _validate_api_response(self, data: dict, operation: str) -> dict:
        """Validate Cal.com API response format and extract data."""
        if "status" in data and data["status"] != "success":
            logger.error(f"{operation} failed: {json.dumps(data, indent=2)}")
            raise ValueError(f"{operation} failed. Response status: {data['status']}")
        
        if "data" not in data:
            logger.error(f"{operation} unexpected response: {json.dumps(data, indent=2)}")
            raise ValueError(f"Unexpected data structure in {operation} response")
        
        return data["data"]
    
    def _format_timezone_info(self) -> str:
        """Format timezone information for display."""
        return f" (in {self.timezone})" if self.timezone else ""
    
    def check_availability(self, start_date: str, end_date: str, event_type_id: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check availability slots for a specific event type and date range.
        According to: https://cal.com/docs/api-reference/v2/slots/find-out-when-is-an-event-type-ready-to-be-booked
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            event_type_id: ID of the event type
            
        Returns:
            Dictionary mapping dates to lists of available time slots
        """
        url = f"{self.base_url}/slots"
        headers = self.headers.copy()
        headers["cal-api-version"] = self.config.cal_api_version_slots
        params = {
            "eventTypeId": event_type_id or self.event_type_id,
            "start": start_date,
            "end": end_date,
            "timeZone": self.timezone
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Handle different API response formats
        if "data" in data:
            return data["data"]
        elif "slots" in data:
            # Convert legacy format to expected format
            result = {}
            for slot in data["slots"]:
                date_str = (slot.get("time") or slot.get("start", "")).split("T")[0]
                if not date_str:
                    continue
                
                if date_str not in result:
                    result[date_str] = []
                
                # Normalize to use "start" field
                if "time" in slot and "start" not in slot:
                    slot["start"] = slot["time"]
                
                result[date_str].append(slot)
            return result
        else:
            return {}

    def get_scheduled_bookings(self, email: str) -> List[Dict[str, Any]]:
        """
        Retrieve scheduled events for a user based on email.
        According to: https://cal.com/docs/api-reference/v2/bookings/get-all-bookings
        
        Args:
            email: Email address of the user
            
        Returns:
            List of scheduled events
        """
        url = f"{self.base_url}/bookings"
        headers = self.headers.copy()
        headers["cal-api-version"] = self.config.cal_api_version_bookings
        params = {
            "timeZone": self.timezone,
            "attendeeEmail": email,
            "sortStart": "asc"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        return self._validate_api_response(data, "get_scheduled_bookings")

    def create_booking(self, 
                     start_time: str,
                     name: str, 
                     email: str, 
                     reason: str = "",
                     event_type_id: int = None) -> Dict[str, Any]:
        """
        Create a new booking in the calendar.
        According to: https://cal.com/docs/api-reference/v2/bookings/create-a-booking
        
        Args:
            start_time: Start time in ISO format (must end with Z for UTC)
            name: Name of the attendee
            email: Email of the attendee
            reason: Reason for the meeting (optional)
            event_type_id: ID of the event type
            
        Returns:
            Dictionary with booking details
        """
        url = f"{self.base_url}/bookings"
        headers = self.headers.copy()
        headers["cal-api-version"] = self.config.cal_api_version_bookings

        payload = {
            "start": start_time,
            "eventTypeId": event_type_id or self.event_type_id,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": self.timezone,
                "language": self.config.default_language
            },
            "metadata": {}
        }
        
        # Add reason/notes if provided
        if reason:
            payload["bookingFieldsResponses"] = {"notes": reason}
        else:
            # API seems to require notes field
            payload["bookingFieldsResponses"] = {"notes": "No specific reason provided"}
        response = requests.post(url, headers=headers, json=payload)
        
        try:
            response.raise_for_status()
            data = response.json()
            return self._validate_api_response(data, "create_booking")
        except requests.HTTPError as e:
            error_message = f"HTTP error: {e}"
            try:
                error_json = response.json()
                if "message" in error_json:
                    error_message = f"{error_message}, API error: {error_json['message']}"
                elif "error" in error_json and "message" in error_json["error"]:
                    error_message = f"{error_message}, API error: {error_json['error']['message']}"
            except Exception:
                pass
            raise requests.HTTPError(error_message, response=response)
        except Exception as e:
            logger.error(f"Unexpected error in create_booking: {e}")
            raise ValueError(f"Failed to create booking: {str(e)}")

    # Formatting methods for user-friendly responses
    def get_formatted_availability(self, start_date: str, end_date: str = None) -> str:
        """
        Get formatted availability with timezone conversion for user display.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)
            
        Returns:
            Formatted string describing available time slots
        """
        # If end_date is not provided, use start_date
        if not end_date:
            end_date = start_date
            
        availability = self.check_availability(start_date, end_date)
        if not availability:
            return f"No availability found for {start_date} to {end_date}"
        
        result = f"Available time slots for {start_date}"
        if start_date != end_date:
            result += f" to {end_date}"
        result += f" (timezone: {self.timezone}):\n"
        
        # availability is a dict mapping dates to lists of slots
        for date_str in sorted(availability.keys()):
            date_obj = datetime.fromisoformat(date_str)
            day_name = date_obj.strftime('%A')
            result += f"\n{date_str} ({day_name}):\n"
            
            slots = availability[date_str]
            for slot in slots:
                start_time = convert_to_timezone(slot['start'], self.timezone)
                result += f"- {start_time.strftime('%H:%M')}\n"
        
        return result

    def _format_booking(self, booking: dict, show_header: bool = False) -> str:
        """Format a single booking object for display."""
        start_time_str = booking.get('start')
        end_time_str = booking.get('end')
        if not start_time_str:
            return "[Invalid booking: missing start time]"
        start = convert_to_timezone(start_time_str, self.timezone)
        end_time_display = ""
        if end_time_str:
            end = convert_to_timezone(end_time_str, self.timezone)
            end_time_display = f" to {end.strftime('%H:%M')}"
        title = booking.get('title', 'Meeting')
        description = booking.get('description', booking.get('notes', 'No description provided'))
        # Attendee extraction: prefer first attendee if present
        attendee_name = attendee_email = "Unknown"
        attendees = booking.get('attendees')
        if attendees and isinstance(attendees, list) and len(attendees) > 0:
            attendee = attendees[0]
            attendee_name = attendee.get('name', 'Unknown')
            attendee_email = attendee.get('email', 'Unknown')
        else:
            attendee_name = booking.get('attendeeName', 'Unknown')
            attendee_email = booking.get('attendeeEmail', 'Unknown')
        timezone_info = f" (in {self.timezone})" if self.timezone else ""
        lines = []
        if show_header:
            lines.append("Meeting successfully booked!")
        lines.extend([
            f"Title: {title}",
            f"Description: {description}",
            f"Date: {start.strftime('%Y-%m-%d %A')}",
            f"Time: {start.strftime('%H:%M')}{end_time_display}{timezone_info}",
            f"Attendee: {attendee_name} ({attendee_email})",
            f"Status: {booking.get('status', 'Unknown')}"
        ])
        return "\n".join(lines)

    def get_formatted_booking_confirmation(self, booking_data: dict) -> str:
        """Format booking confirmation message using the general formatter."""
        return self._format_booking(booking_data, show_header=True)

    def get_formatted_scheduled_bookings(self, email: str) -> str:
        """Get formatted list of scheduled events using the general formatter."""
        events = self.get_scheduled_bookings(email)
        if not events:
            return f"No scheduled events found for {email}."
        formatted_events = []
        for event in events:
            formatted_events.append(self._format_booking(event))
        timezone_info = f" (in {self.timezone})" if self.timezone else ""
        return f"Scheduled events for {email}{timezone_info}:\n" + "\n\n".join(formatted_events)

    def create_booking_with_confirmation(self, 
                                       start_time: str,
                                       name: str, 
                                       email: str, 
                                       reason: str = "",
                                       event_type_id: int = None) -> str:
        """
        Create a booking and return a formatted confirmation message.
        
        Args:
            start_time: Start time in ISO format 
            name: Name of the attendee
            email: Email of the attendee
            reason: Reason for the meeting (optional)
            event_type_id: ID of the event type (optional)
            
        Returns:
            Formatted confirmation message
        """
        # Convert to UTC for booking
        start_utc_str = convert_local_to_utc(start_time, self.timezone)
        
        # Book the meeting
        booking = self.create_booking(
            start_time=start_utc_str,
            name=name,
            email=email,
            reason=reason,
            event_type_id=event_type_id
        )
        
        # Return formatted confirmation
        return self.get_formatted_booking_confirmation(booking)

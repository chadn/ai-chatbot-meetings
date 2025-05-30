"""
Tests for the CalComService class.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.calcom_service import CalComService
from src.config.settings import CalComConfig


@pytest.fixture
def calcom_config():
    """Fixture for CalComConfig with test values."""
    return CalComConfig(
        api_key="test_api_key",
        base_url="https://api.cal.com/v2",
        timezone="UTC",
        cal_api_version_slots="2024-09-04",
        cal_api_version_bookings="2024-08-13",
        default_language="en"
    )


@pytest.fixture
def calcom_service(calcom_config):
    """Fixture for CalComService with test configuration."""
    return CalComService(calcom_config)


def test_check_availability_for_tomorrow(calcom_service):
    """Test the check_availability method for tomorrow's date."""
    # Create date for tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Mock response data in the new format with date keys
    mock_data = {
        tomorrow: [
            {"start": f"{tomorrow}T09:00:00Z"},
            {"start": f"{tomorrow}T10:00:00Z"},
            {"start": f"{tomorrow}T11:00:00Z"},
            {"start": f"{tomorrow}T14:00:00Z"},
            {"start": f"{tomorrow}T15:00:00Z"},
        ]
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": mock_data}
    mock_response.raise_for_status = MagicMock()
    
    # Patch the requests.get method
    with patch("requests.get", return_value=mock_response):
        # Call the method with tomorrow's date (updated API)
        result = calcom_service.check_availability(start_date=tomorrow, end_date=tomorrow, event_type_id=123)
        
        # Verify results
        assert tomorrow in result
        assert len(result[tomorrow]) == 5
        assert all(slot["start"].startswith(tomorrow) for slot in result[tomorrow])


def test_check_availability_no_slots(calcom_service):
    """Test the check_availability method when no slots are available."""
    # Create date for tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Mock empty response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {}}
    mock_response.raise_for_status = MagicMock()
    
    # Patch the requests.get method
    with patch("requests.get", return_value=mock_response):
        # Call the method with tomorrow's date (updated API)
        result = calcom_service.check_availability(start_date=tomorrow, end_date=tomorrow, event_type_id=123)
        
        # Verify results
        assert result == {}


def test_check_availability_request_params(calcom_service):
    """Test that check_availability method sends correct request parameters."""
    # Create date for tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    event_type_id = 123
    
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {}}
    mock_response.raise_for_status = MagicMock()
    
    # Patch the requests.get method and capture the call
    with patch("requests.get", return_value=mock_response) as mock_get:
        # Call the method (updated API)
        calcom_service.check_availability(start_date=tomorrow, end_date=tomorrow, event_type_id=event_type_id)
        
        # Verify request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        
        # Check URL
        assert args[0] == "https://api.cal.com/v2/slots"
        
        # Check headers
        assert kwargs["headers"]["Authorization"] == "Bearer test_api_key"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["headers"]["cal-api-version"] == "2024-09-04"
        
        # Check query parameters
        assert kwargs["params"]["eventTypeId"] == event_type_id
        assert kwargs["params"]["start"] == tomorrow
        assert kwargs["params"]["end"] == tomorrow
        assert kwargs["params"]["timeZone"] == "UTC"


def test_get_scheduled_bookings(calcom_service):
    """Test the get_scheduled_bookings method."""
    test_email = "test@example.com"
    
    # Mock response data
    mock_events = [
        {
            "id": 123,
            "title": "Test Meeting",
            "start": "2024-01-01T10:00:00Z",
            "end": "2024-01-01T10:30:00Z",
            "attendees": [{"email": test_email, "name": "Test User"}]
        }
    ]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success", "data": mock_events}
    mock_response.raise_for_status = MagicMock()
    
    # Patch the requests.get method
    with patch("requests.get", return_value=mock_response):
        result = calcom_service.get_scheduled_bookings(test_email)
        
        # Verify results
        assert result == mock_events
        assert len(result) == 1
        assert result[0]["title"] == "Test Meeting"


def test_create_booking(calcom_service):
    """Test the create_booking method."""
    # Mock response data
    mock_booking = {
        "id": 456,
        "title": "Test Booking",
        "start": "2024-01-01T14:00:00Z",
        "end": "2024-01-01T14:30:00Z"
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success", "data": mock_booking}
    mock_response.raise_for_status = MagicMock()
    
    # Patch the requests.post method
    with patch("requests.post", return_value=mock_response):
        result = calcom_service.create_booking(
            start_time="2024-01-01T14:00:00Z",
            name="Test User",
            email="test@example.com",
            reason="Test meeting",
            event_type_id=123
        )
        
        # Verify results
        assert result == mock_booking
        assert result["id"] == 456 
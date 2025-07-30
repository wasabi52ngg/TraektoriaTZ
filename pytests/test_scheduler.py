import pytest
from unittest.mock import Mock, patch
from scheduler import Scheduler
from copy import deepcopy
from datetime import datetime

"""
Запуск: pytest -v
"""


@pytest.fixture
def mock_data():
    return {
        "days": [
            {"id": 1, "date": "2025-02-15", "start": "09:00", "end": "21:00"},
            {"id": 2, "date": "2025-02-16", "start": "08:00", "end": "22:00"},
        ],
        "timeslots": [
            {"id": 1, "day_id": 1, "start": "17:30", "end": "20:00"},
            {"id": 2, "day_id": 1, "start": "09:00", "end": "12:00"},
            {"id": 3, "day_id": 2, "start": "14:30", "end": "18:00"},
            {"id": 4, "day_id": 2, "start": "09:30", "end": "11:00"},
        ]
    }


@pytest.fixture
def scheduler(mock_data):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = deepcopy(mock_data)
        mock_get.return_value = mock_response
        yield Scheduler("http://test-url")


@pytest.fixture
def scheduler_empty_data():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"days": [], "timeslots": []}
        mock_get.return_value = mock_response
        yield Scheduler("http://test-url")


def test_init_successful(scheduler, mock_data):
    assert scheduler.days == mock_data["days"]
    assert scheduler.slots == mock_data["timeslots"]
    assert scheduler._url == "http://test-url"


def test_init_invalid_data_format():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"days": {}, "timeslots": []}
        mock_get.return_value = mock_response
        with pytest.raises(ValueError, match="Invalid data format"):
            Scheduler("http://test-url")


def test_init_request_failure():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        with pytest.raises(ValueError, match="Failed to get data"):
            Scheduler("http://test-url")


def test_refresh_data_successful(scheduler, mock_data):
    with patch('requests.get') as mock_get:
        updated_data = {
            "days": [{"id": 3, "date": "2025-02-17", "start": "10:00", "end": "15:00"}],
            "timeslots": []
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = updated_data
        mock_get.return_value = mock_response
        scheduler.refresh_data()
        assert scheduler.days == updated_data["days"]
        assert scheduler.slots == updated_data["timeslots"]


def test_refresh_data_failure(scheduler):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        with pytest.raises(RuntimeError, match="Failed to refresh data"):
            scheduler.refresh_data()


def test_check_day_exist_found(scheduler):
    day = scheduler.check_day_exist("2025-02-15")
    assert day == {"id": 1, "date": "2025-02-15", "start": "09:00", "end": "21:00"}


def test_check_day_exist_not_found(scheduler):
    assert scheduler.check_day_exist("2025-02-17") is None


def test_check_day_exist_empty_days(scheduler_empty_data):
    assert scheduler_empty_data.check_day_exist("2025-02-15") is None


def test_get_busy_slots_valid_date(scheduler):
    assert scheduler.get_busy_slots("2025-02-15") == [("09:00", "12:00"), ("17:30", "20:00")]
    assert scheduler.get_busy_slots("2025-02-16") == [("09:30", "11:00"), ("14:30", "18:00")]


def test_get_busy_slots_invalid_date(scheduler):
    assert scheduler.get_busy_slots("2025-02-17") == []


def test_get_busy_slots_no_slots(scheduler):
    scheduler._slots = []
    assert scheduler.get_busy_slots("2025-02-15") == []


def test_get_busy_slots_empty_data(scheduler_empty_data):
    assert scheduler_empty_data.get_busy_slots("2025-02-15") == []


def test_get_free_slots_valid_date(scheduler):
    assert scheduler.get_free_slots("2025-02-15") == [("12:00", "17:30"), ("20:00", "21:00")]
    assert scheduler.get_free_slots("2025-02-16") == [("08:00", "09:30"), ("11:00", "14:30"), ("18:00", "22:00")]


def test_get_free_slots_no_busy_slots():
    mock_data = {
        "days": [{"id": 1, "date": "2025-02-15", "start": "09:00", "end": "21:00"}],
        "timeslots": []
    }
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        scheduler = Scheduler("http://test-url")
        assert scheduler.get_free_slots("2025-02-15") == [("09:00", "21:00")]


def test_get_free_slots_invalid_date(scheduler):
    assert scheduler.get_free_slots("2025-02-17") == []


def test_get_free_slots_empty_data(scheduler_empty_data):
    assert scheduler_empty_data.get_free_slots("2025-02-15") == []


def test_get_free_slots_multiple_busy_slots():
    mock_data = {
        "days": [{"id": 1, "date": "2025-02-15", "start": "09:00", "end": "21:00"}],
        "timeslots": [
            {"id": 1, "day_id": 1, "start": "10:00", "end": "11:00"},
            {"id": 2, "day_id": 1, "start": "12:00", "end": "13:00"},
            {"id": 3, "day_id": 1, "start": "14:00", "end": "15:00"}
        ]
    }
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        scheduler = Scheduler("http://test-url")
        assert scheduler.get_free_slots("2025-02-15") == [
            ("09:00", "10:00"),
            ("11:00", "12:00"),
            ("13:00", "14:00"),
            ("15:00", "21:00")
        ]


def test_is_available_within_free_slot(scheduler):
    assert scheduler.is_available("2025-02-15", "12:30", "13:00") is True


def test_is_available_within_busy_slot(scheduler):
    assert scheduler.is_available("2025-02-15", "17:30", "18:00") is False


def test_is_available_outside_day_hours(scheduler):
    assert scheduler.is_available("2025-02-15", "08:00", "08:30") is False
    assert scheduler.is_available("2025-02-15", "21:00", "21:30") is False


def test_is_available_invalid_date(scheduler):
    assert scheduler.is_available("2025-02-17", "10:00", "10:30") is False


def test_is_available_invalid_time_order(scheduler):
    assert scheduler.is_available("2025-02-15", "13:00", "12:30") is False


def test_is_available_overlapping_busy_slot(scheduler):
    assert scheduler.is_available("2025-02-15", "11:30", "12:30") is False


def test_is_available_exact_slot_boundaries(scheduler):
    assert scheduler.is_available("2025-02-15", "12:00", "17:30") is True
    assert scheduler.is_available("2025-02-15", "20:00", "21:00") is True


def test_find_slot_for_duration_60_minutes(scheduler):
    assert scheduler.find_slot_for_duration(60) == ("2025-02-15", "12:00", "13:00")


def test_find_slot_for_duration_90_minutes(scheduler):
    assert scheduler.find_slot_for_duration(90) == ("2025-02-15", "12:00", "13:30")


def test_find_slot_for_duration_too_long(scheduler):
    assert scheduler.find_slot_for_duration(600) is None


def test_find_slot_for_duration_invalid_duration(scheduler):
    with pytest.raises(ValueError, match="Длительность должна быть положительной"):
        scheduler.find_slot_for_duration(0)
    with pytest.raises(ValueError, match="Длительность должна быть положительной"):
        scheduler.find_slot_for_duration(-10)


def test_find_slot_for_duration_empty_data(scheduler_empty_data):
    assert scheduler_empty_data.find_slot_for_duration(60) is None


def test_to_datetime_valid():
    dt = Scheduler.to_datetime("2025-02-15", "09:00")
    assert dt == datetime(2025, 2, 15, 9, 0)


def test_to_datetime_invalid_format():
    with pytest.raises(ValueError, match="time data"):
        Scheduler.to_datetime("2025-02-15", "25:00")

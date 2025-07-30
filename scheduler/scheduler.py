import requests
import datetime


class Scheduler:
    def __init__(self, url: str):
        self._url = url
        self._days, self._slots = self._parse_data(url)

    @property
    def days(self):
        return self._days

    @property
    def slots(self):
        return self._slots

    @staticmethod
    def to_datetime(date: str, time: str) -> datetime.datetime:
        return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    @staticmethod
    def to_time_str(date_time: datetime.datetime) -> str:
        return date_time.strftime("%H:%M")

    @staticmethod
    def _parse_data(url: str):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            days = data.get('days')
            timeslots = data.get('timeslots')
            if not isinstance(days, list) or not isinstance(timeslots, list):
                raise ValueError("Invalid data format: 'days' and 'timeslots' must be lists")
            return days, timeslots
        except Exception as e:
            raise ValueError(f"Failed to get data from {url}: {e}")

    def refresh_data(self):
        """Я решил добавить метод, с помощью которого можно было обновлять данные без создания нового обьекта"""
        try:
            self._days, self._slots = self._parse_data(self._url)
        except Exception as e:
            raise RuntimeError(f"Failed to refresh data: {e}")

    def check_day_exist(self, date: str):
        """Данный метод проверяет валидность введенной даты, что она существует"""
        for day in self.days:
            if day['date'] == date:
                return day
        return None

    def get_busy_slots(self, date: str):
        for day in self.days or []:
            if day['date'] == date:
                return sorted(
                    [(slot['start'], slot['end']) for slot in self._slots or [] if slot['day_id'] == day['id']],
                    key=lambda x: x[0]
                )
        return []

    def get_free_slots(self, date: str):
        if not (day := self.check_day_exist(date)):
            return []

        day_start = self.to_datetime(date, day['start'])
        day_end = self.to_datetime(date, day['end'])

        busy_slots = sorted([
            (self.to_datetime(date, start),
             self.to_datetime(date, end))
            for start, end in self.get_busy_slots(date)
        ], key=lambda x: x[0])

        if not busy_slots:
            return [(day['start'], day['end'])]

        free_slots = []
        prev_end = day_start

        for busy_start, busy_end in busy_slots:
            if busy_start > prev_end:
                free_slots.append((prev_end, busy_start))
            prev_end = max(prev_end, busy_end)

        if prev_end < day_end:
            free_slots.append((prev_end, day_end))

        return [
            (self.to_time_str(start), self.to_time_str(end))
            for start, end in free_slots
        ]

    def is_available(self, date: str, start_time: str, end_time: str):
        if start_time >= end_time:
            return False
        start_time, end_time = self.to_datetime(date, start_time), self.to_datetime(date, end_time)
        if (not (day := self.check_day_exist(date)) or start_time < self.to_datetime(date, day["start"])
                or end_time > self.to_datetime(date, day['end'])):
            return False
        for free_start, free_end in self.get_free_slots(date):
            free_start = self.to_datetime(date, free_start)
            free_end = self.to_datetime(date, free_end)
            if free_start <= start_time and free_end >= end_time:
                return True
        return False

    def find_slot_for_duration(self, duration_minutes: int):
        if duration_minutes <= 0:
            raise ValueError("Длительность должна быть положительной")
        for day in sorted(self.days or [], key=lambda x: x['date']):
            for start, end in self.get_free_slots(day['date']):
                start_dt, end_dt = self.to_datetime(day['date'], start), self.to_datetime(day['date'], end)
                if (end_dt - start_dt).total_seconds() // 60 >= duration_minutes:
                    return day['date'], start, self.to_time_str(start_dt + datetime.timedelta(minutes=duration_minutes))
        return None


if __name__ == '__main__':
    pass

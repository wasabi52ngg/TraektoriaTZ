from scheduler import Scheduler

if __name__ == '__main__':
    scheduler = Scheduler(url="https://ofc-test-01.tspb.su/test-task/")
    print(scheduler.get_busy_slots("2025-02-15"))
    print(scheduler.get_free_slots("2025-02-15"))
    print(scheduler.is_available("2025-02-15", "12:00", "13:30"))
    print(scheduler.is_available("2025-02-15", "10:00", "11:30"))
    print(scheduler.find_slot_for_duration(duration_minutes=60))
    print(scheduler.find_slot_for_duration(duration_minutes=120))

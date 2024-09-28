import datetime

from rich.console import Console
from rich.table import Table

from usthing.api import HingAPI

console = Console()


def check_booking_status():
    hing = HingAPI()
    lib_info = hing.get_info_library_areas()

    console.print("Please select the area you want to check the booking status for:")

    for area in lib_info:
        console.print(f"[{area['id']}] {area['area_name']}")

    area_choice = int(input("Enter the number of the area you want to check: "))
    date = input("Enter the date of the booking (YYYY-MM-DD): ")
    time_range = input("Enter the time range of the booking (HH:MM-HH:MM): ")

    # find out area info by finding id==area_choice
    area_info: dict | None = None
    for area in lib_info:
        if area["id"] == str(area_choice):
            area_info = area
            break

    if area_info is None:
        console.print("Invalid area choice")
        return

    # Parse time range
    start_time, end_time = time_range.split("-")

    if int(start_time.split(":")[1]) > 59 or int(end_time.split(":")[1]) > 59:
        console.print("Invalid time range")
        return

    if int(start_time.split(":")[0]) > 23 or int(end_time.split(":")[0]) > 23:
        console.print("Invalid time range")
        return

    # the end time should be greater than the start time
    if int(start_time.split(":")[0]) > int(end_time.split(":")[0]):
        console.print("Invalid time range")
        return

    # if start_time.split(":")[1] != "00" or end_time.split(":")[1] != "30":
    start_time_last = "00" if int(start_time.split(":")[1]) < 30 else "30"
    start_time = f"{start_time.split(':')[0]}:{start_time_last}"
    end_time_last = "00" if int(end_time.split(":")[1]) < 30 else "30"
    end_time = f"{end_time.split(':')[0]}:{end_time_last}"

    # get all time slots in 30 minutes interval, if last one xx:00, then it should not be included
    time_slots: list[str] = []
    current_time_date = datetime.datetime.strptime(start_time, "%H:%M")
    end_time_date = datetime.datetime.strptime(end_time, "%H:%M")

    while current_time_date < end_time_date:
        if current_time_date.strftime("%H:%M") == end_time:
            break
        time_slots.append(current_time_date.strftime("%H:%M"))
        current_time_date += datetime.timedelta(minutes=30)

    console.print(
        f"Checking booking status for {time_range} time range, with time slots: {', '.join(time_slots)}"
    )

    # get all bookings for the area
    year, month, day = date.split("-")
    rooms = hing.get_sessions_by_day(area_choice, year, month, day)

    table = Table(
        title=f"Available {area_info['area_name']} ({time_range})",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Room ID", style="dim")
    table.add_column("Room Name", style="dim")
    table.add_column("Room Capacity", style="dim")
    # table.add_column("Time", style="dim")

    available_rooms = []

    for room in rooms:
        okay_num = 0
        required_available_slots_amount = len(time_slots)
        for session in room["sessions"]:
            for time_slot in time_slots:

                def get_next_30_minutes(time: str) -> str:
                    hour, minute = time.split(":")
                    if minute == "00":
                        return f"{hour}:30"
                    else:
                        return f"{int(hour) + 1}:00"

                start_cond = session["start_time_hhmm"] == time_slot
                end_cond = session["end_time_hhmm"] == get_next_30_minutes(time_slot)

                date_cond = session["start_time_YYYYMMDD"] == date.replace("-", "")

                if (
                    session["status"] == "available"
                    and start_cond
                    and end_cond
                    and date_cond
                ):
                    okay_num += 1

        if okay_num == required_available_slots_amount:
            # console.print(f"Room {room['room_name']} is available for booking")
            table.add_row(room["id"], room["room_name"], room["capacity"])

            room["year"] = year
            room["month"] = month
            room["day"] = day
            room["hour"] = start_time.split(":")[0]
            room["min"] = start_time.split(":")[1]
            room["area_id"] = area_choice

            # get minutes difference between start and end time
            min_delta = (
                datetime.datetime.strptime(end_time, "%H:%M")
                - datetime.datetime.strptime(start_time, "%H:%M")
            ).seconds / 60

            room["duration"] = min_delta

            available_rooms.append(room)

    if len(available_rooms) == 0:
        console.print("No available rooms for booking")
    else:
        console.print(table)

    return available_rooms


if __name__ == "__main__":
    check_booking_status()

import sys

from rich.console import Console

from usthing.api import HingAPI
from usthing.booking_availability import check_booking_status

console = Console()


def book():
    hing = HingAPI()
    rooms = check_booking_status()

    if len(rooms) == 0:
        print("No available rooms for booking")
        sys.exit(1)

    room_id = input("Enter the room ID you want to book: ")

    room = next((room for room in rooms if room["id"] == room_id), None)

    if room is None:
        print("Invalid room ID")
        sys.exit(1)

    response = hing.book_library_room(
        room["area_id"],
        room["id"],
        room["year"],
        room["month"],
        room["day"],
        room["hour"],
        room["min"],
        room["duration"],
    )

    if response["status"] == "success":
        console.print("Booking successful", style="green")


if __name__ == "__main__":
    book()

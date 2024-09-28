import time

from rich.console import Console
from rich.table import Table

from usthing.api import HingAPI

console = Console()


def get_booking():
    hing = HingAPI()
    lib_info = hing.get_info_library_areas()
    bookings = hing.get_my_bookings()

    for booking in bookings:
        for area in lib_info:
            for rooms in area["rooms"]:
                if booking["room_id"] == rooms["id"]:
                    booking["room_name"] = rooms["room_name"]
                    booking["area_name"] = area["area_name"]

    # Print a beautiful table

    table = Table(title="My Bookings", show_header=True, header_style="bold magenta")
    # table.add_column("Booking ID", style="dim", width=12)
    # table.add_column("Date", style="dim")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Area", style="dim")
    table.add_column("Room", style="dim")
    # table.add_column("Status", style="dim", width=20)

    for booking in bookings:
        starting_date = time.strftime(
            "%Y-%m-%d", time.localtime(int(booking["start_time"]))
        )
        ending_date = time.strftime(
            "%Y-%m-%d", time.localtime(int(booking["end_time"]))
        )

        # Format the time to HH:MM
        booking["start_time"] = time.strftime(
            "%H:%M", time.localtime(int(booking["start_time"]))
        )
        booking["end_time"] = time.strftime(
            "%H:%M", time.localtime(int(booking["end_time"]))
        )

        table.add_row(
            # booking["id"],
            starting_date,
            ending_date if starting_date != ending_date else "-",
            booking["start_time"],
            booking["end_time"],
            booking["area_name"],
            booking["room_name"],
            # booking["status"],
        )
    console.print(table)

    # return bookings


if __name__ == "__main__":
    get_booking()

import requests

from usthing.get_ms_token import get_access_token


class HingAPI:
    def __init__(self):
        self.key = get_access_token()
        headers = {
            "Authorization": f"Bearer {self.key}",
            "accept": "application/json",
            "user-agent": "USThing/113 CFNetwork/1568.100.1 Darwin/24.0.0",
            "accept-language": "en-GB,en;q=0.9",
        }
        self.headers = headers
        session = requests.Session()
        session.headers.update(headers)
        self.session = session

    def get_my_bookings(self):
        url = "https://library.api.usthing.xyz/v1/getMySchedule"
        response = self.session.get(url)
        data = response.json()
        return data["data"]["bookings"]

    def get_info_library_areas(self):
        url = "https://library.api.usthing.xyz/v1/getInfo"
        response = self.session.get(url)

        if response.status_code > 300:
            print(response.status_code)
            print(response.text)
            raise ValueError("Error when getting library areas!")

        data = response.json()
        return data["data"]["areas"]

    def book_library_room(
        self, area_id, room_id, year, month, day, hour, _min, duration
    ):
        # duration no dot
        duration = int(duration)

        if duration > 120:
            raise ValueError(
                "Duration must be under 120, this is a limitation for each student in HKUST."
            )

        url = f"https://library.api.usthing.xyz/v1/entry?area={area_id}&room={room_id}&year={year}&month={month}&day={day}&hour={hour}&min={_min}&duration={duration}"

        response = self.session.post(url, data=None)

        if response.status_code > 300:
            print(response.status_code)
            print(response.text)
            raise ValueError("Error when booking library room!")

        return response.json()

    def get_sessions_by_day(self, area_id, year, month, day):
        url = f"https://library.api.usthing.xyz/v1/getSessionsByDay?area={area_id}&year={year}&month={month}&day={day}"
        response = self.session.get(url)

        if response.status_code > 300:
            print(response.status_code)
            print(response.text)
            raise ValueError("Error when getting sessions by day!")

        data = response.json()
        return data["data"]["rooms"]

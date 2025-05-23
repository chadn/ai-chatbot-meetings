# To Do

-   :white_check_mark: Create initial streamlit that uses OpenAI and Langchain
-   :white_check_mark: Integrate cal.com API
-   Support cancelling events. When the user says something like "cancel my event at 3pm today", find the event (based on the user's email) and cancel the correct event.
-   Support rescheduling events booked by the user.
-   Support CALCOM_BOOKING_EVENT_TYPE_SLUG instead of CALCOM_BOOKING_EVENT_TYPE_ID by fetching ID from https://cal.com/docs/api-reference/v2/event-types/get-all-event-types
-   Support pagination with cal.com API
-   Fix skipped tests from `pytest tests`


## Bugs

-   In download_messages(), where user can save chat messages as json, user must Click twice to get latest.  Should just click once.

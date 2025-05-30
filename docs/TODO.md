# To Do

-   :white_check_mark: Create initial streamlit that uses OpenAI and Langchain
-   :white_check_mark: Integrate cal.com API
-   :white_check_mark: fetch username and event type ids based on CALCOM_API_KEY.
-   Support cancelling events. When the user says something like "cancel my event at 3pm today", find the event (based on the user's email) and cancel the correct event.
-   Support rescheduling events booked by the user.
-   Support pagination with cal.com API
-   Fix skipped tests from `pytest tests`


## Bugs

-   In download_messages(), where user can save chat messages as json, user must Click twice to get latest.  Should just click once.

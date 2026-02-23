"""
Conversation states for the visa bot wizard.
Each integer maps to a step in the ConversationHandler.
"""
from enum import IntEnum


class State(IntEnum):
    # Visa type selection
    VISA_TYPE = 0

    # Ship information
    SHIP_NAME = 1
    SHIP_OWNER = 2
    SHIP_IMO = 3
    SHIP_REG_DATE = 4

    # Routing
    ORIGIN = 5
    DESTINATION = 6

    # Crew loop
    CREW_FULLNAME = 7
    CREW_PASSPORT = 8
    CREW_PASSPORT_EXPIRY = 9
    CREW_CDC = 10
    CREW_CDC_EXPIRY = 11
    CREW_GENDER = 12
    CREW_DOB = 13
    CREW_RANK = 14
    ADD_MORE_CREW = 15

    # Final confirmation
    CONFIRM = 16

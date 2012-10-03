# Account creation errors
CANNOT_CREATE_ACCOUNT = 'C100'
AMOUNT_TOO_LOW = 'C101'
AMOUNT_TOO_HIGH = 'C102'
INVALID_USER_DETAILS = 'C103'
INVALID_DATES = 'C104'

MESSAGES = {
    CANNOT_CREATE_ACCOUNT: "Cannot create account",
    AMOUNT_TOO_LOW: "Amount too low",
    AMOUNT_TOO_HIGH: "Amount too high",
    INVALID_USER_DETAILS: "Invalid user details",
    INVALID_DATES: "Invalid dates",
}


def message(code):
    return MESSAGES.get(code, "Unknown error")

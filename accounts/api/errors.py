# Account creation errors
CANNOT_CREATE_ACCOUNT = 'C100'
AMOUNT_TOO_LOW = 'C101'
AMOUNT_TOO_HIGH = 'C102'

# Redemption errors
CANNOT_CREATE_TRANSFER = 'T100'
INSUFFICIENT_FUNDS = 'T101'
ACCOUNT_INACTIVE = 'T102'

MESSAGES = {
    CANNOT_CREATE_ACCOUNT: "Cannot create account",
    AMOUNT_TOO_LOW: "Amount too low",
    AMOUNT_TOO_HIGH: "Amount too high",
    CANNOT_CREATE_TRANSFER: "Cannot create transfer",
    INSUFFICIENT_FUNDS: "Insufficient funds",
    ACCOUNT_INACTIVE: "Account inactive",
}


def message(code):
    return MESSAGES.get(code, "Unknown error")

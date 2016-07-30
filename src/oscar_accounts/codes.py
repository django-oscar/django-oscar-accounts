import random
import string

from oscar_accounts.compact_oscar import get_model

Account = get_model('oscar_accounts', 'Account')


def generate(size=12, chars=None):
    """
    Generate a new account code

    :size: Length of code
    :chars: Character set to choose from
    """
    if chars is None:
        chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for x in range(size))
    # Ensure code does not aleady exist
    try:
        Account.objects.get(code=code)
    except Account.DoesNotExist:
        return code
    return generate(size=size, chars=chars)

import random
import string

from django.db.models import get_model

Account = get_model('accounts', 'Account')


def generate(size=8, chars=None):
    if chars is None:
        chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for x in range(size))
    try:
        Account.objects.get(code=code)
    except Account.DoesNotExist:
        return code
    return generate(size=size, chars=chars)

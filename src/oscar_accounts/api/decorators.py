import base64

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponse


def view_or_basicauth(view, request, *args, **kwargs):
    # Check for valid basic auth header
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).decode('utf-8').split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    request.user = user
                    return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    response = HttpResponse()
    response.status_code = 401
    realm = getattr(settings, 'BASIC_AUTH_REALM', 'Forbidden')
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


def basicauth(view_func):
    """
    Basic auth decorator
    """
    def wrapper(request, *args, **kwargs):
        return view_or_basicauth(view_func, request, *args, **kwargs)
    return wrapper

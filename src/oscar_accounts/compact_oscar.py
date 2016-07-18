try:
    import oscar.core

except ImportError:
    from importlib import import_module
    from django.apps import apps
    from django.apps.config import MODELS_MODULE_NAME
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
    from django import forms

    # from oscar.core.compat
    # A setting that can be used in foreign key declarations
    AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
    try:
        AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit('.', 1)
    except ValueError:
        raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form"
                                   " 'app_label.model_name'")

    # from oscar.core.loading
    def get_model(app_label, model_name):
        """
        Fetches a Django model using the app registry.
        This doesn't require that an app with the given app label exists,
        which makes it safe to call when the registry is being populated.
        All other methods to access models might raise an exception about the
        registry not being ready yet.
        Raises LookupError if model isn't found.
        """
        try:
            return apps.get_model(app_label, model_name)
        except AppRegistryNotReady:
            if apps.apps_ready and not apps.models_ready:
                # If this function is called while `apps.populate()` is
                # loading models, ensure that the module that defines the
                # target model has been imported and try looking the model up
                # in the app registry. This effectively emulates
                # `from path.to.app.models import Model` where we use
                # `Model = get_model('app', 'Model')` instead.
                app_config = apps.get_app_config(app_label)
                # `app_config.import_models()` cannot be used here because it
                # would interfere with `apps.populate()`.
                import_module('%s.%s' % (app_config.name, MODELS_MODULE_NAME))
                # In order to account for case-insensitivity of model_name,
                # look up the model through a private API of the app registry.
                return apps.get_registered_model(app_label, model_name)
            else:
                # This must be a different case (e.g. the model really doesn't
                # exist). We just re-raise the exception.
                raise


    # from oscar.core.loading
    def is_model_registered(app_label, model_name):
        """
        Checks whether a given model is registered. This is used to only
        register Oscar models if they aren't overridden by a forked app.
        """
        try:
            apps.get_registered_model(app_label, model_name)
        except LookupError:
            return False
        else:
            return True

    # from oscar.apps.payment.exceptions
    class UnableToTakePayment(Exception):
        """
        Exception to be used for ANTICIPATED payment errors (eg card number wrong,
        expiry date has passed).  The message passed here will be shown to the end
        user.
        """

    # dummy for oscar.templatetags.currency_filters.currency
    def currency(value, currency=None):
        return value

    # dummy for oscar.forms.widgets.DatePickerInput
    DatePickerInput = forms.DateInput

    # dummy for oscar.application.Application
    class Application(object):
        def post_process_urls(self, urlpatterns):
            return urlpatterns


else:  # oscar is installed, use it.
    from oscar.apps.payment.exceptions import UnableToTakePayment
    from oscar.core.application import Application
    from oscar.core.compat import AUTH_USER_MODEL
    from oscar.core.loading import get_model, is_model_registered
    from oscar.forms.widgets import DatePickerInput
    from oscar.templatetags.currency_filters import currency


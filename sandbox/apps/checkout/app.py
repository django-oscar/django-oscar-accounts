from oscar.apps.checkout import app

from apps.checkout import views


class CheckoutApplication(app.CheckoutApplication):
    payment_details_view = views.PaymentDetailsView


application = CheckoutApplication()

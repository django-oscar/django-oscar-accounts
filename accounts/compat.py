try:
    from oscar.templatetags.currency_filters import render_currency as currency
except importError:
    from oscar.templatetags.currency_filters import currency

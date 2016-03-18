from decimal import Decimal as D

from oscar.apps.shipping.methods import FixedPrice, NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository

# Dummy shipping methods
method1 = FixedPrice(D('10.00'))
method1.code = 'method1'
method1.description = 'Ship by van'

method2 = FixedPrice(D('20.00'))
method2.code = 'method2'
method2.description = 'Ship by boat'


class Repository(CoreRepository):
    methods = (method1, method2,)

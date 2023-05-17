# This file is part margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import sale
from . import sale_discount


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSaleMethod,
        sale.Sale,
        sale.SaleLine,
        module='sale_margin', type_='model')
    Pool.register(
        sale_discount.SaleLine,
        module='sale_margin', type_='model', depends=['sale_discount'])
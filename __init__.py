#This file is part margin module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import sale


def register():
    Pool.register(
        configuration.Configuration,
        sale.Sale,
        sale.SaleLine,
        module='sale_margin', type_='model')

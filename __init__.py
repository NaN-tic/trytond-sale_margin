#This file is part margin module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .sale import *


def register():
    Pool.register(
        Sale,
        SaleLine,
        module='sale_margin', type_='model')

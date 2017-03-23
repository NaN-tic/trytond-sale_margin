# This file is part sale_margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import PoolMeta

__all__ = ['Configuration']


class Configuration:
    __metaclass__ = PoolMeta
    __name__ = 'sale.configuration'
    sale_margin_method = fields.Property(fields.Selection([
                ('unit_price', 'Unit Price'),
                ('cost_price', 'Cost Price'),
                ], 'Sale Margin Method', states={
                'required': Bool(Eval('context', {}).get('company')),
                }))

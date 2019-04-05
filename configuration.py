# This file is part sale_margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import Pool, PoolMeta

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

    @classmethod
    def __setup__(cls):
        super(Configuration, cls).__setup__()
        cls._error_messages.update({
                'change_sale_margin_method': ('You cannot change the sale '
                    'margin method because has sales.'),
                })
        cls._modify_no_sale = [
            ('sale_margin_method', 'change_sale_margin_method'),
            ]

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        for _, values in zip(actions, actions):
            for field, error in cls._modify_no_sale:
                    if field in values:
                        cls.check_no_sale(error)
                        break
        super(Configuration, cls).write(*args)

    @classmethod
    def check_no_sale(cls, error):
        Sale = Pool().get('sale.sale')

        sales = Sale.search([], limit=1, order=[])
        if sales:
            cls.raise_user_error(error)

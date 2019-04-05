# This file is part sale_margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta

__all__ = ['Configuration', 'ConfigurationSaleMethod']

SALE_MARGIN_METHOD = [
    ('unit_price', 'Unit Price'),
    ('cost_price', 'Cost Price'),
    ]
sale_margin_method = fields.Selection(SALE_MARGIN_METHOD, 'Sale Margin Method')


class Configuration:
    __metaclass__ = PoolMeta
    __name__ = 'sale.configuration'
    sale_margin_method = fields.MultiValue(sale_margin_method)

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'sale_margin_method':
            return pool.get('sale.configuration.sale_method')
        return super(Configuration, cls).multivalue_model(field)

    @classmethod
    def default_sale_margin_method(cls, **pattern):
        return cls.multivalue_model(
            'sale_margin_method').default_sale_margin_method()

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


class ConfigurationSaleMethod:
    __metaclass__ = PoolMeta
    __name__ = 'sale.configuration.sale_method'
    sale_margin_method = sale_margin_method

    @classmethod
    def default_sale_margin_method(cls):
        return 'cost_price'

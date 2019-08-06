# This file is part sale_margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from math import fabs
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.modules.product import price_digits

__all__ = ['Sale', 'SaleLine']

_ZERO = Decimal(0)

class Sale:
    __metaclass__ = PoolMeta
    __name__ = 'sale.sale'
    margin = fields.Function(fields.Numeric('Margin',
            digits=(16, Eval('currency_digits', 2),),
            depends=['currency_digits'],
            help=('It gives profitability by calculating the difference '
                'between the Unit Price and Cost Price.')),
        'get_margin')
    margin_cache = fields.Numeric('Margin Cache',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    margin_percent = fields.Function(fields.Numeric('Margin (%)',
            digits=(16, 4)),
        'get_margin_percent')
    margin_percent_cache = fields.Numeric('Margin (%) Cache',
        digits=(16, 4), readonly=True)

    def get_margin(self, name):
        '''
        Return the margin of each sales
        '''
        Currency = Pool().get('currency.currency')
        if (self.state in self._states_cached
                and self.margin_cache is not None):
            return self.margin_cache
        margin = sum((l.margin for l in self.lines if l.type == 'line'),
                _ZERO)
        return Currency.round(self.currency, margin)

    def get_margin_percent(self, name):
        if (self.state in self._states_cached
                and self.margin_percent_cache is not None):
            return self.margin_percent_cache

        cost = sum(
            Decimal(str(fabs(l.quantity))) * (l.cost_price or _ZERO)
            for l in self.lines if l.type == 'line')
        if cost:
            return (self.margin / cost).quantize(Decimal('0.0001'))
        else:
            return Decimal('1.0')

    @classmethod
    def store_cache(cls, sales):
        super(Sale, cls).store_cache(sales)
        for sale in sales:
            cls.write([sale], {
                    'margin_cache': sale.margin,
                    'margin_percent_cache': sale.margin_percent,
                    })


class SaleLine:
    __metaclass__ = PoolMeta
    __name__ = 'sale.line'
    cost_price = fields.Numeric('Cost Price', digits=price_digits,
        states={
            'invisible': Eval('type') != 'line',
            }, depends=['type'])
    margin = fields.Function(fields.Numeric('Margin',
            digits=(16, Eval('_parent_sale', {}).get('currency_digits', 2)),
            states={
                'invisible': ~Eval('type').in_(['line', 'subtotal']),
                'readonly': ~Eval('_parent_sale'),
                },
            depends=['type', 'amount']),
        'on_change_with_margin')
    margin_percent = fields.Function(fields.Numeric('Margin (%)',
            digits=(16, 4), states={
                'invisible': ~Eval('type').in_(['line', 'subtotal']),
                }, depends=['type']),
        'on_change_with_margin_percent')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        if hasattr(cls, 'gross_unit_price'):
            cls.on_change_with_margin.depends.add('gross_unit_price')

    @staticmethod
    def default_cost_price():
        return _ZERO

    @fields.depends('product')
    def on_change_product(self):
        super(SaleLine, self).on_change_product()
        if self.product:
            cost_price = self.product.cost_price
            self.cost_price = cost_price.quantize(
                Decimal(1) / 10 ** self.__class__.cost_price.digits[1])

    @fields.depends('type', 'quantity', 'cost_price', '_parent_sale.currency',
        '_parent_sale.lines', methods=['amount'])
    def on_change_with_margin(self, name=None):
        '''
        Return the margin of each sale lines
        '''
        Currency = Pool().get('currency.currency')
        cost = _ZERO
        if self.sale and self.sale.currency:
            currency = self.sale.currency
            if self.type == 'line':
                if self.quantity and self.cost_price:
                    cost = Decimal(str(self.quantity)) * (self.cost_price)
                self.amount = self.on_change_with_amount()
                return Currency.round(currency, self.amount - cost)
            elif self.type == 'subtotal':
                for line2 in self.sale.lines:
                    if self == line2:
                        return cost
                    if line2.type == 'line':
                        cost_price = line2.cost_price or _ZERO
                        cost2 = Decimal(str(line2.quantity)) * cost_price
                        cost += Currency.round(currency, line2.amount - cost2)
                    elif line2.type == 'subtotal':
                        cost = _ZERO
        return cost

    @fields.depends('type', 'quantity', 'cost_price', '_parent_sale.currency',
        '_parent_sale.lines', methods=['margin'])
    def on_change_with_margin_percent(self, name=None):
        if self.type not in ('line', 'subtotal'):
            return
        self.margin = self.on_change_with_margin()
        if not self.margin:
            return
        cost = _ZERO
        if self.type == 'line':
            if not self.quantity:
                return
            if not self.cost_price:
                return Decimal('1.0')
            cost_price = self.get_cost_price()
            cost = (self.margin / cost_price).quantize(Decimal('0.0001'))
        else:
            for line2 in self.sale.lines:
                if self == line2:
                    if not cost:
                        return Decimal('1.0')
                    else:
                        return (self.margin / cost).quantize(Decimal('0.0001'))
                if line2.type == 'line':
                    cost += line2.get_cost_price()
                elif line2.type == 'subtotal':
                    cost = _ZERO

        return cost

    def get_cost_price(self):
        return Decimal(str(fabs(self.quantity))) * (self.cost_price or _ZERO)

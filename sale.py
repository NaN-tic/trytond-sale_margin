#This file is part sale_margin module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from decimal import Decimal
from math import fabs
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.config import config as config_

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta

DIGITS = config_.getint('product', 'price_decimal', default=4)


class Sale:
    __name__ = 'sale.sale'
    margin = fields.Function(fields.Numeric('Margin',
            digits=(16, Eval('currency_digits', 2),),
            depends=['currency_digits'],
            help='It gives profitability by calculating the difference '
                'between the Unit Price and Cost Price.'),
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
                Decimal(0))
        return Currency.round(self.currency, margin)

    def get_margin_percent(self, name):
        if (self.state in self._states_cached
                and self.margin_percent_cache is not None):
            return self.margin_percent_cache

        cost = sum(
            Decimal(str(fabs(l.quantity))) * (l.cost_price or Decimal(0))
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
    __name__ = 'sale.line'
    cost_price = fields.Numeric('Cost Price', digits=(16, DIGITS),
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
        return Decimal(0)

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
        if not self.sale or not self.sale.currency:
            return Decimal(0)
        currency = self.sale.currency
        if self.type == 'line':
            if self.quantity and self.cost_price:
                cost = Decimal(str(self.quantity)) * (self.cost_price)
            else:
                cost = Decimal(0)
            self.amount = self.on_change_with_amount()
            return Currency.round(currency, self.amount - cost)
        elif self.type == 'subtotal':
            cost = Decimal(0)
            for line2 in self.sale.lines:
                if self == line2:
                    return cost
                if line2.type == 'line':
                    cost2 = Decimal(str(line2.quantity)) * (line2.cost_price or
                        Decimal(0))
                    cost += Currency.round(currency, line2.amount - cost2)
                elif line2.type == 'subtotal':
                    cost = Decimal(0)
        else:
            return Decimal(0)

    @fields.depends('type', 'quantity', 'cost_price', '_parent_sale.currency',
        '_parent_sale.lines', methods=['margin'])
    def on_change_with_margin_percent(self, name=None):
        if self.type not in ('line', 'subtotal'):
            return
        self.margin = self.on_change_with_margin()
        if not self.margin:
            return
        if self.type == 'line':
            if not self.quantity:
                return
            if not self.cost_price:
                return Decimal('1.0')
            cost = self.get_cost_price()
            return (self.margin / cost).quantize(Decimal('0.0001'))
        else:
            cost = Decimal(0)
            for line2 in self.sale.lines:
                if self == line2:
                    if not cost:
                        return Decimal('1.0')
                    else:
                        return (self.margin / cost).quantize(Decimal('0.0001'))
                if line2.type == 'line':
                    cost += line2.get_cost_price()
                elif line2.type == 'subtotal':
                    cost = Decimal(0)

    def get_cost_price(self):
        return Decimal(str(fabs(self.quantity))) * (self.cost_price or
                Decimal(0))

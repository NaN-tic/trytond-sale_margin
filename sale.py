# This file is part sale_margin module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from math import fabs
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.modules.product import price_digits
from trytond.modules.currency.fields import Monetary

__all__ = ['Sale', 'SaleLine']

_ZERO = Decimal(0)


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    margin = fields.Function(Monetary('Margin',
        currency='currency', digits='currency',
        help=('It gives profitability by calculating the difference '
            'between the Unit Price and Cost Price.')),
        'get_margin')
    margin_cache = Monetary('Margin Cache',
        currency='currency', digits='currency', readonly=True)
    margin_percent = fields.Function(fields.Numeric('Margin (%)',
        digits=(16, 4)), 'get_margin_percent')
    margin_percent_cache = fields.Numeric('Margin (%) Cache',
        digits=(16, 4), readonly=True)

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['margin_cache'] = None
        default['margin_percent_cache'] = None
        return super(Sale, cls).copy(sales, default=default)

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
        Configuration = Pool().get('sale.configuration')

        config = Configuration(1)
        sale_margin_method = config.sale_margin_method or 'cost_price'

        if (self.state in self._states_cached
                and self.margin_percent_cache is not None):
            return self.margin_percent_cache

        price = sum(
            Decimal(str(fabs(l.quantity))) * (
                getattr(l, sale_margin_method) or _ZERO)
            for l in self.lines if l.type == 'line')
        if price:
            return (self.margin / price).quantize(Decimal('0.0001'))
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


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'
    cost_price = fields.Numeric('Cost Price', digits=price_digits,
        states={
            'invisible': Eval('type') != 'line',
            'readonly': ~Eval('sale_state').in_(['draft', 'quotation']),
            },
        depends=['type', 'sale_state'])
    margin = fields.Function(Monetary('Margin',
        currency='currency', digits='currency',
        states={
            'invisible': ~Eval('type').in_(['line', 'subtotal']),
            'readonly': ~Eval('_parent_sale'),
            },
        depends=['type', 'amount']), 'on_change_with_margin')
    margin_percent = fields.Function(fields.Numeric('Margin (%)',
        digits=(16, 4), states={
            'invisible': ~Eval('type').in_(['line', 'subtotal']),
            }, depends=['type']), 'on_change_with_margin_percent')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        if hasattr(cls, 'gross_unit_price'):
            cls.margin.on_change_with.add('gross_unit_price')
            cls.margin_percent.on_change_with.add('gross_unit_price')

    @staticmethod
    def default_cost_price():
        return _ZERO

    @fields.depends('product', 'currency')
    def on_change_product(self):
        Currency = Pool().get('currency.currency')

        super(SaleLine, self).on_change_product()

        if self.product:
            if self.currency:
                cost_price = Currency.compute(
                    self.currency, self.product.cost_price,
                    self.sale.currency, round=False)
            else:
                cost_price = self.product.cost_price
            self.cost_price = cost_price

    @fields.depends('type', 'quantity', 'cost_price', '_parent_sale.currency',
        '_parent_sale.lines', methods=['on_change_with_amount'])
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

    @fields.depends('type', 'quantity', 'cost_price', 'unit_price',
        '_parent_sale.currency', '_parent_sale.lines',
        methods=['on_change_with_margin'])
    def on_change_with_margin_percent(self, name=None):
        Configuration = Pool().get('sale.configuration')

        config = Configuration(1)
        sale_margin_method = config.sale_margin_method or 'cost_price'

        if self.type not in ('line', 'subtotal'):
            return
        self.margin = self.on_change_with_margin()
        if not self.margin:
            return
        price = _ZERO
        if self.type == 'line':
            if not self.quantity:
                return
            if sale_margin_method == 'cost_price' and not self.cost_price:
                return Decimal('1.0')
            if sale_margin_method == 'unit_price' and not self.unit_price:
                return Decimal('1.0')
            if sale_margin_method == 'unit_price':
                price = self.get_margin_unit_price()
            else:
                price = self.get_margin_cost_price()
            return (self.margin / price).quantize(Decimal('0.0001'))
        else:
            for line2 in self.sale.lines:
                if self == line2:
                    if not price:
                        return Decimal('1.0')
                    else:
                        return (
                            self.margin / price).quantize(Decimal('0.0001'))
                if line2.type == 'line':
                    if sale_margin_method == 'unit_price':
                        price += line2.get_margin_unit_price()
                    else:
                        price += line2.get_margin_cost_price()
                elif line2.type == 'subtotal':
                    price = _ZERO
        return price

    def get_margin_cost_price(self):
        return Decimal(str(fabs(self.quantity))) * (self.cost_price or
                _ZERO)

    def get_margin_unit_price(self):
        return Decimal(str(fabs(self.quantity))) * (self.unit_price or
                _ZERO)

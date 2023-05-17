from trytond.pool import PoolMeta
from trytond.model import fields

class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    @fields.depends('gross_unit_price')
    def on_change_with_margin(self, name=None):
        return super().on_change_with_margin(name)

    @fields.depends('gross_unit_price')
    def on_change_with_margin_percent(self, name=None):
        return super().on_change_with_margin_percent(name)

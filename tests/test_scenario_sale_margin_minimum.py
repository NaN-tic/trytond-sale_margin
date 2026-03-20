import unittest
from decimal import Decimal

from proteus import Model
from trytond.exceptions import UserError, UserWarning
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install sale_margin
        config = activate_modules('sale_margin')

        # Create company
        _ = create_company()
        company = get_company()

        # Create sale user
        Group = Model.get('res.group')
        User = Model.get('res.user')
        sale_user = User()
        sale_user.name = 'Sale'
        sale_user.login = 'sale'
        sale_group, = Group.find([('name', '=', 'Sales')])
        sale_user.groups.append(sale_group)
        sale_user.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Set default accounting values
        AccountConfiguration = Model.get('account.configuration')
        account_configuration = AccountConfiguration(1)
        account_configuration.default_category_account_expense = expense
        account_configuration.default_category_account_revenue = revenue
        account_configuration.save()

        # Create category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name='Category')
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'Product'
        template.account_category = account_category
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        product, = template.products
        product.cost_price = Decimal('9')
        template.save()
        product, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Configure minimum margin
        Configuration = Model.get('sale.configuration')
        configuration = Configuration(1)
        configuration.sale_margin_minimum = Decimal('0.2')
        configuration.sale_margin_minimum_action = 'warning'
        config.user = 1
        configuration.save()

        # Sale with low margin triggers warning
        config.user = sale_user.id
        Sale = Model.get('sale.sale')
        SaleLine = Model.get('sale.line')
        sale = Sale()
        sale.party = customer
        sale.payment_term = payment_term
        sale_line = SaleLine()
        sale.lines.append(sale_line)
        sale_line.product = product
        sale_line.quantity = 1
        sale.save()

        with self.assertRaises(UserWarning):
            sale.click('quote')

        with self.assertRaises(UserWarning):
            try:
                sale.click('quote')
            except UserWarning as warning:
                _, (key, *_) = warning.args
                raise

        Warning = Model.get('res.user.warning')
        Warning.skip(key, True, config.context)
        sale.click('quote')
        sale.click('confirm')

        # Block when configured
        config.user = 1
        configuration.sale_margin_minimum_action = 'block'
        configuration.save()

        config.user = sale_user.id
        sale_block = Sale()
        sale_block.party = customer
        sale_block.payment_term = payment_term
        sale_line_block = SaleLine()
        sale_block.lines.append(sale_line_block)
        sale_line_block.product = product
        sale_line_block.quantity = 1
        sale_block.save()

        with self.assertRaises(UserError):
            sale_block.click('quote')

import unittest
from decimal import Decimal

from proteus import Model
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

        # Create products
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
        product.cost_price = Decimal('5')
        template.save()
        product, = template.products
        template2 = ProductTemplate()
        template2.name = 'Product 2'
        template2.account_category = account_category
        template2.default_uom = unit
        template2.type = 'goods'
        template2.salable = True
        template2.list_price = Decimal('80')
        template2.cost_price = Decimal('50')
        product2, = template2.products
        product2.cost_price = Decimal('5')
        template2.save()
        product2, = template2.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Sale margin with and percentatge with unit price method
        config.user = sale_user.id
        Sale = Model.get('sale.sale')
        SaleLine = Model.get('sale.line')
        sale2 = Sale()
        sale2.party = customer
        sale2.payment_term = payment_term
        sale2_line = SaleLine()
        sale2.lines.append(sale2_line)
        sale2_line.product = product
        sale2_line.quantity = 2
        sale2.save()
        self.assertEqual(sale2.margin, Decimal('10.00'))
        self.assertEqual(sale2.margin_percent, Decimal('0.5000'))
        self.assertEqual(sale2_line.margin, Decimal('10.00'))
        self.assertEqual(sale2_line.margin_percent, Decimal('0.5000'))

        # Confirm sale2 and check cache is done
        Sale.quote([sale2.id], config.context)
        Sale.confirm([sale2.id], config.context)
        self.assertEqual(sale2.margin and sale2.margin, sale2.margin_cache)
        self.assertEqual(sale2.margin_percent and sale2.margin_percent,
                         sale2.margin_percent_cache)

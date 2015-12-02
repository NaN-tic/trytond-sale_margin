====================
Sale Margin Scenario
====================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code
    >>> from.trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale_margin, sale::

    >>> Module = Model.get('ir.module')
    >>> modules = Module.find([
    ...         ('name', 'in', ('sale_margin', 'sale')),
    ...         ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create sale user::

    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']

    >>> AccountJournal = Model.get('account.journal')
    >>> stock_journal, = AccountJournal.find([('code', '=', 'STO')])

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.supply_on_sale = True
    >>> template.save()
    >>> product.template = template
    >>> product.save()
    >>> product2 = Product()
    >>> template2 = ProductTemplate()
    >>> template2.name = 'Product 2'
    >>> template2.category = category
    >>> template2.default_uom = unit
    >>> template2.type = 'goods'
    >>> template2.purchasable = True
    >>> template2.salable = True
    >>> template2.list_price = Decimal('80')
    >>> template2.cost_price = Decimal('50')
    >>> template2.account_expense = expense
    >>> template2.account_revenue = revenue
    >>> template2.supply_on_sale = True
    >>> template2.save()
    >>> product2.template = template2
    >>> product2.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Sale with 1 product::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 2
    >>> sale.save()
    >>> sale.margin
    Decimal('10.00')
    >>> sale.margin_percent
    Decimal('1.0000')

Add second product and a subtotal::

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product2
    >>> sale_line.quantity = 4
    >>> sale.save()
    >>> sale_line.margin
    Decimal('120.00')
    >>> sale_line.margin_percent
    Decimal('0.6000')
    >>> sale.margin
    Decimal('130.00')
    >>> sale.margin_percent
    Decimal('0.6190')

Add subtotal and a line without product::

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.type = 'subtotal'
    >>> sale_line.description = 'Subtotal'
    >>> sale_line2 = SaleLine()
    >>> sale.lines.append(sale_line2)
    >>> sale_line2.description = 'New product'
    >>> sale_line2.quantity = 2
    >>> sale_line2.cost_price = Decimal('100')
    >>> sale_line2.unit_price = Decimal('125')
    >>> sale.save()
    >>> sale_line.margin
    Decimal('130.00')
    >>> sale_line.margin_percent
    Decimal('0.6190')
    >>> sale_line2.margin
    Decimal('50.00')
    >>> sale_line2.margin_percent
    Decimal('0.2500')
    >>> sale.margin
    Decimal('180.00')
    >>> sale.margin_percent
    Decimal('0.4390')

Confirm sale and check cache is done::

    >>> Sale.quote([sale.id], config.context)
    >>> Sale.confirm([sale.id], config.context)
    >>> sale.margin and sale.margin == sale.margin_cache
    True
    >>> sale.margin_percent and sale.margin_percent == sale.margin_percent_cache
    True

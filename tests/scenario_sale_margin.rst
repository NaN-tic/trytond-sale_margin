====================
Sale Margin Scenario
====================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install sale_margin::

    >>> config = activate_modules('sale_margin')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create sale user::

    >>> Group = Model.get('res.group')
    >>> User = Model.get('res.user')
    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
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

Set default accounting values::

    >>> AccountConfiguration = Model.get('account.configuration')
    >>> account_configuration = AccountConfiguration(1)
    >>> account_configuration.default_category_account_expense = expense
    >>> account_configuration.default_category_account_revenue = revenue
    >>> account_configuration.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name='Category')
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.account_category = account_category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> product, = template.products
    >>> product.cost_price = Decimal('5')
    >>> template.save()
    >>> product, = template.products

    >>> template2 = ProductTemplate()
    >>> template2.name = 'Product 2'
    >>> template2.account_category = account_category
    >>> template2.default_uom = unit
    >>> template2.type = 'goods'
    >>> template2.salable = True
    >>> template2.list_price = Decimal('80')
    >>> template2.cost_price = Decimal('50')
    >>> product2, = template2.products
    >>> product2.cost_price = Decimal('5')
    >>> template2.save()
    >>> product2, = template2.products

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Change sale configuration::

    >>> Configuration = Model.get('sale.configuration')
    >>> configuration = Configuration(1)
    >>> configuration.sale_margin_method = 'cost_price'
    >>> configuration.save()

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
    >>> sale_line.margin
    Decimal('10.00')
    >>> sale_line.margin_percent
    Decimal('1.0000')

Add second product and a subtotal::

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product2
    >>> sale_line.quantity = 4
    >>> sale.save()
    >>> sale_line.margin
    Decimal('300.00')
    >>> sale_line.margin_percent
    Decimal('15.0000')
    >>> sale.margin
    Decimal('310.00')
    >>> sale.margin_percent
    Decimal('10.3333')

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
    Decimal('310.00')
    >>> sale_line.margin_percent
    Decimal('10.3333')
    >>> sale_line2.margin
    Decimal('50.00')
    >>> sale_line2.margin_percent
    Decimal('0.2500')
    >>> sale.margin
    Decimal('360.00')
    >>> sale.margin_percent
    Decimal('1.5652')

Confirm sale and check cache is done::

    >>> Sale.quote([sale.id], config.context)
    >>> Sale.confirm([sale.id], config.context)
    >>> sale.margin and sale.margin == sale.margin_cache
    True
    >>> sale.margin_percent and sale.margin_percent == sale.margin_percent_cache
    True

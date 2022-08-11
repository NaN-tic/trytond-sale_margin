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

Sale margin with and percentatge with unit price method::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale2 = Sale()
    >>> sale2.party = customer
    >>> sale2.payment_term = payment_term
    >>> sale2_line = SaleLine()
    >>> sale2.lines.append(sale2_line)
    >>> sale2_line.product = product
    >>> sale2_line.quantity = 2
    >>> sale2.save()
    >>> sale2.margin
    Decimal('10.00')
    >>> sale2.margin_percent
    Decimal('0.5000')
    >>> sale2_line.margin
    Decimal('10.00')
    >>> sale2_line.margin_percent
    Decimal('0.5000')

Confirm sale2 and check cache is done::

    >>> Sale.quote([sale2.id], config.context)
    >>> Sale.confirm([sale2.id], config.context)
    >>> sale2.margin and sale2.margin == sale2.margin_cache
    True
    >>> sale2.margin_percent and sale2.margin_percent == sale2.margin_percent_cache
    True

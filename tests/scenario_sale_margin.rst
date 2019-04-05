====================
Sale Margin Scenario
====================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale_margin, sale::

    >>> Module = Model.get('ir.module.module')
    >>> modules = Module.find([
    ...         ('name', 'in', ('sale_margin', 'sale')),
    ...         ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Zikzakmedia')
    >>> party.save()
    >>> company.party = party
    >>> currencies = Currency.find([('code', '=', 'EUR')])
    >>> if not currencies:
    ...     currency = Currency(name='EURO', symbol='€', code='EUR',
    ...         rounding=Decimal('0.01'), mon_grouping='[]',
    ...         mon_decimal_point='.')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find()

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

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name='%s' % today.year)
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_sequence = Sequence(name='%s' % today.year,
    ...     code='account.move',
    ...     company=company)
    >>> post_move_sequence.save()
    >>> fiscalyear.post_move_sequence = post_move_sequence
    >>> invoice_sequence = SequenceStrict(name='%s' % today.year,
    ...     code='account.invoice',
    ...     company=company)
    >>> invoice_sequence.save()
    >>> fiscalyear.out_invoice_sequence = invoice_sequence
    >>> fiscalyear.in_invoice_sequence = invoice_sequence
    >>> fiscalyear.out_credit_note_sequence = invoice_sequence
    >>> fiscalyear.in_credit_note_sequence = invoice_sequence
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> AccountJournal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')
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

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Direct')
    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)
    >>> payment_term.lines.append(payment_term_line)
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

Change sale configuration::

    >>> Configuration = Model.get('sale.configuration')
    >>> configuration = Configuration(1)
    >>> configuration.sale_margin_method = 'unit_price'
    >>> configuration.save()

Sale margin with and percentatge with unit price method::

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

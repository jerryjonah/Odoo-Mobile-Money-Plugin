# -*- coding: utf-8 -*-
{
    'name': 'SmobilPay Mobile Money Gateway',
    'version': '2.1.5',
    'category': 'Accounting/Payment Providers',
    'summary': 'Accept Mobile Money payments in Cameroon through SmobilPay',
    'description': """
SmobilPay Mobile Money Payment Gateway for Odoo
===============================================

Enable your Odoo e-commerce store to accept mobile money payments from customers in Cameroon through SmobilPay's secure payment platform.

Supported Payment Methods:
* MTN Mobile Money Cameroon
* Orange Mobile Money Cameroon  
* Express Union Mobile Money
* SmobilPay Cash

Key Features:
* Automatic callback URL handling
* Test and production environments
* Comprehensive payment tracking
* Real-time payment status updates
* Secure OAuth 2.0 integration
* Multi-currency support
    """,
    'author': 'Maviance PLC',
    'website': 'https://maviance.cm',
    'license': 'GPL-3',
    'depends': ['payment', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_provider_views.xml',
        'views/payment_smobilpay_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'smobilpay_odoo_gateway/static/src/css/payment_form.css',
            'smobilpay_odoo_gateway/static/src/js/payment_form.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
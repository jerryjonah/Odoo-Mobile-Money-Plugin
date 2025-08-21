# -*- coding: utf-8 -*-

import logging
import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('smobilpay', 'SmobilPay')], ondelete={'smobilpay': 'set default'}
    )
    
    # SmobilPay specific fields
    smobilpay_consumer_key = fields.Char(
        string="Consumer Key",
        help="Your SmobilPay API consumer key",
        required_if_provider="smobilpay",
        groups="base.group_system"
    )
    
    smobilpay_consumer_secret = fields.Char(
        string="Consumer Secret", 
        help="Your SmobilPay API consumer secret",
        required_if_provider="smobilpay",
        groups="base.group_system"
    )
    
    smobilpay_webhook_secret = fields.Char(
        string="Webhook Secret",
        help="Secret key for webhook validation",
        groups="base.group_system"
    )
    
    # Environment settings
    smobilpay_api_url = fields.Char(
        string="API URL",
        help="SmobilPay API endpoint URL",
        default=lambda self: self._get_default_smobilpay_api_url(),
        groups="base.group_system"
    )

    def _get_default_smobilpay_api_url(self):
        """Get default API URL based on state"""
        return "https://api.enkap.cm" if not self.state == 'test' else "https://api-staging.enkap.cm"

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Override to include SmobilPay for supported currencies"""
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        
        # SmobilPay supports XAF (Central African Franc) primarily
        currency = self.env['res.currency'].browse(currency_id) if currency_id else None
        if currency and currency.name in ['XAF', 'EUR', 'USD']:
            providers = providers.filtered(lambda p: p.code != 'smobilpay')
        
        return providers

    def _get_supported_currencies(self):
        """Return supported currencies for SmobilPay"""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'smobilpay':
            # SmobilPay primarily supports XAF but can handle other currencies
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['XAF', 'EUR', 'USD']
            )
        return supported_currencies

    def _smobilpay_get_api_url(self):
        """Get the appropriate API URL based on environment"""
        if self.state == 'test':
            return "https://api-staging.enkap.cm"
        return "https://api.enkap.cm"

    def _smobilpay_make_request(self, endpoint, data=None, method='GET'):
        """Make authenticated request to SmobilPay API"""
        url = f"{self._smobilpay_get_api_url()}{endpoint}"
        
        # Get OAuth token
        token = self._smobilpay_get_access_token()
        if not token:
            raise UserError(_("Failed to authenticate with SmobilPay API"))
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=data, headers=headers, timeout=30)
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            _logger.error("SmobilPay API request failed: %s", str(e))
            raise UserError(_("Communication with SmobilPay API failed: %s") % str(e))

    def _smobilpay_get_access_token(self):
        """Get OAuth access token from SmobilPay"""
        auth_url = f"{self._smobilpay_get_api_url()}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.smobilpay_consumer_key,
            'client_secret': self.smobilpay_consumer_secret,
        }
        
        try:
            response = requests.post(auth_url, data=auth_data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except requests.RequestException as e:
            _logger.error("Failed to get SmobilPay access token: %s", str(e))
            return False

    def _smobilpay_register_callback_url(self, callback_url):
        """Register callback URL with SmobilPay"""
        try:
            # Try multiple URL formats as the WordPress plugin does
            url_variants = [
                callback_url,
                callback_url.rstrip('/'),
                f"{callback_url.rstrip('/')}/",
            ]
            
            for url_variant in url_variants:
                try:
                    data = {'callbackUrl': url_variant}
                    response = self._smobilpay_make_request('/api/callbackurl', data, 'POST')
                    
                    if response.get('status') == 'success':
                        _logger.info("Successfully registered callback URL: %s", url_variant)
                        return True
                        
                except Exception as e:
                    _logger.warning("Failed to register callback URL %s: %s", url_variant, str(e))
                    continue
            
            # Force registration attempt for test mode
            if self.state == 'test':
                try:
                    data = {'callbackUrl': callback_url, 'force': True}
                    response = self._smobilpay_make_request('/api/callbackurl', data, 'POST')
                    return response.get('status') == 'success'
                except Exception:
                    pass
                    
            return False
            
        except Exception as e:
            _logger.error("Callback URL registration failed: %s", str(e))
            return False

    @api.constrains('state', 'smobilpay_consumer_key', 'smobilpay_consumer_secret')
    def _check_smobilpay_configuration(self):
        """Validate SmobilPay configuration"""
        for provider in self.filtered(lambda p: p.code == 'smobilpay' and p.state != 'disabled'):
            if not provider.smobilpay_consumer_key:
                raise ValidationError(_("SmobilPay Consumer Key is required"))
            if not provider.smobilpay_consumer_secret:
                raise ValidationError(_("SmobilPay Consumer Secret is required"))

    def action_test_smobilpay_connection(self):
        """Test connection to SmobilPay API"""
        self.ensure_one()
        
        try:
            token = self._smobilpay_get_access_token()
            if token:
                # Test API call to verify connection
                response = self._smobilpay_make_request('/api/ping')
                if response:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success!'),
                            'message': _('SmobilPay API connection successful'),
                            'type': 'success',
                        }
                    }
            
            raise UserError(_("Failed to connect to SmobilPay API"))
            
        except Exception as e:
            raise UserError(_("Connection test failed: %s") % str(e))
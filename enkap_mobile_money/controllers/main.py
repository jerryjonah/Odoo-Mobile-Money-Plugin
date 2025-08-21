# -*- coding: utf-8 -*-

import json
import logging
import pprint
import werkzeug

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SmobilpayController(http.Controller):
    _callback_url = '/payment/smobilpay/callback'
    _return_url = '/payment/smobilpay/return'
    _webhook_url = '/payment/smobilpay/webhook'

    @http.route('/payment/smobilpay/callback/<string:merchant_reference>', 
                type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def smobilpay_callback(self, merchant_reference, **kwargs):
        """Handle payment callback from SmobilPay (similar to WordPress smobilpay-return.php)"""
        _logger.info("SmobilPay callback received for merchant reference: %s", merchant_reference)
        
        try:
            # Get transaction by merchant reference
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('smobilpay_merchant_reference', '=', merchant_reference)
            ], limit=1)
            
            if not tx_sudo:
                _logger.error("No transaction found for merchant reference: %s", merchant_reference)
                return request.redirect('/shop/cart')

            # Extract payment data from request (GET or POST)
            notification_data = dict(request.httprequest.args)
            if request.httprequest.method == 'POST':
                notification_data.update(request.httprequest.form.to_dict())
                
            # Add merchant reference to notification data
            notification_data['merchantReference'] = merchant_reference
            
            _logger.info("SmobilPay callback data: %s", pprint.pformat(notification_data))

            # Process the notification data
            if notification_data:
                tx_sudo._handle_notification_data('smobilpay', notification_data)
            
            # Redirect to appropriate page based on transaction state
            if tx_sudo.state == 'done':
                return request.redirect('/payment/status')
            elif tx_sudo.state in ['error', 'cancel']:
                return request.redirect('/shop/cart?payment_error=1')
            else:
                return request.redirect('/payment/status')
                
        except ValidationError as e:
            _logger.exception("Validation error in SmobilPay callback: %s", str(e))
            return request.redirect('/shop/cart?payment_error=1')
        except Exception as e:
            _logger.exception("Error processing SmobilPay callback: %s", str(e))
            return request.redirect('/shop/cart?payment_error=1')

    @http.route('/payment/smobilpay/return/<string:merchant_reference>',
                type='http', auth='public', methods=['GET'], csrf=False, save_session=False)
    def smobilpay_return(self, merchant_reference, **kwargs):
        """Handle customer return from SmobilPay payment page"""
        _logger.info("SmobilPay return received for merchant reference: %s", merchant_reference)
        
        try:
            # Get transaction
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('smobilpay_merchant_reference', '=', merchant_reference)
            ], limit=1)
            
            if not tx_sudo:
                _logger.error("No transaction found for merchant reference: %s", merchant_reference)
                return request.redirect('/shop/cart')

            # Handle return parameters (similar to WordPress plugin)
            status = kwargs.get('status', '').upper()
            payment_id = kwargs.get('paymentId', '')
            
            if status and payment_id:
                notification_data = {
                    'merchantReference': merchant_reference,
                    'status': status,
                    'paymentId': payment_id,
                    'statusMessage': kwargs.get('statusMessage', ''),
                }
                
                # Process notification data
                tx_sudo._handle_notification_data('smobilpay', notification_data)

            # Redirect based on transaction state
            return self._redirect_after_payment(tx_sudo)
            
        except Exception as e:
            _logger.exception("Error processing SmobilPay return: %s", str(e))
            return request.redirect('/shop/cart?payment_error=1')

    @http.route('/payment/smobilpay/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def smobilpay_webhook(self, **kwargs):
        """Handle SmobilPay webhook notifications (asynchronous status updates)"""
        _logger.info("SmobilPay webhook received")
        
        try:
            # Get webhook payload
            webhook_data = json.loads(request.httprequest.data)
            _logger.info("SmobilPay webhook data: %s", pprint.pformat(webhook_data))
            
            # Verify webhook signature if configured
            signature = request.httprequest.headers.get('X-SmobilPay-Signature', '')
            merchant_reference = webhook_data.get('merchantReference')
            
            if not merchant_reference:
                _logger.error("SmobilPay webhook missing merchant reference")
                return {'status': 'error', 'message': 'Missing merchant reference'}

            # Find transaction
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('smobilpay_merchant_reference', '=', merchant_reference)
            ], limit=1)
            
            if not tx_sudo:
                _logger.error("No transaction found for webhook merchant reference: %s", merchant_reference)
                return {'status': 'error', 'message': 'Transaction not found'}

            # Verify webhook signature if secret is configured
            if tx_sudo.provider_id.smobilpay_webhook_secret:
                if not tx_sudo._smobilpay_verify_webhook_signature(
                    request.httprequest.data.decode('utf-8'),
                    signature,
                    tx_sudo.provider_id.smobilpay_webhook_secret
                ):
                    _logger.error("SmobilPay webhook signature verification failed")
                    return {'status': 'error', 'message': 'Invalid signature'}

            # Process webhook data
            tx_sudo._handle_notification_data('smobilpay', webhook_data)
            
            return {'status': 'success', 'message': 'Webhook processed successfully'}
            
        except Exception as e:
            _logger.exception("Error processing SmobilPay webhook: %s", str(e))
            return {'status': 'error', 'message': str(e)}

    def _redirect_after_payment(self, tx_sudo):
        """Redirect customer after payment based on transaction state"""
        if tx_sudo.state == 'done':
            # Payment successful - redirect to success page
            return request.redirect('/payment/status')
        elif tx_sudo.state == 'cancel':
            # Payment cancelled - return to cart with message
            return request.redirect('/shop/cart?payment_cancelled=1')
        elif tx_sudo.state == 'error':
            # Payment failed - return to cart with error
            return request.redirect('/shop/cart?payment_error=1')
        else:
            # Payment pending - show status page
            return request.redirect('/payment/status')

    @http.route('/payment/smobilpay/test', type='http', auth='user', methods=['GET'])
    def smobilpay_test_connection(self, **kwargs):
        """Test SmobilPay API connection (admin only)"""
        if not request.env.user.has_group('base.group_system'):
            return werkzeug.exceptions.Forbidden()
            
        try:
            provider = request.env['payment.provider'].sudo().search([
                ('code', '=', 'smobilpay'), 
                ('state', '!=', 'disabled')
            ], limit=1)
            
            if not provider:
                return request.make_response("SmobilPay provider not found or disabled", 404)
            
            # Test API connection
            token = provider._smobilpay_get_access_token()
            if token:
                return request.make_response(
                    "<h2>SmobilPay Connection Test</h2>"
                    "<p style='color: green;'>✓ Successfully connected to SmobilPay API</p>"
                    f"<p>API URL: {provider._smobilpay_get_api_url()}</p>"
                    f"<p>Environment: {'Test' if provider.state == 'test' else 'Production'}</p>"
                )
            else:
                return request.make_response(
                    "<h2>SmobilPay Connection Test</h2>"
                    "<p style='color: red;'>✗ Failed to connect to SmobilPay API</p>",
                    500
                )
                
        except Exception as e:
            return request.make_response(
                f"<h2>SmobilPay Connection Test</h2>"
                f"<p style='color: red;'>✗ Connection failed: {str(e)}</p>",
                500
            )
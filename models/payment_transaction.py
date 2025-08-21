# -*- coding: utf-8 -*-

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # SmobilPay specific fields
    smobilpay_payment_id = fields.Char(
        string="SmobilPay Payment ID",
        help="Unique payment identifier from SmobilPay",
        readonly=True,
    )
    
    smobilpay_merchant_reference = fields.Char(
        string="Merchant Reference", 
        help="Unique merchant reference for this transaction",
        readonly=True,
    )
    
    smobilpay_payment_method = fields.Selection([
        ('mtn_cm', 'MTN Mobile Money'),
        ('orange_cm', 'Orange Mobile Money'), 
        ('express_union', 'Express Union Mobile Money'),
        ('smobilpay_cash', 'SmobilPay Cash'),
    ], string="Payment Method", readonly=True)
    
    smobilpay_phone_number = fields.Char(
        string="Phone Number",
        help="Customer's mobile money phone number",
    )
    
    smobilpay_status_details = fields.Text(
        string="Status Details",
        help="Detailed status information from SmobilPay",
        readonly=True,
    )

    def _get_specific_rendering_values(self, processing_values):
        """Return SmobilPay-specific rendering values"""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'smobilpay':
            return res

        # Generate unique merchant reference
        merchant_reference = str(uuid.uuid4())
        self.smobilpay_merchant_reference = merchant_reference
        
        # Get callback URL for payment notifications
        base_url = self.provider_id.get_base_url()
        callback_url = urls.url_join(base_url, f'/payment/smobilpay/callback/{merchant_reference}')
        return_url = urls.url_join(base_url, f'/payment/smobilpay/return/{merchant_reference}')
        
        # Register callback URL with SmobilPay
        self.provider_id._smobilpay_register_callback_url(callback_url)

        rendering_values = {
            'api_url': self.provider_id._smobilpay_get_api_url(),
            'consumer_key': self.provider_id.smobilpay_consumer_key,
            'merchant_reference': merchant_reference,
            'callback_url': callback_url,
            'return_url': return_url,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'customer_email': self.partner_email,
            'customer_name': self.partner_name,
            'transaction_reference': self.reference,
        }
        
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override to handle SmobilPay notifications"""
        if provider_code != 'smobilpay':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        merchant_reference = notification_data.get('merchantReference') or notification_data.get('reference')
        if not merchant_reference:
            raise ValidationError("SmobilPay: Missing merchant reference in notification data")

        tx = self.search([('smobilpay_merchant_reference', '=', merchant_reference)], limit=1)
        if not tx:
            raise ValidationError(f"SmobilPay: No transaction found for reference {merchant_reference}")

        return tx

    def _process_notification_data(self, notification_data):
        """Process SmobilPay notification data"""
        super()._process_notification_data(notification_data)
        
        if self.provider_code != 'smobilpay':
            return

        # Extract SmobilPay specific data
        self.smobilpay_payment_id = notification_data.get('paymentId', '')
        status = notification_data.get('status', '').upper()
        
        # Map SmobilPay statuses to Odoo transaction states
        status_mapping = {
            'CREATED': 'pending',
            'INITIALISED': 'pending', 
            'IN_PROGRESS': 'pending',
            'CONFIRMED': 'done',
            'FAILED': 'error',
            'CANCELED': 'cancel',
            'CANCELLED': 'cancel',
        }
        
        new_state = status_mapping.get(status, 'pending')
        
        # Update transaction details
        self.smobilpay_status_details = notification_data.get('statusMessage', '')
        
        if notification_data.get('phoneNumber'):
            self.smobilpay_phone_number = notification_data['phoneNumber']
            
        if notification_data.get('paymentMethod'):
            method_mapping = {
                'MTN_CM': 'mtn_cm',
                'ORANGE_CM': 'orange_cm', 
                'EXPRESS_UNION': 'express_union',
                'SMOBILPAY_CASH': 'smobilpay_cash',
            }
            self.smobilpay_payment_method = method_mapping.get(
                notification_data['paymentMethod'].upper(), 
                'mtn_cm'
            )

        # Update transaction state based on SmobilPay status
        if new_state == 'done':
            self._set_done()
        elif new_state == 'error':
            self._set_error(
                state_message=self.smobilpay_status_details or "Payment failed"
            )
        elif new_state == 'cancel':
            self._set_canceled(
                state_message=self.smobilpay_status_details or "Payment cancelled"
            )
        else:
            self._set_pending()

    def _smobilpay_create_payment_request(self):
        """Create payment request with SmobilPay API"""
        self.ensure_one()
        
        if not self.smobilpay_merchant_reference:
            self.smobilpay_merchant_reference = str(uuid.uuid4())

        # Prepare payment data
        payment_data = {
            'amount': int(self.amount * 100),  # Convert to cents
            'currency': self.currency_id.name,
            'merchantReference': self.smobilpay_merchant_reference,
            'description': f"Payment for order {self.reference}",
            'customerEmail': self.partner_email,
            'customerName': self.partner_name,
            'callbackUrl': self._get_callback_url(),
            'returnUrl': self._get_return_url(),
        }
        
        try:
            # Create payment request via API
            response = self.provider_id._smobilpay_make_request(
                '/api/order/create', payment_data, 'POST'
            )
            
            if response.get('status') == 'success' and response.get('paymentUrl'):
                self.smobilpay_payment_id = response.get('paymentId', '')
                return response['paymentUrl']
            else:
                raise UserError(_("Failed to create SmobilPay payment request"))
                
        except Exception as e:
            _logger.error("SmobilPay payment creation failed: %s", str(e))
            raise UserError(_("Payment creation failed: %s") % str(e))

    def _get_callback_url(self):
        """Generate callback URL for payment notifications"""
        base_url = self.provider_id.get_base_url()
        return urls.url_join(
            base_url, 
            f'/payment/smobilpay/callback/{self.smobilpay_merchant_reference}'
        )

    def _get_return_url(self):
        """Generate return URL after payment"""
        base_url = self.provider_id.get_base_url()
        return urls.url_join(
            base_url, 
            f'/payment/smobilpay/return/{self.smobilpay_merchant_reference}'
        )

    @api.model 
    def _smobilpay_verify_webhook_signature(self, payload, signature, secret):
        """Verify webhook signature from SmobilPay"""
        if not secret:
            _logger.warning("No webhook secret configured for signature verification")
            return True  # Skip verification if no secret is set
            
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    def _log_received_message(self, message, notification_data):
        """Override to log SmobilPay specific information"""
        super()._log_received_message(message, notification_data)
        
        if self.provider_code == 'smobilpay' and notification_data:
            _logger.info(
                "SmobilPay notification for transaction %s (ref: %s): Status=%s, PaymentID=%s",
                self.reference,
                self.smobilpay_merchant_reference,
                notification_data.get('status', 'Unknown'),
                notification_data.get('paymentId', 'None')
            )
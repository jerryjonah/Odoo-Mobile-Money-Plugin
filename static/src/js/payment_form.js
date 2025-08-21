/* global $ */
odoo.define('smobilpay_odoo_gateway.payment_form', function (require) {
    'use strict';

    const core = require('web.core');
    const Dialog = require('web.Dialog');
    const publicWidget = require('web.public.widget');

    const _t = core._t;

    /**
     * SmobilPay Payment Form Widget
     */
    publicWidget.registry.SmobilpayPaymentForm = publicWidget.Widget.extend({
        selector: '.smobilpay-payment-form',
        events: {
            'change #smobilpay_phone': '_onPhoneChange',
            'change #smobilpay_method': '_onMethodChange',
            'submit': '_onSubmit',
        },

        start: function () {
            this._super.apply(this, arguments);
            this._setupValidation();
            return Promise.resolve();
        },

        /**
         * Setup form validation
         */
        _setupValidation: function () {
            this.phoneInput = this.$('#smobilpay_phone');
            this.methodSelect = this.$('#smobilpay_method');
            
            // Add validation attributes
            this.phoneInput.attr('pattern', '[0-9]{9}');
            this.phoneInput.attr('title', 'Enter a valid 9-digit phone number');
        },

        /**
         * Handle phone number input changes
         */
        _onPhoneChange: function (ev) {
            const phone = $(ev.currentTarget).val();
            const isValid = this._validatePhone(phone);
            
            if (phone && !isValid) {
                this._showFieldError($(ev.currentTarget), _t('Please enter a valid phone number (9 digits)'));
            } else {
                this._clearFieldError($(ev.currentTarget));
            }
            
            this._updateSubmitButton();
        },

        /**
         * Handle payment method selection changes  
         */
        _onMethodChange: function (ev) {
            const method = $(ev.currentTarget).val();
            
            if (method) {
                this._clearFieldError($(ev.currentTarget));
                this._updatePaymentMethodInfo(method);
            }
            
            this._updateSubmitButton();
        },

        /**
         * Handle form submission
         */
        _onSubmit: function (ev) {
            ev.preventDefault();
            
            const phone = this.phoneInput.val();
            const method = this.methodSelect.val();
            
            if (!this._validateForm(phone, method)) {
                return false;
            }
            
            this._showLoadingState();
            this._createPaymentRequest(phone, method);
        },

        /**
         * Validate phone number format
         */
        _validatePhone: function (phone) {
            // Remove spaces and special characters
            const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
            
            // Check if it's a valid Cameroon phone number (9 digits)
            return /^[0-9]{9}$/.test(cleanPhone);
        },

        /**
         * Validate entire form
         */
        _validateForm: function (phone, method) {
            let isValid = true;
            
            // Validate phone number
            if (!phone || !this._validatePhone(phone)) {
                this._showFieldError(this.phoneInput, _t('Please enter a valid phone number'));
                isValid = false;
            }
            
            // Validate payment method
            if (!method) {
                this._showFieldError(this.methodSelect, _t('Please select a payment method'));
                isValid = false;
            }
            
            return isValid;
        },

        /**
         * Show field-specific error
         */
        _showFieldError: function ($field, message) {
            $field.addClass('smobilpay-error');
            
            // Remove existing error message
            $field.parent().find('.smobilpay-error-message').remove();
            
            // Add new error message
            $field.parent().append(
                $('<div class="smobilpay-error-message">').text(message)
            );
        },

        /**
         * Clear field error
         */
        _clearFieldError: function ($field) {
            $field.removeClass('smobilpay-error');
            $field.parent().find('.smobilpay-error-message').remove();
        },

        /**
         * Update payment method information
         */
        _updatePaymentMethodInfo: function (method) {
            const methodInfo = {
                'mtn_cm': {
                    name: 'MTN Mobile Money',
                    prefix: '67, 68',
                    color: '#FFD700'
                },
                'orange_cm': {
                    name: 'Orange Mobile Money', 
                    prefix: '69, 65',
                    color: '#FF8C00'
                },
                'express_union': {
                    name: 'Express Union',
                    prefix: '67, 68, 69',
                    color: '#4169E1'
                },
                'smobilpay_cash': {
                    name: 'SmobilPay Cash',
                    prefix: 'Any number',
                    color: '#32CD32'
                }
            };
            
            const info = methodInfo[method];
            if (info) {
                this.phoneInput.attr('placeholder', `Enter ${info.prefix} number`);
                this.phoneInput.attr('title', `Valid prefixes for ${info.name}: ${info.prefix}`);
            }
        },

        /**
         * Update submit button state
         */
        _updateSubmitButton: function () {
            const phone = this.phoneInput.val();
            const method = this.methodSelect.val();
            const isFormValid = this._validatePhone(phone) && method;
            
            const $submitBtn = this.$('button[type="submit"], input[type="submit"]');
            $submitBtn.prop('disabled', !isFormValid);
            
            if (isFormValid) {
                $submitBtn.removeClass('btn-secondary').addClass('btn-success');
                $submitBtn.text(_t('Pay with Mobile Money'));
            } else {
                $submitBtn.removeClass('btn-success').addClass('btn-secondary');
                $submitBtn.text(_t('Complete form to continue'));
            }
        },

        /**
         * Show loading state during payment processing
         */
        _showLoadingState: function () {
            this.$el.addClass('smobilpay-loading');
            
            const $submitBtn = this.$('button[type="submit"], input[type="submit"]');
            $submitBtn.prop('disabled', true);
            $submitBtn.html('<i class="fa fa-spinner fa-spin"></i> ' + _t('Processing...'));
        },

        /**
         * Create payment request with SmobilPay
         */
        _createPaymentRequest: function (phone, method) {
            const paymentData = {
                phone: phone,
                method: method,
                merchant_reference: this.$('input[name="merchant_reference"]').val(),
                amount: this.$('input[name="amount"]').val(),
                currency: this.$('input[name="currency"]').val(),
            };
            
            // Make AJAX request to create payment
            $.ajax({
                url: '/payment/smobilpay/create',
                method: 'POST',
                data: paymentData,
                dataType: 'json',
                success: this._onPaymentRequestSuccess.bind(this),
                error: this._onPaymentRequestError.bind(this)
            });
        },

        /**
         * Handle successful payment request creation
         */
        _onPaymentRequestSuccess: function (response) {
            if (response.status === 'success' && response.payment_url) {
                // Redirect to SmobilPay payment page
                window.location.href = response.payment_url;
            } else {
                this._onPaymentRequestError({
                    responseJSON: {
                        error: response.message || _t('Failed to create payment request')
                    }
                });
            }
        },

        /**
         * Handle payment request errors
         */
        _onPaymentRequestError: function (xhr) {
            this.$el.removeClass('smobilpay-loading');
            
            const errorMessage = xhr.responseJSON && xhr.responseJSON.error 
                ? xhr.responseJSON.error 
                : _t('Payment request failed. Please try again.');
                
            // Show error dialog
            Dialog.alert(this, errorMessage, {
                title: _t('Payment Error'),
                confirm_callback: () => {
                    // Reset form
                    const $submitBtn = this.$('button[type="submit"], input[type="submit"]');
                    $submitBtn.prop('disabled', false);
                    $submitBtn.text(_t('Pay with Mobile Money'));
                }
            });
        }
    });

    /**
     * Payment Status Page Widget
     */
    publicWidget.registry.SmobilpayPaymentStatus = publicWidget.Widget.extend({
        selector: '.payment-status-container',

        start: function () {
            this._super.apply(this, arguments);
            this._checkPaymentStatus();
            return Promise.resolve();
        },

        /**
         * Periodically check payment status for pending transactions
         */
        _checkPaymentStatus: function () {
            const $alert = this.$('.alert-warning');
            if ($alert.length > 0) {
                // Payment is pending, check status every 5 seconds
                setTimeout(() => {
                    window.location.reload();
                }, 5000);
            }
        }
    });

    return {
        SmobilpayPaymentForm: publicWidget.registry.SmobilpayPaymentForm,
        SmobilpayPaymentStatus: publicWidget.registry.SmobilpayPaymentStatus,
    };
});
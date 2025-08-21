# SmobilPay Mobile Money Gateway for Odoo

A comprehensive mobile money payment gateway addon for Odoo that enables seamless payment processing across Cameroon and the CEMAC region through SmobilPay's secure platform.

## Features

### Payment Methods Supported
- **MTN Mobile Money Cameroon** - Leading mobile money service
- **Orange Mobile Money Cameroon** - Comprehensive coverage
- **Express Union Mobile Money** - Wide network reach
- **SmobilPay Cash** - Universal payment option

### Key Capabilities
- ✅ **Automatic Callback Handling** - No manual configuration needed
- ✅ **Dual Environment Support** - Test and production modes
- ✅ **Real-time Payment Status** - Instant transaction updates
- ✅ **Secure OAuth 2.0** - Enterprise-grade authentication
- ✅ **Multi-currency Support** - XAF, EUR, USD compatible
- ✅ **Comprehensive Logging** - Full audit trail
- ✅ **Mobile-Optimized Forms** - Responsive payment interface
- ✅ **Webhook Integration** - Asynchronous status updates

## Installation

### Method 1: Odoo App Store (Recommended)
1. Go to Odoo Apps in your instance
2. Search for "SmobilPay Mobile Money Gateway"
3. Click Install
4. Configure your API credentials

### Method 2: Manual Installation
1. Download the addon files
2. Copy `smobilpay_odoo_gateway` folder to your Odoo addons directory
3. Update app list: Settings → Apps → Update Apps List
4. Search for "SmobilPay Mobile Money Gateway" and install

### Method 3: Development Installation
```bash
# Clone repository
git clone https://github.com/your-repo/smobilpay-odoo-gateway.git

# Copy to Odoo addons directory
cp -r smobilpay_odoo_gateway /opt/odoo/addons/

# Restart Odoo service
sudo systemctl restart odoo

# Update app list and install via Odoo interface
```

## Configuration

### 1. API Credentials Setup
1. Navigate to **Settings → Payment Providers**
2. Find **SmobilPay Mobile Money** and click Configure
3. Enter your credentials:
   - **Consumer Key**: Your SmobilPay API consumer key
   - **Consumer Secret**: Your SmobilPay API consumer secret  
   - **Webhook Secret**: (Optional) For webhook signature verification

### 2. Environment Configuration
- **Test Mode**: Uses staging environment for testing
- **Production Mode**: Live payment processing

### 3. Currency Support
Configure supported currencies:
- Primary: **XAF (Central African Franc)**
- Additional: **EUR, USD**

### 4. Country Restrictions
Optimized for CEMAC region:
- Cameroon, Chad, Central African Republic
- Republic of Congo, Gabon, Equatorial Guinea

## Usage

### For Customers
1. **Select SmobilPay** at checkout
2. **Choose payment method** (MTN, Orange, Express Union, or SmobilPay Cash)
3. **Enter phone number** for mobile money account
4. **Complete payment** by following mobile prompts
5. **Receive confirmation** automatically in Odoo

### Payment Flow
```
Customer Checkout → SmobilPay Selection → Phone/Method Entry → 
Mobile Money Prompt → PIN Entry → Payment Confirmation → Order Success
```

### For Administrators
- **Monitor transactions** in Accounting → Payment Transactions
- **View payment details** including phone numbers and methods
- **Track payment status** with real-time updates
- **Generate reports** for mobile money payments
- **Test connections** with built-in API testing

## Technical Architecture

### Core Components
- **Payment Provider Model** - Handles API integration and configuration
- **Payment Transaction Model** - Manages transaction lifecycle
- **Controller Layer** - Processes callbacks and webhooks
- **Frontend Templates** - Mobile-optimized payment forms
- **JavaScript Widgets** - Enhanced user experience

### API Integration
- **OAuth 2.0 Authentication** with automatic token management
- **RESTful API Communication** with SmobilPay platform
- **Webhook Processing** for real-time status updates
- **Error Handling** with comprehensive logging

### Security Features
- **Input Sanitization** for all user data
- **HMAC Signature Verification** for webhooks
- **Secure Token Storage** with Odoo's encryption
- **CSRF Protection** on all forms
- **SSL/TLS Enforcement** for API communications

## Troubleshooting

### Common Issues

#### Connection Errors
```python
# Test API connection
provider = env['payment.provider'].search([('code', '=', 'smobilpay')])
provider.action_test_smobilpay_connection()
```

#### Payment Status Not Updating
1. Check webhook URL registration
2. Verify callback URL accessibility
3. Review server logs for errors

#### Invalid Phone Numbers
- Ensure 9-digit format (without country code)
- Validate against provider prefixes:
  - MTN: 67, 68
  - Orange: 69, 65
  - Express Union: 67, 68, 69

### Debug Mode
Enable debug logging in configuration:
```python
# In payment provider form
self.env['ir.logging'].create({
    'name': 'smobilpay.debug',
    'level': 'DEBUG',
    'message': 'Payment processing details...'
})
```

## Development

### Extending the Addon
```python
# Custom payment method validation
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _smobilpay_validate_phone(self, phone, method):
        # Custom validation logic
        return super()._smobilpay_validate_phone(phone, method)
```

### Webhook Customization
```python
# Custom webhook processing
@http.route('/payment/smobilpay/webhook/custom', type='json', auth='public')
def custom_webhook(self, **kwargs):
    # Custom webhook logic
    return {'status': 'success'}
```

## Compatibility

- **Odoo Versions**: 15.0, 16.0, 17.0+
- **Python**: 3.8+
- **Dependencies**: `payment`, `website_sale`
- **Browsers**: Chrome, Firefox, Safari, Edge (mobile optimized)

## Support

### Getting Help
- **Documentation**: Complete setup guides and API reference
- **Issue Tracker**: Report bugs and feature requests
- **Community Forum**: Connect with other users
- **Professional Support**: Enterprise support available

### API Credentials
To get SmobilPay API credentials:
1. Visit [SmobilPay Registration](https://enkap.cm/)
2. Complete merchant account setup
3. Request API keys from support team
4. Test in sandbox environment first

## License

This addon is licensed under **GPL-3.0** - see LICENSE file for details.

## Changelog

### Version 2.1.5 (Latest)
- ✅ Enhanced callback URL handling with multiple format support
- ✅ Improved test mode compatibility
- ✅ Real-time payment status updates
- ✅ Mobile-optimized payment forms
- ✅ Comprehensive error handling
- ✅ Webhook signature verification
- ✅ Multi-currency support enhancements

### Previous Versions
See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

**Built by Maviance PLC** - Enabling digital payments across Africa
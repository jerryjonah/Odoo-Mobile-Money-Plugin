# Changelog

All notable changes to the SmobilPay Odoo Gateway addon will be documented in this file.

## [2.1.5] - 2025-08-20

### Added
- Initial release of SmobilPay Mobile Money Gateway for Odoo
- Payment provider integration with SmobilPay API
- Support for MTN, Orange, Express Union, and SmobilPay Cash
- OAuth 2.0 authentication with automatic token management
- Automatic callback URL registration with multiple format support
- Real-time payment status updates via webhooks
- Mobile-optimized payment forms with JavaScript validation
- Multi-currency support (XAF, EUR, USD)
- Comprehensive transaction tracking and logging
- Test and production environment configurations
- HMAC webhook signature verification
- Responsive payment form design
- Administrative tools for connection testing
- Complete error handling and user feedback
- Integration with Odoo's payment transaction system
- CEMAC region country support
- Phone number validation for different mobile money providers

### Features
- **Payment Processing**: Seamless mobile money transaction handling
- **Security**: Enterprise-grade OAuth 2.0 and webhook verification
- **User Experience**: Mobile-first responsive design
- **Administration**: Easy configuration and monitoring tools
- **Compliance**: Full audit trail and transaction logging
- **Scalability**: Optimized for high-volume transaction processing

### Technical Implementation
- Modern Odoo addon architecture following best practices
- RESTful API integration with SmobilPay platform
- Asynchronous webhook processing for real-time updates
- Comprehensive input validation and sanitization
- Error handling with graceful degradation
- Extensible design for future enhancements

### Compatibility
- Odoo 15.0, 16.0, 17.0+
- Python 3.8+
- Modern web browsers with mobile optimization
- CEMAC region mobile money networks

## Planned Features

### [2.2.0] - Future Release
- Enhanced reporting and analytics dashboard
- Bulk payment processing capabilities
- Advanced fraud detection mechanisms
- Multi-language support (French, English)
- Custom payment method configurations
- Integration with additional mobile money providers
- Advanced webhook retry mechanisms
- Payment link generation for invoices

### [2.3.0] - Future Release
- Subscription and recurring payment support
- Advanced customer payment preferences
- Integration with Odoo accounting modules
- Custom payment workflows
- Enhanced mobile app compatibility
- Payment QR code generation
- Advanced settlement reporting
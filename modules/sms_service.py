"""
SMS Service Module

Handles SMS sending via Twilio for verification codes and notifications.
Includes development mode for testing without actual SMS sending.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import os
from typing import Optional


class SMSService:
    """
    SMS service for sending verification codes and notifications.
    
    Uses Twilio in production, console output in development.
    """
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None,
                 phone_number: Optional[str] = None):
        """
        Initialize SMS service.
        
        Args:
            account_sid: Twilio Account SID (optional, uses env var if not provided)
            auth_token: Twilio Auth Token (optional, uses env var if not provided)
            phone_number: Twilio phone number (optional, uses env var if not provided)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = phone_number or os.getenv('TWILIO_PHONE_NUMBER')
        self.dev_mode = not (self.account_sid and self.auth_token and self.phone_number)
        
        if self.dev_mode:
            print("📱 SMSService: Running in DEVELOPMENT MODE (console output only)")
        else:
            print("📱 SMSService: Running in PRODUCTION MODE (Twilio enabled)")
    
    def send_verification_code(self, to_phone: str, code: str) -> bool:
        """
        Send SMS verification code.
        
        Args:
            to_phone: Recipient phone number
            code: 6-digit verification code
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"Your Luggage Room Boys Fund verification code: {code}\n\nThis code expires in 10 minutes."
        
        return self._send_sms(to_phone, message)
    
    def send_invitation_notification(self, to_phone: str, invited_by_name: str) -> bool:
        """
        Send SMS notification about invitation.
        
        Args:
            to_phone: Recipient phone number
            invited_by_name: Name of person who sent invite
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"You've been invited by {invited_by_name} to join The Luggage Room Boys Fund. Check your email for details."
        
        return self._send_sms(to_phone, message)
    
    def send_welcome_sms(self, to_phone: str, first_name: str) -> bool:
        """
        Send welcome SMS after successful signup.
        
        Args:
            to_phone: New user's phone number
            first_name: New user's first name
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"Welcome to LRBF, {first_name}! Your account is now active. Log in to access your dashboard."
        
        return self._send_sms(to_phone, message)
    
    def send_transaction_alert(self, to_phone: str, transaction_type: str, amount: float) -> bool:
        """
        Send SMS alert about capital transaction.
        
        Args:
            to_phone: User's phone number
            transaction_type: 'contribution', 'distribution', or 'withdrawal'
            amount: Transaction amount
            
        Returns:
            bool: True if SMS sent successfully
        """
        transaction_label = {
            'contribution': 'Contribution',
            'distribution': 'Distribution',
            'withdrawal': 'Withdrawal'
        }.get(transaction_type, transaction_type.capitalize())
        
        message = f"LRBF: {transaction_label} of ${amount:,.2f} recorded. Check your email for details."
        
        return self._send_sms(to_phone, message)
    
    def send_admin_alert(self, to_phone: str, alert_message: str) -> bool:
        """
        Send admin alert SMS.
        
        Args:
            to_phone: Admin's phone number
            alert_message: Alert message
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"LRBF ADMIN ALERT: {alert_message}"
        
        return self._send_sms(to_phone, message)
    
    def send_new_cofounder_alert(self, to_phone: str, new_cofounder_name: str) -> bool:
        """
        Alert existing co-founders about new member.
        
        Args:
            to_phone: Co-founder's phone number
            new_cofounder_name: Name of new co-founder
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"LRBF: {new_cofounder_name} has joined the fund as a co-founder."
        
        return self._send_sms(to_phone, message)
    
    def send_password_reset_code(self, to_phone: str, code: str) -> bool:
        """
        Send password reset verification code.
        
        Args:
            to_phone: User's phone number
            code: 6-digit verification code
            
        Returns:
            bool: True if SMS sent successfully
        """
        message = f"Your LRBF password reset code: {code}\n\nThis code expires in 10 minutes. If you didn't request this, ignore this message."
        
        return self._send_sms(to_phone, message)
    
    def _send_sms(self, to_phone: str, message: str) -> bool:
        """
        Internal method to send SMS via Twilio or console.
        
        Args:
            to_phone: Recipient phone number
            message: SMS message content
            
        Returns:
            bool: True if successful
        """
        if self.dev_mode:
            # Development mode - print to console
            print("\n" + "="*70)
            print("📱 SMS SENT (Development Mode)")
            print("="*70)
            print(f"To: {to_phone}")
            print(f"From: {self.phone_number or 'LRBF'}")
            print("-"*70)
            print(message)
            print("="*70 + "\n")
            return True
        
        else:
            # Production mode - send via Twilio
            try:
                from twilio.rest import Client
                
                client = Client(self.account_sid, self.auth_token)
                
                message = client.messages.create(
                    body=message,
                    from_=self.phone_number,
                    to=to_phone
                )
                
                if message.sid:
                    print(f"✅ SMS sent successfully to {to_phone} (SID: {message.sid})")
                    return True
                else:
                    print(f"⚠️ SMS send returned no SID for {to_phone}")
                    return False
                
            except Exception as e:
                print(f"❌ Failed to send SMS to {to_phone}: {e}")
                return False
    
    def validate_phone_format(self, phone: str) -> bool:
        """
        Validate phone number format for SMS.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if valid format
        """
        import re
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Must start with + for international format
        if not phone.startswith('+'):
            return False
        
        # Must be all digits after the +
        if not cleaned[1:].isdigit():
            return False
        
        # Must be reasonable length (10-15 digits after +)
        if len(cleaned) < 11 or len(cleaned) > 16:
            return False
        
        return True


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SMS SERVICE - TESTING")
    print("="*70 + "\n")
    
    # Initialize in dev mode
    sms_service = SMSService()
    
    # Test verification code
    print("1. Testing verification code...")
    success = sms_service.send_verification_code(
        to_phone="+1-555-123-4567",
        code="123456"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test invitation notification
    print("\n2. Testing invitation notification...")
    success = sms_service.send_invitation_notification(
        to_phone="+1-555-123-4567",
        invited_by_name="John Smith"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test welcome SMS
    print("\n3. Testing welcome SMS...")
    success = sms_service.send_welcome_sms(
        to_phone="+1-555-123-4567",
        first_name="Hugo"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test transaction alert
    print("\n4. Testing transaction alert...")
    success = sms_service.send_transaction_alert(
        to_phone="+1-555-123-4567",
        transaction_type="contribution",
        amount=5000.00
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test admin alert
    print("\n5. Testing admin alert...")
    success = sms_service.send_admin_alert(
        to_phone="+1-555-123-4567",
        alert_message="Daily loss limit reached"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test new co-founder alert
    print("\n6. Testing new co-founder alert...")
    success = sms_service.send_new_cofounder_alert(
        to_phone="+1-555-123-4567",
        new_cofounder_name="Hugo Martinez"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test password reset code
    print("\n7. Testing password reset code...")
    success = sms_service.send_password_reset_code(
        to_phone="+1-555-123-4567",
        code="789012"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test phone validation
    print("\n8. Testing phone validation...")
    valid_phones = ["+15551234567", "+442071234567"]
    invalid_phones = ["5551234567", "+1555", "not-a-phone"]
    
    for phone in valid_phones:
        result = sms_service.validate_phone_format(phone)
        print(f"   {phone}: {'✅ Valid' if result else '❌ Invalid'}")
    
    for phone in invalid_phones:
        result = sms_service.validate_phone_format(phone)
        print(f"   {phone}: {'✅ Valid' if result else '❌ Invalid (expected)'}")
    
    print("\n✅ All SMS service tests completed!")

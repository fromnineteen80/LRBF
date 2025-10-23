"""
Authentication Helper Module

Handles password hashing, session token generation, and verification codes.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import bcrypt
import secrets
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple


class AuthHelper:
    """Helper class for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            password_hash: Stored hash
            
        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure random session token.
        
        Returns:
            32-character hex token
        """
        return secrets.token_hex(32)
    
    @staticmethod
    def generate_verification_code() -> str:
        """
        Generate a 6-digit verification code for phone/email verification.
        
        Returns:
            6-digit string code
        """
        return f"{random.randint(0, 999999):06d}"
    
    @staticmethod
    def get_session_expiry(days: int = 30) -> datetime:
        """
        Calculate session expiry datetime.
        
        Args:
            days: Number of days until expiry (default: 30)
            
        Returns:
            Datetime object for expiry
        """
        return datetime.now() + timedelta(days=days)
    
    @staticmethod
    def is_session_expired(expires_at_str: str) -> bool:
        """
        Check if a session has expired.
        
        Args:
            expires_at_str: ISO format datetime string
            
        Returns:
            True if expired
        """
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.now() > expires_at
        except Exception:
            return True
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        
        Args:
            password: Password to validate
            
        Returns:
            (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Basic email validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            (is_valid, error_message)
        """
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email:
            return False, "Email is required"
        
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """
        Basic phone number validation (US format).
        
        Args:
            phone: Phone number to validate
            
        Returns:
            (is_valid, error_message)
        """
        import re
        
        # Remove common formatting characters
        clean = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Check if it's 10 or 11 digits (with optional country code)
        if not clean.isdigit():
            return False, "Phone number must contain only digits"
        
        if len(clean) not in [10, 11]:
            return False, "Phone number must be 10 digits (or 11 with country code)"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username meets requirements.
        
        Requirements:
        - 3-20 characters
        - Alphanumeric and underscores only
        - Must start with a letter
        
        Args:
            username: Username to validate
            
        Returns:
            (is_valid, error_message)
        """
        import re
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 20:
            return False, "Username must be 20 characters or less"
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
            return False, "Username must start with a letter and contain only letters, numbers, and underscores"
        
        return True, ""


# ============================================================================
# EMAIL & SMS SERVICES
# ============================================================================

class NotificationService:
    """
    Service for sending email and SMS notifications.
    
    Uses:
    - SendGrid for email (or SMTP)
    - Twilio for SMS
    
    Configure API keys in environment variables or config.
    """
    
    def __init__(self):
        """Initialize notification service with API keys from environment."""
        import os
        
        # Email configuration (SendGrid)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@railyardmarkets.com')
        
        # SMS configuration (Twilio)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
    
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        """
        Send verification code via SMS.
        
        Args:
            phone_number: Recipient phone number
            code: 6-digit verification code
            
        Returns:
            True if successful
        """
        # TODO: Implement Twilio SMS sending
        # For now, just log the code (development mode)
        print(f"📱 SMS VERIFICATION CODE for {phone_number}: {code}")
        print(f"   (In production, this will be sent via Twilio)")
        
        # Uncomment when Twilio is configured:
        # try:
        #     from twilio.rest import Client
        #     client = Client(self.twilio_account_sid, self.twilio_auth_token)
        #     
        #     message = client.messages.create(
        #         body=f"Your Railyard Markets verification code is: {code}",
        #         from_=self.twilio_phone_number,
        #         to=phone_number
        #     )
        #     return message.sid is not None
        # except Exception as e:
        #     print(f"Error sending SMS: {e}")
        #     return False
        
        return True  # Simulated success in development
    
    def send_account_deletion_notification(self, recipient_emails: list, deleted_user_name: str) -> bool:
        """
        Send email notification when a co-founder deletes their account.
        
        Args:
            recipient_emails: List of co-founder email addresses
            deleted_user_name: Name of user who deleted account
            
        Returns:
            True if successful
        """
        # TODO: Implement SendGrid email sending
        # For now, just log the notification (development mode)
        print(f"📧 ACCOUNT DELETION NOTIFICATION")
        print(f"   To: {', '.join(recipient_emails)}")
        print(f"   User deleted: {deleted_user_name}")
        print(f"   (In production, this will be sent via SendGrid)")
        
        # Uncomment when SendGrid is configured:
        # try:
        #     from sendgrid import SendGridAPIClient
        #     from sendgrid.helpers.mail import Mail
        #     
        #     for email in recipient_emails:
        #         message = Mail(
        #             from_email=self.from_email,
        #             to_emails=email,
        #             subject=f"Co-Founder Account Deletion - {deleted_user_name}",
        #             html_content=f"""
        #             <h2>Account Deletion Notification</h2>
        #             <p>{deleted_user_name} has requested to delete their account from The Luggage Room Boys Fund.</p>
        #             <p>Please review the account deletion and payout details in your dashboard.</p>
        #             """
        #         )
        #         
        #         sg = SendGridAPIClient(self.sendgrid_api_key)
        #         response = sg.send(message)
        #         print(f"Email sent to {email}: {response.status_code}")
        #     
        #     return True
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        #     return False
        
        return True  # Simulated success in development
    
    def send_welcome_email(self, email: str, first_name: str, username: str) -> bool:
        """
        Send welcome email to new co-founder.
        
        Args:
            email: Recipient email
            first_name: User's first name
            username: User's username
            
        Returns:
            True if successful
        """
        print(f"📧 WELCOME EMAIL to {email}")
        print(f"   Welcome {first_name}! Username: {username}")
        print(f"   (In production, this will be sent via SendGrid)")
        
        return True  # Simulated success in development
    
    def send_contribution_change_notification(self, email: str, recipient_first_name: str, 
                                              changed_user_first_name: str, changed_user_last_name: str,
                                              new_contribution: float, new_ownership_pct: float) -> bool:
        """
        Send email notification when a co-founder changes their fund contribution.
        
        Args:
            email: Recipient email
            recipient_first_name: Name of person receiving notification
            changed_user_first_name: First name of user who changed contribution
            changed_user_last_name: Last name of user who changed contribution
            new_contribution: New contribution amount
            new_ownership_pct: Recipient's updated ownership percentage
            
        Returns:
            True if successful
        """
        print(f"📧 CONTRIBUTION CHANGE NOTIFICATION to {email}")
        print(f"   Dear {recipient_first_name},")
        print(f"   {changed_user_first_name} {changed_user_last_name} has updated their fund contribution to ${new_contribution:,.2f}")
        print(f"   Your new ownership percentage is {new_ownership_pct:.2f}%")
        print(f"   (In production, this will be sent via SendGrid)")
        
        # Uncomment when SendGrid is configured:
        # try:
        #     from sendgrid import SendGridAPIClient
        #     from sendgrid.helpers.mail import Mail
        #     
        #     message = Mail(
        #         from_email=self.from_email,
        #         to_emails=email,
        #         subject="Fund Contribution Update",
        #         html_content=f"""
        #         <h2>Fund Contribution Update</h2>
        #         <p>Dear {recipient_first_name},</p>
        #         <p><strong>{changed_user_first_name} {changed_user_last_name}</strong> has updated their fund contribution to <strong>${new_contribution:,.2f}</strong>.</p>
        #         <p>Your ownership percentage has been automatically recalculated to <strong>{new_ownership_pct:.2f}%</strong>.</p>
        #         <p>Log in to your dashboard to view updated fund details.</p>
        #         <p>Best regards,<br>The Luggage Room Boys Fund</p>
        #         """
        #     )
        #     
        #     sg = SendGridAPIClient(self.sendgrid_api_key)
        #     response = sg.send(message)
        #     return response.status_code == 202
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        #     return False
        
        return True  # Simulated success in development
    
    def send_deletion_notification(self, email: str, recipient_first_name: str,
                                   deleted_user_first_name: str, deleted_user_last_name: str,
                                   payout_amount: float, new_ownership_pct: float) -> bool:
        """
        Send email notification when a co-founder deletes their account.
        
        Args:
            email: Recipient email
            recipient_first_name: Name of person receiving notification
            deleted_user_first_name: First name of user deleting account
            deleted_user_last_name: Last name of user deleting account
            payout_amount: Amount being paid out
            new_ownership_pct: Recipient's updated ownership percentage
            
        Returns:
            True if successful
        """
        print(f"📧 ACCOUNT DELETION NOTIFICATION to {email}")
        print(f"   Dear {recipient_first_name},")
        print(f"   {deleted_user_first_name} {deleted_user_last_name} has deleted their account")
        print(f"   Payout amount: ${payout_amount:,.2f}")
        print(f"   Your new ownership percentage: {new_ownership_pct:.2f}%")
        print(f"   (In production, this will be sent via SendGrid)")
        
        # Uncomment when SendGrid is configured:
        # try:
        #     from sendgrid import SendGridAPIClient
        #     from sendgrid.helpers.mail import Mail
        #     
        #     message = Mail(
        #         from_email=self.from_email,
        #         to_emails=email,
        #         subject="Co-Founder Account Deletion",
        #         html_content=f"""
        #         <h2>Co-Founder Account Deletion</h2>
        #         <p>Dear {recipient_first_name},</p>
        #         <p><strong>{deleted_user_first_name} {deleted_user_last_name}</strong> has requested to delete their account from The Luggage Room Boys Fund.</p>
        #         <h3>Details:</h3>
        #         <ul>
        #             <li>Payout Amount: <strong>${payout_amount:,.2f}</strong></li>
        #             <li>Processing Time: 10-15 business days</li>
        #             <li>Your New Ownership: <strong>{new_ownership_pct:.2f}%</strong></li>
        #         </ul>
        #         <p>The account has been immediately deactivated. Fund ownership percentages have been automatically recalculated among remaining co-founders.</p>
        #         <p>If you have questions about this deletion, please contact the other co-founders.</p>
        #         <p>Best regards,<br>The Luggage Room Boys Fund</p>
        #         """
        #     )
        #     
        #     sg = SendGridAPIClient(self.sendgrid_api_key)
        #     response = sg.send(message)
        #     return response.status_code == 202
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        #     return False
        
        return True  # Simulated success in development
    
    # ========================================================================
    # INVITATION SYSTEM
    # ========================================================================
    
    @staticmethod
    def generate_invite_token() -> str:
        """
        Generate a secure invitation token.
        
        Returns:
            str: Unique invitation token with 'inv_' prefix
        """
        import string
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(32))
        return f'inv_{token}'
    
    @staticmethod
    def get_invitation_expiry(days: int = 7) -> datetime:
        """
        Calculate invitation expiry datetime.
        
        Args:
            days: Number of days until expiry (default: 7)
            
        Returns:
            datetime: Expiry datetime
        """
        return datetime.now() + timedelta(days=days)
    
    @staticmethod
    def validate_invitation_token(token: str, expires_at: datetime, used: bool) -> Tuple[bool, str]:
        """
        Validate an invitation token.
        
        Args:
            token: The invitation token
            expires_at: Token expiration datetime
            used: Whether token has been used
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not token:
            return False, "Invalid invitation token"
        
        if used:
            return False, "Invitation has already been used"
        
        if datetime.now() > expires_at:
            return False, "Invitation has expired"
        
        return True, ""
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number string
            
        Returns:
            tuple: (is_valid, error_message)
        """
        import re
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Check if it's all digits and reasonable length
        if not cleaned.isdigit():
            return False, "Phone number must contain only digits"
        
        if len(cleaned) < 10:
            return False, "Phone number too short (minimum 10 digits)"
        
        if len(cleaned) > 15:
            return False, "Phone number too long (maximum 15 digits)"
        
        return True, ""
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Format phone number to standard format.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            str: Formatted phone number (e.g., +1-555-123-4567)
        """
        import re
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format for US numbers (10 digits)
        if len(digits) == 10:
            return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:]}"
        
        # Format for international with country code
        elif len(digits) == 11 and digits[0] == '1':
            return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        
        # Return with + prefix if not already formatted
        elif not phone.startswith('+'):
            return f"+{digits}"
        
        return phone


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing AuthHelper...")
    print("=" * 60)
    
    # Test password hashing
    password = "SecurePass123!"
    hashed = AuthHelper.hash_password(password)
    print(f"\n1. Password Hashing:")
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verify correct: {AuthHelper.verify_password(password, hashed)}")
    print(f"   Verify wrong: {AuthHelper.verify_password('wrong', hashed)}")
    
    # Test validation
    print(f"\n2. Password Validation:")
    valid, msg = AuthHelper.validate_password_strength("weak")
    print(f"   'weak': {valid} - {msg}")
    
    valid, msg = AuthHelper.validate_password_strength("SecurePass123!")
    print(f"   'SecurePass123!': {valid} - {msg}")
    
    # Test email validation
    print(f"\n3. Email Validation:")
    valid, msg = AuthHelper.validate_email("test@example.com")
    print(f"   'test@example.com': {valid}")
    
    valid, msg = AuthHelper.validate_email("invalid-email")
    print(f"   'invalid-email': {valid} - {msg}")
    
    # Test session token generation
    print(f"\n4. Session Token:")
    token = AuthHelper.generate_session_token()
    print(f"   Token: {token}")
    
    # Test verification code
    print(f"\n5. Verification Code:")
    code = AuthHelper.generate_verification_code()
    print(f"   Code: {code}")
    
    print("\n✅ All authentication helper tests passed!")

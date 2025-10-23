"""
Email Service Module

Handles email sending via SendGrid for invitation system and notifications.
Includes development mode for testing without actual email sending.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import os
from typing import Optional


class EmailService:
    """
    Email service for sending invitations and notifications.
    
    Uses SendGrid in production, console output in development.
    """
    
    def __init__(self, sendgrid_api_key: Optional[str] = None, from_email: Optional[str] = None):
        """
        Initialize email service.
        
        Args:
            sendgrid_api_key: SendGrid API key (optional, uses env var if not provided)
            from_email: Sender email address (optional, uses env var if not provided)
        """
        self.sendgrid_api_key = sendgrid_api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = from_email or os.getenv('FROM_EMAIL', 'noreply@luggageroomboys.com')
        self.dev_mode = not self.sendgrid_api_key
        
        if self.dev_mode:
            print("📧 EmailService: Running in DEVELOPMENT MODE (console output only)")
        else:
            print("📧 EmailService: Running in PRODUCTION MODE (SendGrid enabled)")
    
    def send_invitation_email(self, to_email: str, first_name: str, invite_token: str,
                             invited_by_name: str, app_url: str = "http://localhost:5000") -> bool:
        """
        Send invitation email to new co-founder.
        
        Args:
            to_email: Recipient email address
            first_name: Recipient's first name
            invite_token: Unique invitation token
            invited_by_name: Name of person who sent invite
            app_url: Base URL of application
            
        Returns:
            bool: True if email sent successfully
        """
        signup_link = f"{app_url}/signup?invite={invite_token}"
        
        subject = "You're Invited to Join The Luggage Room Boys Fund"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #3B352F;
                    background-color: #FAF9F7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: #FFFFFF;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 30px;
                    border-bottom: 2px solid #E7E5E0;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #3B352F;
                    margin: 0;
                }}
                .content {{
                    padding: 30px 0;
                }}
                h1 {{
                    font-size: 28px;
                    font-weight: 600;
                    color: #3B352F;
                    margin: 0 0 20px 0;
                }}
                p {{
                    margin: 16px 0;
                    color: #3B352F;
                }}
                .cta-button {{
                    display: inline-block;
                    background: #3B352F;
                    color: #FFFFFF !important;
                    padding: 14px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 500;
                    margin: 20px 0;
                    text-align: center;
                }}
                .cta-button:hover {{
                    background: #574F45;
                }}
                .footer {{
                    padding-top: 30px;
                    border-top: 2px solid #E7E5E0;
                    text-align: center;
                    font-size: 14px;
                    color: #6B635A;
                }}
                .expiry {{
                    background: #FAF9F7;
                    padding: 16px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                    color: #6B635A;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <p class="logo">The Luggage Room Boys Fund</p>
                </div>
                
                <div class="content">
                    <h1>Hi {first_name},</h1>
                    
                    <p>You've been invited by <strong>{invited_by_name}</strong> to join The Luggage Room Boys Fund, a quantitative trading fund using AI-driven VWAP recovery strategies.</p>
                    
                    <p>As a co-founder, you'll have access to:</p>
                    <ul>
                        <li>Real-time trading dashboards and performance analytics</li>
                        <li>Capital contribution tracking and ownership management</li>
                        <li>Monthly statements and tax documents</li>
                        <li>Fund governance and decision-making</li>
                    </ul>
                    
                    <p style="text-align: center;">
                        <a href="{signup_link}" class="cta-button">Accept Invitation & Create Account</a>
                    </p>
                    
                    <div class="expiry">
                        ⏰ This invitation expires in 7 days
                    </div>
                    
                    <p style="font-size: 14px; color: #6B635A;">
                        If you're having trouble clicking the button, copy and paste this link into your browser:<br>
                        <a href="{signup_link}" style="color: #3B352F; word-break: break-all;">{signup_link}</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from The Luggage Room Boys Fund.<br>
                    If you received this email in error, please disregard it.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {first_name},

        You've been invited by {invited_by_name} to join The Luggage Room Boys Fund.

        Click here to create your account:
        {signup_link}

        This invitation expires in 7 days.

        If you received this email in error, please disregard it.

        - The Luggage Room Boys Fund
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, first_name: str) -> bool:
        """
        Send welcome email after successful signup.
        
        Args:
            to_email: New user's email
            first_name: New user's first name
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "Welcome to The Luggage Room Boys Fund"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #3B352F;
                    background-color: #FAF9F7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: #FFFFFF;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 30px;
                    border-bottom: 2px solid #E7E5E0;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #3B352F;
                    margin: 0;
                }}
                .content {{
                    padding: 30px 0;
                }}
                h1 {{
                    font-size: 28px;
                    font-weight: 600;
                    color: #3B352F;
                    margin: 0 0 20px 0;
                }}
                p {{
                    margin: 16px 0;
                    color: #3B352F;
                }}
                .footer {{
                    padding-top: 30px;
                    border-top: 2px solid #E7E5E0;
                    text-align: center;
                    font-size: 14px;
                    color: #6B635A;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <p class="logo">The Luggage Room Boys Fund</p>
                </div>
                
                <div class="content">
                    <h1>Welcome, {first_name}! 🎉</h1>
                    
                    <p>Your account has been successfully created. You're now a co-founder of The Luggage Room Boys Fund.</p>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Complete your profile information</li>
                        <li>Review fund documents and operating agreement</li>
                        <li>Familiarize yourself with the trading dashboard</li>
                        <li>Contact other co-founders to coordinate contributions</li>
                    </ol>
                    
                    <p>You can access your dashboard at any time by logging in to the platform.</p>
                    
                    <p>If you have any questions, feel free to reach out to the other co-founders.</p>
                </div>
                
                <div class="footer">
                    <p>The Luggage Room Boys Fund<br>
                    Quantitative Trading | AI-Driven Strategies</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome, {first_name}!

        Your account has been successfully created. You're now a co-founder of The Luggage Room Boys Fund.

        Next Steps:
        1. Complete your profile information
        2. Review fund documents and operating agreement
        3. Familiarize yourself with the trading dashboard
        4. Contact other co-founders to coordinate contributions

        - The Luggage Room Boys Fund
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_transaction_notification(self, to_email: str, user_name: str, 
                                     transaction_type: str, amount: float,
                                     new_balance: float) -> bool:
        """
        Send notification about capital transaction.
        
        Args:
            to_email: User's email
            user_name: User's full name
            transaction_type: 'contribution', 'distribution', or 'withdrawal'
            amount: Transaction amount
            new_balance: New balance after transaction
            
        Returns:
            bool: True if email sent successfully
        """
        subject = f"Capital {transaction_type.capitalize()} Recorded - LRBF"
        
        transaction_label = {
            'contribution': 'Contribution',
            'distribution': 'Distribution',
            'withdrawal': 'Withdrawal'
        }.get(transaction_type, transaction_type.capitalize())
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #3B352F;
                    background-color: #FAF9F7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: #FFFFFF;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .transaction-box {{
                    background: #FAF9F7;
                    padding: 24px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .amount {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #3B352F;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{transaction_label} Recorded</h1>
                
                <p>Hi {user_name},</p>
                
                <p>A capital {transaction_type} has been recorded for your account.</p>
                
                <div class="transaction-box">
                    <p><strong>Transaction Type:</strong> {transaction_label}</p>
                    <p><strong>Amount:</strong></p>
                    <p class="amount">${amount:,.2f}</p>
                    <p><strong>New Balance:</strong> ${new_balance:,.2f}</p>
                </div>
                
                <p>You can view your complete transaction history and statements in the Ledger section of your dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {transaction_label} Recorded

        Hi {user_name},

        A capital {transaction_type} has been recorded for your account.

        Transaction Type: {transaction_label}
        Amount: ${amount:,.2f}
        New Balance: ${new_balance:,.2f}

        You can view your complete transaction history in the Ledger section.

        - The Luggage Room Boys Fund
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str) -> bool:
        """
        Internal method to send email via SendGrid or console.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML version of email
            text_content: Plain text version of email
            
        Returns:
            bool: True if successful
        """
        if self.dev_mode:
            # Development mode - print to console
            print("\n" + "="*70)
            print("📧 EMAIL SENT (Development Mode)")
            print("="*70)
            print(f"To: {to_email}")
            print(f"From: {self.from_email}")
            print(f"Subject: {subject}")
            print("-"*70)
            print(text_content)
            print("="*70 + "\n")
            return True
        
        else:
            # Production mode - send via SendGrid
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail, Content
                
                message = Mail(
                    from_email=self.from_email,
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=Content("text/plain", text_content),
                    html_content=Content("text/html", html_content)
                )
                
                sg = SendGridAPIClient(self.sendgrid_api_key)
                response = sg.send(message)
                
                if response.status_code in [200, 201, 202]:
                    print(f"✅ Email sent successfully to {to_email}")
                    return True
                else:
                    print(f"⚠️ Email send returned status {response.status_code}")
                    return False
                
            except Exception as e:
                print(f"❌ Failed to send email to {to_email}: {e}")
                return False


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  EMAIL SERVICE - TESTING")
    print("="*70 + "\n")
    
    # Initialize in dev mode
    email_service = EmailService()
    
    # Test invitation email
    print("1. Testing invitation email...")
    success = email_service.send_invitation_email(
        to_email="test@example.com",
        first_name="Hugo",
        invite_token="inv_test123",
        invited_by_name="John Smith",
        app_url="http://localhost:5000"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test welcome email
    print("\n2. Testing welcome email...")
    success = email_service.send_welcome_email(
        to_email="test@example.com",
        first_name="Hugo"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test transaction notification
    print("\n3. Testing transaction notification...")
    success = email_service.send_transaction_notification(
        to_email="test@example.com",
        user_name="Hugo Martinez",
        transaction_type="contribution",
        amount=5000.00,
        new_balance=15000.00
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n✅ All email service tests completed!")

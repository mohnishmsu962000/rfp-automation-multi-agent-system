import resend
from app.core.config import get_settings

settings = get_settings()
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    
    @staticmethod
    def send_welcome_email(email: str, name: str, company_name: str):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": "Welcome to ScaleRFP! 🎉",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #6366f1;">Welcome to ScaleRFP!</h2>
                    <p>Hi {name},</p>
                    <p>Welcome aboard! Your company <strong>{company_name}</strong> is now set up on ScaleRFP.</p>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Your Free Plan includes:</strong></p>
                        <ul style="margin: 10px 0 0 0;">
                            <li>2 RFPs per month</li>
                            <li>10 documents per month</li>
                        </ul>
                    </div>
                    <p>Ready to get started? Upload your first RFP and let AI do the heavy lifting.</p>
                    <a href="https://app.scalerfp.com/dashboard" 
                       style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Go to Dashboard
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending welcome email: {e}")
    
    @staticmethod
    def send_quota_warning(email: str, name: str, used: int, limit: int, quota_type: str, tier: str):
        percentage = int((used / limit) * 100)
        
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": f"⚠️ {percentage}% of your {quota_type} quota used",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #f59e0b;">Running Low on {quota_type}!</h2>
                    <p>Hi {name},</p>
                    <p>You've used <strong>{used} out of {limit}</strong> {quota_type.lower()} this month on your <strong>{tier.title()}</strong> plan.</p>
                    <p>That's <strong>{percentage}%</strong> of your monthly quota.</p>
                    <div style="margin: 30px 0;">
                        <a href="https://app.scalerfp.com/dashboard/settings/billing" 
                           style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                            Upgrade Now
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        Upgrade to a higher plan to get more capacity and avoid interruptions.
                    </p>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending quota warning email: {e}")
    
    @staticmethod
    def send_quota_limit_reached(email: str, name: str, limit: int, quota_type: str, tier: str, reset_date: str):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": f"🚨 {quota_type} Limit Reached",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #ef4444;">Limit Reached</h2>
                    <p>Hi {name},</p>
                    <p>You've reached your monthly limit of <strong>{limit} {quota_type.lower()}</strong> on your <strong>{tier.title()}</strong> plan.</p>
                    <p>You won't be able to create new {quota_type.lower()} until:</p>
                    <ul>
                        <li>Your limit resets on <strong>{reset_date}</strong>, or</li>
                        <li>You upgrade to a higher plan</li>
                    </ul>
                    <div style="margin: 30px 0;">
                        <a href="https://app.scalerfp.com/dashboard/settings/billing" 
                           style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                            Upgrade Now
                        </a>
                    </div>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending limit reached email: {e}")
    
    @staticmethod
    def send_quota_reset(email: str, name: str, tier: str, rfp_limit: int, doc_limit: int):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": "✨ Monthly Quota Reset",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #10b981;">Quota Reset!</h2>
                    <p>Hi {name},</p>
                    <p>Great news! Your monthly quotas have been reset.</p>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Your {tier.title()} Plan Limits:</strong></p>
                        <ul style="margin: 10px 0 0 0;">
                            <li><strong>{rfp_limit} RFPs</strong> per month</li>
                            <li><strong>{doc_limit} documents</strong> per month</li>
                        </ul>
                    </div>
                    <p>You can now continue processing RFPs and uploading documents for the new month.</p>
                    <a href="https://app.scalerfp.com/dashboard" 
                       style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Go to Dashboard
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending quota reset email: {e}")
    
    @staticmethod
    def send_subscription_upgraded(email: str, name: str, old_plan: str, new_plan: str, new_price: int, rfp_limit: int, doc_limit: int):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": f"🚀 Upgraded to {new_plan}!",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #6366f1;">Plan Upgraded!</h2>
                    <p>Hi {name},</p>
                    <p>You've successfully upgraded from <strong>{old_plan}</strong> to <strong>{new_plan}</strong>.</p>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>New Plan Details:</strong></p>
                        <p style="margin: 10px 0 0 0;"><strong>Plan:</strong> {new_plan}</p>
                        <p style="margin: 10px 0 0 0;"><strong>Amount:</strong> ₹{new_price:,}/month</p>
                        <p style="margin: 10px 0 0 0;"><strong>RFPs:</strong> {rfp_limit}/month</p>
                        <p style="margin: 10px 0 0 0;"><strong>Documents:</strong> {doc_limit}/month</p>
                    </div>
                    <p>Your new limits are active immediately. Start taking advantage of your increased capacity!</p>
                    <a href="https://app.scalerfp.com/dashboard" 
                       style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Go to Dashboard
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending upgrade email: {e}")
    
    @staticmethod
    def send_subscription_activated(email: str, name: str, plan_name: str, price: int):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": f"🎉 Welcome to {plan_name}!",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #10b981;">Subscription Activated!</h2>
                    <p>Hi {name},</p>
                    <p>Your <strong>{plan_name}</strong> subscription is now active.</p>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Plan:</strong> {plan_name}</p>
                        <p style="margin: 10px 0 0 0;"><strong>Amount:</strong> ₹{price:,}/month</p>
                    </div>
                    <p>You can now enjoy all the benefits of your new plan!</p>
                    <a href="https://app.scalerfp.com/dashboard" 
                       style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Go to Dashboard
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending subscription activated email: {e}")
    
    @staticmethod
    def send_payment_failed(email: str, name: str, plan_name: str):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": "❌ Payment Failed",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #ef4444;">Payment Failed</h2>
                    <p>Hi {name},</p>
                    <p>We couldn't process your payment for the <strong>{plan_name}</strong> plan.</p>
                    <p>Please update your payment method to continue using your subscription.</p>
                    <a href="https://app.scalerfp.com/dashboard/settings/billing" 
                       style="background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Update Payment Method
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending payment failed email: {e}")
    
    @staticmethod
    def send_subscription_cancelled(email: str, name: str, plan_name: str, end_date: str):
        try:
            resend.Emails.send({
                "from": "ScaleRFP <notifications@scalerfp.com>",
                "to": email,
                "subject": "Subscription Cancelled",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Subscription Cancelled</h2>
                    <p>Hi {name},</p>
                    <p>Your <strong>{plan_name}</strong> subscription has been cancelled.</p>
                    <p>You'll continue to have access until <strong>{end_date}</strong>.</p>
                    <p>We're sorry to see you go! If you change your mind, you can reactivate anytime.</p>
                    <a href="https://app.scalerfp.com/dashboard/settings/billing" 
                       style="background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px;">
                        Reactivate Subscription
                    </a>
                </div>
                """
            })
        except Exception as e:
            print(f"Error sending cancellation email: {e}")
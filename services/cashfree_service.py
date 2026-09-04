import os
import base64
import hmac
import hashlib
import json
import time
import uuid
import re
import requests
from flask import current_app
from config import INTERNSHIP_FEES


class CashfreeService:
    """Official Cashfree Payment Gateway Service for Anti-Matrix Internship Applications."""

    SANDBOX_BASE_URL = "https://sandbox.cashfree.com/pg"
    PRODUCTION_BASE_URL = "https://api.cashfree.com/pg"

    @classmethod
    def get_config(cls):
        env = os.environ.get('CASHFREE_ENVIRONMENT', 'sandbox').lower()
        client_id = os.environ.get('CASHFREE_CLIENT_ID', '').strip()
        client_secret = os.environ.get('CASHFREE_CLIENT_SECRET', '').strip()
        api_version = os.environ.get('CASHFREE_API_VERSION', '2023-08-01').strip()
        
        # Determine base URL based on environment
        if env == 'production':
            base_url = cls.PRODUCTION_BASE_URL
        else:
            base_url = cls.SANDBOX_BASE_URL

        return {
            'environment': env,
            'client_id': client_id,
            'client_secret': client_secret,
            'api_version': api_version,
            'base_url': base_url
        }

    @classmethod
    def get_headers(cls):
        cfg = cls.get_config()
        return {
            'x-client-id': cfg['client_id'],
            'x-client-secret': cfg['client_secret'],
            'x-api-version': cfg['api_version'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    @classmethod
    def generate_order_id(cls, application_id: int) -> str:
        """Generate a unique, collision-resistant Cashfree order ID."""
        ts = int(time.time())
        rand_suffix = uuid.uuid4().hex[:5].upper()
        return f"AM-APP-{application_id:06d}-PAY-{ts}-{rand_suffix}"

    @classmethod
    def clean_phone(cls, phone: str) -> str:
        """Extract a clean 10-digit Indian phone number."""
        digits = re.sub(r'\D', '', phone or '')
        if len(digits) > 10 and digits.startswith('91'):
            digits = digits[2:]
        if len(digits) == 10:
            return digits
        return digits[-10:] if len(digits) >= 10 else "9876543210"

    @classmethod
    def create_order(cls, application, job, return_url: str, notify_url: str = None):
        """
        Create a Cashfree Order server-side.
        Amount is strictly calculated from job duration on server.
        """
        cfg = cls.get_config()
        
        # Server-enforced fee validation
        duration = job.duration or application.duration or '1_month'
        amount = float(INTERNSHIP_FEES.get(duration, 199))
        
        order_id = cls.generate_order_id(application.id)
        phone = cls.clean_phone(application.phone)
        customer_id = f"cust_{application.id}_{application.email.split('@')[0][:15]}"
        customer_id = re.sub(r'[^a-zA-Z0-9_-]', '_', customer_id)

        payload = {
            "order_id": order_id,
            "order_amount": amount,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": customer_id,
                "customer_name": application.full_name[:100],
                "customer_email": application.email[:100],
                "customer_phone": phone
            },
            "order_meta": {
                "return_url": return_url.replace('{order_id}', order_id) if '{order_id}' in return_url else f"{return_url}?order_id={order_id}"
            },
            "order_note": f"Anti-Matrix Internship Application - {job.title} ({job.duration_display})"
        }

        if notify_url:
            payload["order_meta"]["notify_url"] = notify_url

        # Check for mock/test environment without real credentials
        is_mock_or_unconfigured = (
            cfg['environment'] == 'test' or
            not cfg['client_id'] or
            not cfg['client_secret'] or
            cfg['client_id'].startswith('your_') or
            cfg['client_secret'].startswith('your_')
        )

        if is_mock_or_unconfigured and cfg['environment'] != 'production':
            # Local development test session
            mock_session_id = f"session_test_{order_id}_{uuid.uuid4().hex[:8]}"
            return True, {
                "order_id": order_id,
                "payment_session_id": mock_session_id,
                "order_status": "ACTIVE",
                "order_amount": amount,
                "order_currency": "INR",
                "is_sandbox_simulation": True
            }, None

        # Execute Live/Sandbox Cashfree API call
        endpoint = f"{cfg['base_url']}/orders"
        try:
            response = requests.post(
                endpoint,
                headers=cls.get_headers(),
                data=json.dumps(payload),
                timeout=15
            )
            data = response.json()
            if response.status_code in [200, 201]:
                return True, data, None
            else:
                error_msg = data.get('message') or data.get('error', {}).get('message') or f"Cashfree API Error ({response.status_code})"
                return False, data, error_msg
        except Exception as e:
            return False, None, f"Network error connecting to Cashfree PG: {str(e)}"

    @classmethod
    def get_order_status(cls, order_id: str):
        """Retrieve the order details directly from Cashfree."""
        cfg = cls.get_config()

        is_mock_or_unconfigured = (
            cfg['environment'] == 'test' or
            not cfg['client_id'] or
            not cfg['client_secret'] or
            cfg['client_id'].startswith('your_') or
            cfg['client_secret'].startswith('your_')
        )

        if is_mock_or_unconfigured and cfg['environment'] != 'production':
            return True, {
                "order_id": order_id,
                "order_status": "PAID",
                "order_amount": 199.00
            }, None

        endpoint = f"{cfg['base_url']}/orders/{order_id}"
        try:
            response = requests.get(
                endpoint,
                headers=cls.get_headers(),
                timeout=15
            )
            data = response.json()
            if response.status_code == 200:
                return True, data, None
            else:
                error_msg = data.get('message') or f"Unable to fetch Cashfree order status ({response.status_code})"
                return False, data, error_msg
        except Exception as e:
            return False, None, f"Network error querying Cashfree order: {str(e)}"

    @classmethod
    def get_order_payments(cls, order_id: str):
        """Retrieve all payment transactions for a given Cashfree order."""
        cfg = cls.get_config()

        is_mock_or_unconfigured = (
            cfg['environment'] == 'test' or
            not cfg['client_id'] or
            not cfg['client_secret'] or
            cfg['client_id'].startswith('your_') or
            cfg['client_secret'].startswith('your_')
        )

        if is_mock_or_unconfigured and cfg['environment'] != 'production':
            return True, [{
                "payment_status": "SUCCESS",
                "cf_payment_id": f"cf_sim_{order_id}",
                "payment_amount": 199.00,
                "payment_currency": "INR",
                "payment_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }], None

        endpoint = f"{cfg['base_url']}/orders/{order_id}/payments"
        try:
            response = requests.get(
                endpoint,
                headers=cls.get_headers(),
                timeout=15
            )
            data = response.json()
            if response.status_code == 200:
                return True, data, None
            else:
                error_msg = data.get('message') if isinstance(data, dict) else f"Cashfree Payments Error ({response.status_code})"
                return False, data, error_msg
        except Exception as e:
            return False, None, f"Network error querying Cashfree payments: {str(e)}"

    @classmethod
    def verify_order_payment(cls, order_id: str):
        """
        Verify payment status server-side from Cashfree.
        Returns (is_paid, payment_status_string, payment_info_dict, error_message).
        """
        success, payments_data, err = cls.get_order_payments(order_id)
        
        if success and isinstance(payments_data, list) and len(payments_data) > 0:
            # Check for successful payment attempt
            for pay in payments_data:
                p_status = pay.get('payment_status', '').upper()
                if p_status == 'SUCCESS':
                    return True, 'SUCCESS', pay, None
                elif p_status in ['FAILED', 'USER_DROPPED', 'CANCELLED']:
                    return False, p_status, pay, None
                elif p_status == 'PENDING':
                    return False, 'PENDING', pay, None

            # If none succeeded, return latest payment's status
            latest = payments_data[-1]
            return False, latest.get('payment_status', 'FAILED'), latest, None

        # Fallback to checking order status directly
        ord_success, order_data, ord_err = cls.get_order_status(order_id)
        if ord_success and isinstance(order_data, dict):
            ord_status = order_data.get('order_status', '').upper()
            if ord_status == 'PAID':
                return True, 'SUCCESS', order_data, None
            elif ord_status == 'ACTIVE':
                return False, 'PENDING', order_data, None
            elif ord_status in ['EXPIRED', 'TERMINATED']:
                return False, 'FAILED', order_data, None

        return False, 'UNKNOWN', None, err or ord_err or "No payment records found for order"

    @classmethod
    def verify_webhook_signature(cls, signature: str, timestamp: str, raw_body: bytes) -> bool:
        """
        Verify Cashfree Webhook signature using HMAC-SHA256.
        Formula: HMAC_SHA256(timestamp + raw_body, client_secret) base64 encoded.
        """
        if not signature or not timestamp:
            return False

        cfg = cls.get_config()
        client_secret = cfg['client_secret']
        if not client_secret:
            return False

        try:
            message = timestamp.encode('utf-8') + raw_body
            computed_hmac = hmac.new(
                client_secret.encode('utf-8'),
                message,
                hashlib.sha256
            ).digest()
            computed_signature = base64.b64encode(computed_hmac).decode('utf-8')
            return hmac.compare_digest(computed_signature, signature)
        except Exception:
            return False

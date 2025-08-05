import stripe
import streamlit as st

stripe.api_key = st.secrets["stripe_secret_key"]

def create_checkout_session(amount, currency="usd", filename="file.csv", email=None):
    """Create a dynamic Stripe Checkout Session and return payment URL + session ID."""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": f"Data Cleaning - {filename}"},
                "unit_amount": int(amount * 100)  # Stripe wants cents
            },
            "quantity": 1
        }],
        mode="payment",
        success_url="https://datacleanpro.com/payment-complete",
        cancel_url="https://datacleanpro.com/payment-cancelled",
        customer_email=email
    )
    return session.url, session.id


def check_payment_status(session_id):
    """Check the Stripe Checkout Session payment status."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status  # "paid", "unpaid", or "no_payment_required"
    except Exception as e:
        return f"error: {e}"

import stripe
import streamlit as st



stripe.api_key = st.secrets["stripe"]["secret_key"]

def create_checkout_session(amount_cents: int, user_email: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "DataCleanPro CSV Cleaning"},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            customer_email=user_email,
            success_url="https://datacleanpro.com?status=success",
            cancel_url="https://datacleanpro.com?status=cancel",
        )
        return session.url
    except Exception as e:
        st.error(f"⚠️ Payment error: {e}")
        return None

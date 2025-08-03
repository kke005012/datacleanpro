import stripe
import streamlit as st



stripe.api_key = st.secrets["stripe"]["secret_key"]

def create_checkout_session(cost_cents, user_email, filename):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "DataCleanPro File Cleaning",
                    },
                    "unit_amount": cost_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://datacleanpro.streamlit.app/?status=success&session_id={CHECKOUT_SESSION_ID}"",
            cancel_url="https://datacleanpro.streamlit.app/?status=cancel&session_id={CHECKOUT_SESSION_ID}",
            customer_email=user_email,
            metadata={"filename": filename}
        )
        return session.url
    except Exception as e:
        print("❌ Stripe session error:", e)
        return None


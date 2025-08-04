import stripe
import streamlit as st


stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def create_checkout_session(amount, currency="usd", filename="file.csv", email=None):
    session = stripe.checkout.Session.create(
        ui_mode="embedded",  # key difference
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": f"Data Cleaning - {filename}"},
                "unit_amount": int(amount * 100)
            },
            "quantity": 1
        }],
        mode="payment",
        return_url="https://datacleanpro.com/payment-complete",  # after success/fail
        customer_email=email
    )
    return session.client_secret

import streamlit.components.v1 as components

def render_embedded_checkout(client_secret, publishable_key):
    html_code = f"""
    <script src="https://js.stripe.com/v3/"></script>
    <div id="checkout"></div>
    <script>
      const stripe = Stripe("{publishable_key}");
      stripe.initEmbeddedCheckout({{
        clientSecret: "{client_secret}"
      }}).mount("#checkout");
    </script>
    """
    components.html(html_code, height=700)


def check_payment_status(session_id):
    session = stripe.checkout.Session.retrieve(session_id)
    return session.payment_status  # "paid" or "unpaid"
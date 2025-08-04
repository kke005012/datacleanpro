import stripe
import streamlit as st
import os

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def create_payment_intent_or_free(cost, currency="usd", metadata=None):
    if cost == 0:
        return {"mode": "FREE_ORDER"}  # special flag
    intent = stripe.PaymentIntent.create(
        amount=int(cost * 100),
        currency=currency,
        metadata=metadata or {}
    )
    return {
        "mode": "STRIPE",
        "client_secret": intent.client_secret
    }
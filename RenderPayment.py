import streamlit.components.v1 as components

def render_stripe_payment(client_secret, publishable_key):
    html_code = f"""
    <script src="https://js.stripe.com/v3/"></script>
    <div id="payment-element"></div>
    <button id="submit">Pay Now</button>
    <div id="payment-message"></div>

    <script>
      const stripe = Stripe("{publishable_key}");
      const elements = stripe.elements({{ clientSecret: "{client_secret}" }});
      const paymentElement = elements.create("payment");
      paymentElement.mount("#payment-element");

      document.getElementById("submit").addEventListener("click", async () => {{
        const result = await stripe.confirmPayment({{
          elements,
          confirmParams: {{ return_url: window.location.href }},
          redirect: "if_required"
        }});

        if (result.error) {{
          document.getElementById("payment-message").innerText = result.error.message;
          window.parent.postMessage({{type: "PAYMENT_FAILED"}}, "*");
        }} else if (result.paymentIntent && result.paymentIntent.status === "succeeded") {{
          document.getElementById("payment-message").innerText = "✅ Payment Successful!";
          window.parent.postMessage({{type: "PAYMENT_SUCCESS"}}, "*");
        }}
      }});
    </script>
    """
    components.html(html_code, height=400)


from streamlit_javascript import st_javascript  # or custom listener

def wait_for_payment(mode):
    if mode == "FREE_ORDER":
        return "PAYMENT_SUCCESS"
    return st_javascript("""
        await new Promise(resolve => {
            window.addEventListener('message', e => resolve(e.data.type));
        });
    """)

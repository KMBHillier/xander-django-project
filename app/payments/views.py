from django.shortcuts import render, redirect
from .models import Payment
from .forms import PaymentForm
import stripe
from app import stripe_config


def process_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            stripe_token = form.cleaned_data['stripe_token']
            amount = 100  # Replace this with the actual amount

            try:
                charge = stripe.Charge.create(
                    amount=int(amount * 100),
                    currency='usd',
                    source=stripe_token,
                    description='Payment description'
                )

                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    stripe_payment_id=charge['id']
                )

                # Your success logic here
                return redirect('success_page')
            except stripe.error.CardError as e:
                # Handle card errors
                pass

    form = PaymentForm()
    return render(request, 'payments/payment_form.html', {'form': form})

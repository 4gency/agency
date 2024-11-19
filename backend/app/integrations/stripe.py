from datetime import datetime
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select
import stripe
from app.core.config import settings
from app.models.core import Payment, Subscription, SubscriptionPlan, User

valid_currencies = ["usd", "aed", "afn", "all", "amd", "ang", "aoa", "ars", "aud", "awg", "azn", "bam", "bbd", "bdt", "bgn", "bhd", "bif", "bmd", "bnd", "bob", "brl", "bsd", "bwp", "byn", "bzd", "cad", "cdf", "chf", "clp", "cny", "cop", "crc", "cve", "czk", "djf", "dkk", "dop", "dzd", "egp", "etb", "eur", "fjd", "fkp", "gbp", "gel", "gip", "gmd", "gnf", "gtq", "gyd", "hkd", "hnl", "hrk", "htg", "huf", "idr", "ils", "inr", "isk", "jmd", "jod", "jpy", "kes", "kgs", "khr", "kmf", "krw", "kwd", "kyd", "kzt", "lak", "lbp", "lkr", "lrd", "lsl", "mad", "mdl", "mga", "mkd", "mmk", "mnt", "mop", "mur", "mvr", "mwk", "mxn", "myr", "mzn", "nad", "ngn", "nio", "nok", "npr", "nzd", "omr", "pab", "pen", "pgk", "php", "pkr", "pln", "pyg", "qar", "ron", "rsd", "rub", "rwf", "sar", "sbd", "scr", "sek", "sgd", "shp", "sle", "sos", "srd", "std", "szl", "thb", "tjs", "tnd", "top", "try", "ttd", "twd", "tzs", "uah", "ugx", "uyu", "uzs", "vnd", "vuv", "wst", "xaf", "xcd", "xof", "xpf", "yer", "zar", "zmw", "usdc", "btn", "ghs", "eek", "lvl", "svc", "vef", "ltl", "sll", "mro"]
valid_metric_types = ["day", "week", "month", "year"]

class BadRequest(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=400, detail=detail)

class NotFound(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=404, detail=detail)

def integration_enabled() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)

def create_checkout_subscription_session(
    session: Session,
    subscription_plan: SubscriptionPlan,
    user: User,
    payment: Payment,
) -> stripe.checkout.Session:
    # check if the user has a Stripe customer ID
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or user.email,
        )
        user.stripe_customer_id = customer.id
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        customer = stripe.Customer.retrieve(user.stripe_customer_id)

    # check if the subscription plan is set up in Stripe
    if not subscription_plan.stripe_price_id:
        raise BadRequest("Subscription plan is not set up in Stripe.")

    # create the checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        line_items=[
            {
                "price": subscription_plan.stripe_price_id,
                "quantity": 1,
            },
        ],
        mode="subscription",
        success_url=f"{settings.FRONTEND_HOST}/success?session_id={payment.transaction_id}",
        cancel_url=f"{settings.FRONTEND_HOST}/cancel?session_id={payment.transaction_id}",
        metadata={
            "payment_id": str(payment.id),
            "subscription_id": str(payment.subscription_id),
            "user_id": str(user.id),
            "transaction_id": str(payment.transaction_id),
        },
    )
    return checkout_session

def create_subscription_plan(
    session: Session,
    subscription_plan: SubscriptionPlan,
) -> tuple[stripe.Product, stripe.Price]:
    if subscription_plan.currency.lower() not in valid_currencies:
        raise BadRequest("Invalid currency")

    product_creation_data = {
        "name": subscription_plan.name,
        "active": subscription_plan.is_active,
        "metadata": {
            "subscription_plan_id": str(subscription_plan.id),
        },
    }
    if subscription_plan.description:
        product_creation_data["description"] = subscription_plan.description

    # calculate the amount in cents
    amount = int(subscription_plan.price * 100)

    # get the interval
    interval = subscription_plan.metric_type.name.lower()
    interval_count = subscription_plan.metric_value
    
    if interval not in valid_metric_types:
        raise BadRequest("Invalid metric type")

    # create the product in Stripe
    product = stripe.Product.create(
        **product_creation_data
    )
    
    # create the price in Stripe
    price = stripe.Price.create(
        unit_amount=amount,
        currency=subscription_plan.currency.lower(),
        recurring={
            "interval": interval,
            "interval_count": interval_count,
        },
        product=product.id,
        active=subscription_plan.is_active,
    )

    # save the Stripe IDs to the database
    subscription_plan.stripe_product_id = product.id
    subscription_plan.stripe_price_id = price.id

    session.add(subscription_plan)
    session.commit()
    session.refresh(subscription_plan)

    return product, price


def update_subscription_plan(
    session: Session,
    subscription_plan: SubscriptionPlan,
) -> None:
    if not subscription_plan.stripe_product_id or not subscription_plan.stripe_price_id:
        create_subscription_plan(session, subscription_plan)
        
    if subscription_plan.currency.lower() not in valid_currencies:
        raise BadRequest("Invalid currency")
    
    if subscription_plan.metric_type.name.lower() not in valid_metric_types:
        raise BadRequest("Invalid metric type")

    # update the product in Stripe
    stripe.Product.modify(
        subscription_plan.stripe_product_id,
        name=subscription_plan.name,
        description=subscription_plan.description,
        active=subscription_plan.is_active,
        metadata={
            "subscription_plan_id": str(subscription_plan.id),
        },
    )

    # now, let's check if the price has changed
    price = stripe.Price.retrieve(subscription_plan.stripe_price_id)

    # calculate the new amount
    new_amount = int(subscription_plan.price * 100)
    new_interval = subscription_plan.metric_type.name.lower()
    new_interval_count = subscription_plan.metric_value
    
    if new_interval_count <= 0:
        raise BadRequest("Invalid metric value")
    
    price_changed = price.unit_amount != new_amount

    # if not changed, check if the recurring interval has changed
    if not price_changed and price.recurring:
        price_changed = (
            price.recurring.get('interval') != new_interval or
            price.recurring.get('interval_count') != new_interval_count
        )

    if price_changed:
        # create a new price
        new_price = stripe.Price.create(
            unit_amount=new_amount,
            currency=subscription_plan.currency.lower(),
            recurring={
                "interval": new_interval,
                "interval_count": new_interval_count,
            },
            product=subscription_plan.stripe_product_id,
        )
        subscription_plan.stripe_price_id = new_price.id

    session.add(subscription_plan)
    session.commit()
    session.refresh(subscription_plan)


def deactivate_subscription_plan(
    session: Session,
    subscription_plan: SubscriptionPlan,
) -> None:
    if not subscription_plan.stripe_product_id:
        raise NotFound("Subscription plan is not set up in Stripe.")

    # deactivate the product in Stripe
    stripe.Product.modify(
        subscription_plan.stripe_product_id,
        active=False,
    )

    
def update_subscription_payment(
    session: Session,
    subscription: Subscription,
    payment: Payment,
) -> None:
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    # get the subscription from Stripe
    stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

    # update the subscription locally
    subscription_status = stripe_subscription.status
    subscription.is_active = subscription_status in ['active', 'trialing']
    subscription.start_date = datetime.fromtimestamp(stripe_subscription.current_period_start)
    subscription.end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)

    # update the payment locally
    latest_invoice = stripe_subscription.latest_invoice
    if latest_invoice:
        invoice = stripe.Invoice.retrieve(str(latest_invoice))
        payment.payment_status = invoice.status if invoice.status else "unknown"
        payment.payment_date = datetime.fromtimestamp(invoice.created)
        payment.amount = invoice.amount_paid / 100
        payment.currency = invoice.currency.upper()
        payment.stripe_payment_intent_id = invoice.payment_intent

    session.add(subscription)
    session.add(payment)
    session.commit()
    session.refresh(subscription)
    session.refresh(payment)


def cancel_subscription(session: Session, subscription: Subscription) -> None:
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    stripe_subscription.delete()

    # update the subscription locally
    subscription.is_active = False
    subscription.end_date = datetime.fromtimestamp(
        stripe_subscription.ended_at or datetime.now().timestamp()
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)


# webhook handlers:
def handle_payment_intent(session: Session, event: dict) -> None:
    payment_intent = event['data']['object']
    payment_intent_id = payment_intent['id']

    payment = session.exec(
        select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id) # type: ignore
    ).first()

    if not payment:
        # Registro não encontrado
        return

    # Atualizar o status do pagamento
    payment.payment_status = payment_intent['status']
    payment.payment_date = datetime.fromtimestamp(payment_intent['created'])
    payment.amount = (payment_intent['amount_received'] / 100 if payment_intent.get('amount_received') else 0)
    payment.currency = payment_intent['currency'].upper()

    session.add(payment)
    session.commit()
    session.refresh(payment)

def handle_checkout_session(session: Session, event: dict) -> None:
    checkout_session = event['data']['object']
    session_id = checkout_session['id']
    payment_intent_id = checkout_session.get('payment_intent')
    stripe_subscription_id = checkout_session.get('subscription')
    metadata = checkout_session.get('metadata', {})

    payment_id = metadata.get('payment_id')
    subscription_id_local = metadata.get('subscription_id')
    # user_id = metadata.get('user_id')

    payment = session.get(Payment, uuid.UUID(payment_id))
    subscription = session.get(Subscription, uuid.UUID(subscription_id_local))

    if payment:
        payment.stripe_payment_intent_id = payment_intent_id
        payment.payment_status = 'processing'

    if subscription:
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.is_active = True
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        subscription.start_date = datetime.fromtimestamp(stripe_subscription.current_period_start)
        subscription.end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)

    session.add(payment)
    session.add(subscription)
    session.commit()
    session.refresh(payment)
    session.refresh(subscription)

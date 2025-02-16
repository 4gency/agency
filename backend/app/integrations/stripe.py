import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import stripe
from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.models.core import (
    CheckoutSession,
    Payment,
    Subscription,
    SubscriptionMetric,
    SubscriptionPlan,
    User,
)

# --------------------------------------------------
# 1) Constantes e Exceções
# --------------------------------------------------

VALID_CURRENCIES = (
    "usd",
    "aed",
    "afn",
    "all",
    "amd",
    "ang",
    "aoa",
    "ars",
    "aud",
    "awg",
    "azn",
    "bam",
    "bbd",
    "bdt",
    "bgn",
    "bhd",
    "bif",
    "bmd",
    "bnd",
    "bob",
    "brl",
    "bsd",
    "bwp",
    "byn",
    "bzd",
    "cad",
    "cdf",
    "chf",
    "clp",
    "cny",
    "cop",
    "crc",
    "cve",
    "czk",
    "djf",
    "dkk",
    "dop",
    "dzd",
    "egp",
    "etb",
    "eur",
    "fjd",
    "fkp",
    "gbp",
    "gel",
    "gip",
    "gmd",
    "gnf",
    "gtq",
    "gyd",
    "hkd",
    "hnl",
    "hrk",
    "htg",
    "huf",
    "idr",
    "ils",
    "inr",
    "isk",
    "jmd",
    "jod",
    "jpy",
    "kes",
    "kgs",
    "khr",
    "kmf",
    "krw",
    "kwd",
    "kyd",
    "kzt",
    "lak",
    "lbp",
    "lkr",
    "lrd",
    "lsl",
    "mad",
    "mdl",
    "mga",
    "mkd",
    "mmk",
    "mnt",
    "mop",
    "mur",
    "mvr",
    "mwk",
    "mxn",
    "myr",
    "mzn",
    "nad",
    "ngn",
    "nio",
    "nok",
    "npr",
    "nzd",
    "omr",
    "pab",
    "pen",
    "pgk",
    "php",
    "pkr",
    "pln",
    "pyg",
    "qar",
    "ron",
    "rsd",
    "rub",
    "rwf",
    "sar",
    "sbd",
    "scr",
    "sek",
    "sgd",
    "shp",
    "sle",
    "sos",
    "srd",
    "std",
    "szl",
    "thb",
    "tjs",
    "tnd",
    "top",
    "try",
    "ttd",
    "twd",
    "tzs",
    "uah",
    "ugx",
    "uyu",
    "uzs",
    "vnd",
    "vuv",
    "wst",
    "xaf",
    "xcd",
    "xof",
    "xpf",
    "yer",
    "zar",
    "zmw",
    "usdc",
    "btn",
    "ghs",
    "eek",
    "lvl",
    "svc",
    "vef",
    "ltl",
    "sll",
    "mro",
)
VALID_METRIC_TYPES = ("day", "week", "month", "year")


class BadRequest(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=400, detail=detail)


class NotFound(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=404, detail=detail)


# --------------------------------------------------
# 2) Verificações Básicas
# --------------------------------------------------


def integration_enabled() -> bool:
    """Retorna True se a chave secreta da Stripe estiver configurada."""
    return bool(settings.STRIPE_SECRET_KEY)


# --------------------------------------------------
# 3) Funções de Plano de Assinatura (Product/Price)
# --------------------------------------------------


def create_subscription_plan(
    session: Session,
    subscription_plan: SubscriptionPlan,
) -> tuple[stripe.Product, stripe.Price]:
    """
    Cria um Product e Price na Stripe para o SubscriptionPlan,
    armazenando os IDs no banco.
    """
    if subscription_plan.currency.lower() not in VALID_CURRENCIES:
        raise BadRequest("Invalid currency")

    interval: str = subscription_plan.metric_type.value

    interval_count = subscription_plan.metric_value
    if interval not in VALID_METRIC_TYPES:
        raise BadRequest("Invalid metric type")

    product_data = {
        "name": subscription_plan.name,
        "active": subscription_plan.is_active,
        "metadata": {"subscription_plan_id": str(subscription_plan.id)},
    }
    if subscription_plan.description:
        product_data["description"] = subscription_plan.description

    amount_cents = int(subscription_plan.price * 100)

    # Cria product na Stripe
    product = stripe.Product.create(**product_data)  # type: ignore

    # Cria price na Stripe
    price = stripe.Price.create(
        unit_amount=amount_cents,
        currency=subscription_plan.currency.lower(),
        recurring={"interval": interval, "interval_count": interval_count},  # type: ignore
        product=product.id,
        active=subscription_plan.is_active,
    )

    # Salva IDs no BD
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
    """
    Atualiza Product/Price na Stripe se já existir,
    ou cria se não houver IDs. Altera Price caso mude de valor ou intervalo.
    """
    # Se não tem product/price, cria
    if not subscription_plan.stripe_product_id or not subscription_plan.stripe_price_id:
        create_subscription_plan(session, subscription_plan)
        return

    # Valida moeda e tipo de métrica
    if subscription_plan.currency.lower() not in VALID_CURRENCIES:
        raise BadRequest("Invalid currency")

    interval = subscription_plan.metric_type.name.lower()
    interval_count = subscription_plan.metric_value
    if interval not in VALID_METRIC_TYPES:
        raise BadRequest("Invalid metric type")
    if interval_count <= 0:
        raise BadRequest("Invalid metric value")

    # Atualiza product
    stripe.Product.modify(
        subscription_plan.stripe_product_id,
        name=subscription_plan.name,
        description=subscription_plan.description,
        active=subscription_plan.is_active,
        metadata={"subscription_plan_id": str(subscription_plan.id)},
    )

    # Verifica se precisa criar um novo price
    current_price = stripe.Price.retrieve(subscription_plan.stripe_price_id)
    new_amount_cents = int(subscription_plan.price * 100)

    price_changed = False
    if current_price.unit_amount != new_amount_cents:
        price_changed = True
    else:
        # Checa se mudou o intervalo
        if current_price.recurring:
            if (
                current_price.recurring.get("interval") != interval
                or current_price.recurring.get("interval_count") != interval_count
            ):
                price_changed = True

    if price_changed:
        new_price = stripe.Price.create(
            unit_amount=new_amount_cents,
            currency=subscription_plan.currency.lower(),
            recurring={"interval": interval, "interval_count": interval_count},  # type: ignore
            product=subscription_plan.stripe_product_id,
            active=subscription_plan.is_active,
        )
        subscription_plan.stripe_price_id = new_price.id

    session.add(subscription_plan)
    session.commit()
    session.refresh(subscription_plan)


def deactivate_subscription_plan(
    session: Session,  # noqa
    subscription_plan: SubscriptionPlan,
) -> None:
    """
    Desativa um product na Stripe (não remove o Price).
    """
    if not subscription_plan.stripe_product_id:
        raise NotFound("Subscription plan is not set up in Stripe.")
    stripe.Product.modify(subscription_plan.stripe_product_id, active=False)


# --------------------------------------------------
# 4) Funções de Checkout / Customer
# --------------------------------------------------


def ensure_stripe_customer(session: Session, user: User) -> str:
    """
    Verifica se o User tem stripe_customer_id. Se não tiver,
    cria um Customer na Stripe e salva localmente.
    Retorna o ID do customer.
    """
    if user.stripe_customer_id:
        # Já existe
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name or user.email,
    )
    user.stripe_customer_id = customer.id
    session.add(user)
    session.commit()
    session.refresh(user)

    return customer.id


def create_checkout_subscription_session(
    session: Session,
    subscription_plan: SubscriptionPlan,
    user: User,
    payment: Payment,
) -> stripe.checkout.Session:
    """
    Cria uma sessão de checkout (Stripe Checkout) para assinar um plano.
    Usa 'payment' para preencher metadata de identificação.
    """
    # Garante que o user tenha Stripe Customer
    customer_id = ensure_stripe_customer(session, user)

    if not subscription_plan.stripe_price_id:
        raise BadRequest("Subscription plan is not set up in Stripe.")

    # Cria checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": subscription_plan.stripe_price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.FRONTEND_HOST}/stripe/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_HOST}/stripe/cancel?session_id={{CHECKOUT_SESSION_ID}}",
        metadata={
            "payment_id": str(payment.id),
            "subscription_id": str(payment.subscription_id),
            "user_id": str(user.id),
            "transaction_id": str(payment.transaction_id),
        },
    )

    return checkout_session


# --------------------------------------------------
# 5) Funções de Assinatura (Subscription)
# --------------------------------------------------


def update_subscription_payment(
    session: Session,
    subscription: Subscription,
    payment: Payment,
) -> None:
    """
    Puxa dados da subscription na Stripe e atualiza:
    - subscription (status, datas)
    - payment (invoice, amounts)
    """
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    subscription_status = stripe_sub.status
    subscription.is_active = subscription_status in ["active", "trialing"]
    subscription.start_date = datetime.fromtimestamp(stripe_sub.current_period_start)
    subscription.end_date = datetime.fromtimestamp(stripe_sub.current_period_end)

    # Atualiza pagamento a partir da latest_invoice
    latest_invoice_id = stripe_sub.latest_invoice
    if latest_invoice_id:
        invoice = stripe.Invoice.retrieve(str(latest_invoice_id))
        payment.payment_status = invoice.status if invoice.status else "unknown"
        payment.payment_date = datetime.fromtimestamp(invoice.created)
        payment.amount = (invoice.amount_paid or 0) / 100
        payment.currency = invoice.currency.upper()
        payment.transaction_id = str(invoice.payment_intent)

    session.add(subscription)
    session.add(payment)
    session.commit()
    session.refresh(subscription)
    session.refresh(payment)


def cancel_subscription(session: Session, subscription: Subscription) -> None:
    """
    Cancela (deleta) completamente a assinatura na Stripe,
    removendo cobranças futuras e mudando status local para inativo.
    """
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    stripe_sub.delete()

    subscription.is_active = False
    subscription.end_date = datetime.fromtimestamp(
        stripe_sub.ended_at or datetime.now(timezone.utc).timestamp()
    )

    session.add(subscription)
    session.commit()
    session.refresh(subscription)


def cancel_subscription_recurring_payment(
    session: Session, subscription: Subscription, cancel_at_period_end: bool = True
) -> None:
    """
    Cancela somente a recorrência de pagamento na Stripe,
    definindo cancel_at_period_end. Não deleta a subscription.

    - Se True: assinatura permanece ativa até o fim do ciclo atual,
      mas não será renovada.
    - Se False: cancela imediatamente a recorrência (status='canceled').
    """
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    if stripe_sub.status in ("canceled", "inactive"):
        raise BadRequest("Subscription is already fully canceled on Stripe.")

    updated_sub = stripe.Subscription.modify(
        subscription.stripe_subscription_id, cancel_at_period_end=cancel_at_period_end
    )

    # Se cancelar imediatamente (False), Stripe define status='canceled'
    if not cancel_at_period_end:
        subscription.is_active = False
        subscription.end_date = datetime.fromtimestamp(
            updated_sub.ended_at or datetime.now(timezone.utc).timestamp()
        )
    else:
        # Caso contrário, a sub fica "ativa" até o fim do período
        # Se quiser marcar algo local para saber que ela será cancelada, pode fazer.
        pass

    session.add(subscription)
    session.commit()
    session.refresh(subscription)


def reactivate_subscription(session: Session, subscription: Subscription) -> None:
    """
    Reativa uma assinatura que estava com cancel_at_period_end=True.
    Se a assinatura já estiver com status='canceled' na Stripe,
    não é possível reativar (precisa criar outra).
    """
    if not subscription.stripe_subscription_id:
        raise NotFound("Subscription does not have a Stripe Subscription ID.")

    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

    if stripe_sub.status == "canceled":
        raise BadRequest(
            "Subscription is fully canceled on Stripe. Need a new subscription."
        )

    if not stripe_sub.cancel_at_period_end:
        raise BadRequest("Subscription is not set to cancel at period end.")

    stripe.Subscription.modify(
        subscription.stripe_subscription_id, cancel_at_period_end=False
    )

    subscription.is_active = True
    session.add(subscription)
    session.commit()
    session.refresh(subscription)


# --------------------------------------------------
# 6) Helpers de Datas e Extensão
# --------------------------------------------------


def _calculate_end_date(
    plan: SubscriptionPlan, base_date: datetime | None = None
) -> datetime:
    """Calcula a data de término com base na metric_type e metric_value do plano."""
    if not base_date:
        base_date = datetime.now(timezone.utc)

    if plan.metric_type == SubscriptionMetric.DAY:
        return base_date + timedelta(days=plan.metric_value)
    elif plan.metric_type == SubscriptionMetric.WEEK:
        return base_date + timedelta(weeks=plan.metric_value)
    elif plan.metric_type == SubscriptionMetric.MONTH:
        return base_date + timedelta(days=30 * plan.metric_value)
    elif plan.metric_type == SubscriptionMetric.YEAR:
        return base_date + timedelta(days=365 * plan.metric_value)
    return base_date


def _extend_subscription(subscription: Subscription, plan: SubscriptionPlan) -> None:
    """
    Se a sub já expirou, redefine start_date para agora.
    Se ainda está ativa, soma a nova duração ao end_date atual.
    """
    now_utc = datetime.now(timezone.utc)

    # Garante que end_date esteja em UTC
    if subscription.end_date.tzinfo is None:
        subscription.end_date = subscription.end_date.replace(tzinfo=timezone.utc)

    if subscription.end_date < now_utc:
        subscription.start_date = now_utc
        subscription.end_date = _calculate_end_date(plan, base_date=now_utc)
    else:
        subscription.end_date = _calculate_end_date(
            plan, base_date=subscription.end_date
        )

    subscription.is_active = True


# --------------------------------------------------
# 7) Webhooks e Callbacks
# --------------------------------------------------


def handle_checkout_session(session: Session, event: dict[Any, Any]) -> None:
    """
    Webhook handler para 'checkout.session.completed'.
    Decide se foi um 'success' ou 'cancel' e chama a lógica unificada.
    """
    checkout_obj = event["data"]["object"]
    # session_id = checkout_obj["id"]
    payment_status = checkout_obj.get("payment_status")  # 'paid' ou 'unpaid'
    stripe_subscription_id = checkout_obj.get("subscription")
    metadata = checkout_obj.get("metadata", {})

    # Busca local
    payment_id = metadata.get("payment_id")
    local_sub_id = metadata.get("subscription_id")

    payment = session.get(Payment, uuid.UUID(payment_id)) if payment_id else None
    subscription = (
        session.get(Subscription, uuid.UUID(local_sub_id)) if local_sub_id else None
    )

    # Se pagamento_status='paid', chamamos _common_success_logic
    # caso contrário, pode ser um 'cancel' ou 'unpaid'
    if payment_status == "paid":
        _common_success_logic(session, subscription, payment, stripe_subscription_id)
    elif payment_status == "unpaid":
        _common_cancel_logic(session, payment)


def handle_success_callback(
    session: Session, checkout: CheckoutSession, plan: SubscriptionPlan, user: User
) -> dict[str, str]:
    """
    Rota de sucesso. Verifica no Stripe se está pago e chama a mesma
    função de sucesso unificada (se ainda não tiver processado).
    """
    stripe_sess = stripe.checkout.Session.retrieve(checkout.session_id)

    if stripe_sess.payment_status == "paid":
        # Carrega local
        stripe_subscription_id = stripe_sess.get("subscription")
        payment_id = stripe_sess.get("metadata", {}).get("payment_id")
        local_sub_id = stripe_sess.get("metadata", {}).get("subscription_id")

        payment = session.get(Payment, uuid.UUID(payment_id)) if payment_id else None
        subscription = (
            session.get(Subscription, uuid.UUID(local_sub_id)) if local_sub_id else None
        )

        _common_success_logic(session, subscription, payment, stripe_subscription_id)
        # Também chamamos _validate_success_callback para criar/estender se não existir
        # mas podemos unificar essa ideia dentro de _common_success_logic
        _validate_success_callback(session, checkout, plan, user)

        return {"message": "Success callback processed"}
    else:
        raise BadRequest("Checkout session payment status is not 'paid'")


def handle_cancel_callback(
    session: Session, checkout: CheckoutSession
) -> dict[str, str]:
    """
    Rota de cancelamento. Se não estiver pago, marcamos como cancelado.
    Caso já tenha sido pago, ignoramos.
    """
    stripe_sess = stripe.checkout.Session.retrieve(checkout.session_id)

    if checkout.status == "complete":
        return {"message": "Already processed"}

    # Se não está pago, chamamos a lógica de cancel
    if stripe_sess.payment_status != "paid":
        payment_id = stripe_sess.get("metadata", {}).get("payment_id")

        payment = session.get(Payment, uuid.UUID(payment_id)) if payment_id else None

        _common_cancel_logic(session, payment)

        # Marcar o checkout também como cancelado
        checkout.status = "canceled"
        checkout.payment_status = "unpaid"
        checkout.updated_at = datetime.now(timezone.utc)
        session.add(checkout)
        session.commit()
        session.refresh(checkout)

        return {"message": "Cancel callback processed"}
    else:
        # Se já está pago, não dá para cancelar
        return {"message": "Payment already done, cannot cancel"}


#
# LÓGICA COMPARTILHADA DE SUCESSO / CANCEL
#


def _common_success_logic(
    session: Session,
    subscription: Subscription | None,
    payment: Payment | None,
    stripe_subscription_id: str | None,
) -> None:
    """
    Lógica de 'success' usada tanto pelo webhook checkout.session.completed
    (caso payment_status='paid'), quanto pelo callback success do usuário.
    - Marca 'payment_status' como 'paid'
    - Atribui 'stripe_subscription_id' se ainda não tiver
    - Marca subscription como ativa
    - Ajusta datas
    """
    if subscription:
        if not subscription.stripe_subscription_id and stripe_subscription_id:
            subscription.stripe_subscription_id = stripe_subscription_id
        subscription.is_active = True

        # Se quisermos puxar datas exatas da Stripe:
        if subscription.stripe_subscription_id:
            stripe_sub = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )
            subscription.start_date = datetime.fromtimestamp(
                stripe_sub.current_period_start
            )
            subscription.end_date = datetime.fromtimestamp(
                stripe_sub.current_period_end
            )

    if payment:
        payment.payment_status = "paid"

    session.add_all([subscription, payment])
    session.commit()
    if subscription:
        session.refresh(subscription)
    if payment:
        session.refresh(payment)


def _common_cancel_logic(
    session: Session,
    # subscription: Subscription | None,
    payment: Payment | None,
) -> None:
    """
    Lógica de 'cancel' usada tanto pelo webhook (se por acaso recebesse um evento 'canceled')
    quanto pela rota callback de cancel:
    - Marca payment como 'unpaid' ou 'canceled'
    """
    if payment and payment.payment_status not in ("paid", "refunded"):
        payment.payment_status = "canceled"

    session.add_all(
        [
            payment,
        ]
    )
    session.commit()
    if payment:
        session.refresh(payment)


#
# VALIDATE SUCCESS
#


def _validate_success_callback(
    session: Session, checkout: CheckoutSession, plan: SubscriptionPlan, user: User
) -> Subscription | None:
    """
    Marca checkout como 'complete' + 'paid'.
    Cria ou estende assinatura localmente para esse user + plan,
    cria Payment se ainda não existir, etc.
    """
    if checkout.status == "complete":
        return None  # já processou

    try:
        # 1) Atualiza status do CheckoutSession
        checkout.status = "complete"
        checkout.payment_status = "paid"
        checkout.updated_at = datetime.now(timezone.utc)
        session.add(checkout)

        # 2) Verifica se já existe sub ativa para o mesmo plano
        existing_sub = session.exec(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.subscription_plan_id == plan.id)
            .where(Subscription.is_active is True)
        ).first()

        # 3) Cria ou atualiza a sub
        if existing_sub:
            # _extend_subscription seria outra função para somar dias/meses
            existing_sub.end_date = datetime.now(timezone.utc)  # Exemplo
            subscription = existing_sub
        else:
            subscription = Subscription(
                user_id=user.id,
                subscription_plan_id=plan.id,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=30),  # Exemplo
                is_active=True,
                metric_type=plan.metric_type,
                metric_status=1,
                stripe_subscription_id=None,  # pode ser setado depois
            )
            session.add(subscription)
            session.flush()

        # 4) Verifica Payment
        existing_payment = session.exec(
            select(Payment).where(Payment.transaction_id == checkout.session_id)
        ).first()

        if not existing_payment:
            new_payment = Payment(
                subscription_id=subscription.id,
                user_id=user.id,
                amount=plan.price,
                currency=plan.currency,
                payment_date=datetime.now(timezone.utc),
                payment_status="paid",
                payment_gateway="stripe",
                transaction_id=checkout.session_id,
            )
            session.add(new_payment)
            session.flush()
        else:
            existing_payment.payment_status = "paid"
            existing_payment.payment_date = datetime.now(timezone.utc)
            session.add(existing_payment)
            session.flush()

        session.commit()
        return subscription
    except Exception as e:
        session.rollback()
        raise e

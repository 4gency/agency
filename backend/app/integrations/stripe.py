import logging
from datetime import datetime, timezone

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm.session import SessionTransaction
from sqlmodel import Session, select

from app.core.config import settings
from app.models.core import (
    CheckoutSession,
    Payment,
    Subscription,
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
logger = logging.getLogger(__name__)


class BadRequest(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotFound(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyProcessed(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _begin_transaction(session: Session) -> SessionTransaction:
    if session.in_transaction():
        return session.begin_nested()
    return session.begin()


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


def setup_plan_in_stripe(
    session: Session,
    subscription_plan: SubscriptionPlan,
) -> None:
    """
    Cria ou atualiza Product/Price na Stripe para o SubscriptionPlan.
    """
    if not subscription_plan.stripe_product_id or not subscription_plan.stripe_price_id:
        create_subscription_plan(session, subscription_plan)
    else:
        update_subscription_plan(session, subscription_plan)


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
) -> stripe.checkout.Session:
    """
    Cria uma sessão de checkout (Stripe Checkout) para assinar um plano.
    Usa 'payment' para preencher metadata de identificação.
    """
    # Garante que o user tenha Stripe Customer
    customer_id = ensure_stripe_customer(session, user)

    if not subscription_plan.stripe_price_id:
        setup_plan_in_stripe(session, subscription_plan)
        if not subscription_plan.stripe_price_id:
            raise Exception("Stripe Price ID cannot be set")

    # Cria checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": subscription_plan.stripe_price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.FRONTEND_HOST}/checkout-success?sessionId={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_HOST}/checkout-failed?sessionId={{CHECKOUT_SESSION_ID}}",
        metadata={
            "user_id": str(user.id),
            "plan_id": str(subscription_plan.id),
        },
    )

    return checkout_session


# --------------------------------------------------
# 5) Funções de Assinatura (Subscription)
# --------------------------------------------------


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
# 7) Webhooks e Callbacks
# --------------------------------------------------


def handle_success_callback(
    session: Session, checkout: CheckoutSession
) -> dict[str, str]:
    """
    Callback acionado pelo usuário informando que concluiu o processo.
    Atualiza o CheckoutSession para 'complete', após validar o status pago no Stripe.
    Essa função NÃO cria ou atualiza a subscription, pois isso já é feito pelo handle_invoice_payment_succeeded.
    """
    try:
        stripe_sess = stripe.checkout.Session.retrieve(checkout.session_id)
        if stripe_sess.payment_status == "paid":
            with _begin_transaction(session):
                if checkout.status != "complete":
                    checkout.status = "complete"
                    checkout.payment_status = "paid"
                    checkout.updated_at = datetime.now(timezone.utc)
                    session.add(checkout)
                    logger.info(
                        "Success callback: CheckoutSession %s marcado como complete",
                        checkout.session_id,
                    )
            return {"message": "Success callback processed"}
        else:
            logger.error(
                "CheckoutSession %s não está com payment_status 'paid'",
                checkout.session_id,
            )
            raise BadRequest("Checkout session payment status is not 'paid'")
    except Exception as e:
        session.rollback()
        logger.exception("Falha no processamento do success callback: %s", str(e))
        raise e


def handle_checkout_session(session: Session, event: stripe.Event) -> None:
    """
    Webhook handler para 'checkout.session.completed'.
    Finaliza os dados do checkout, marcando-o como complete (para payment_status 'paid')
    ou delegando ao cancelamento (para 'unpaid').
    """
    try:
        with _begin_transaction(session):
            checkout_obj = event["data"]["object"]
            checkout_session_id = checkout_obj.get("id")
            payment_status = checkout_obj.get("payment_status")

            checkout = session.exec(
                select(CheckoutSession).where(
                    CheckoutSession.session_id == checkout_session_id
                )
            ).first()
            if not checkout:
                logger.error(
                    "CheckoutSession não encontrado para session_id: %s",
                    checkout_session_id,
                )
                raise Exception("CheckoutSession not found.")

            if payment_status == "paid":
                if checkout.status != "complete":
                    checkout.status = "complete"
                    checkout.payment_status = "paid"
                    checkout.updated_at = datetime.now(timezone.utc)
                    session.add(checkout)
                    logger.info(
                        "CheckoutSession %s marcado como complete (payment_status paid)",
                        checkout_session_id,
                    )
            elif payment_status == "unpaid":
                handle_cancel_callback(session, checkout)
            else:
                logger.warning(
                    "Status de pagamento desconhecido (%s) para CheckoutSession %s",
                    payment_status,
                    checkout_session_id,
                )

    except Exception as e:
        session.rollback()
        logger.exception(
            "Falha no processamento de checkout.session.completed: %s", str(e)
        )
        raise e


def handle_cancel_callback(
    session: Session, checkout: CheckoutSession
) -> dict[str, str]:
    """
    Callback de cancelamento.
    Caso a CheckoutSession ainda não esteja paga, marca-a como 'canceled' e 'unpaid'.
    """
    try:
        stripe_sess = stripe.checkout.Session.retrieve(checkout.session_id)
        if checkout.status == "complete":
            return {"message": "Already processed"}

        if stripe_sess.payment_status != "paid":
            with _begin_transaction(session):
                checkout.status = "canceled"
                checkout.payment_status = "unpaid"
                checkout.updated_at = datetime.now(timezone.utc)
                session.add(checkout)
                logger.info(
                    "CheckoutSession %s marcado como canceled", checkout.session_id
                )
            return {"message": "Cancel callback processed"}
        else:
            logger.info(
                "Pagamento já efetuado para CheckoutSession %s; cancelamento não permitido",
                checkout.session_id,
            )
            return {"message": "Payment already done, cannot cancel"}
    except Exception as e:
        session.rollback()
        logger.exception("Falha no processamento do cancel callback: %s", str(e))
        raise e


#
# VALIDATE SUCCESS
#


def update_subscription_payment(
    session: Session,
    subscription: Subscription,
    payment: Payment,
    stripe_sub: stripe.Subscription,
) -> None:
    """
    Atualiza a subscription e o Payment com os dados mais recentes da Stripe.

    Consulta a subscription na Stripe para atualizar o status, datas e, a partir da última invoice,
    atualiza os detalhes do pagamento.
    """
    try:
        # Recupera os dados atualizados da subscription na Stripe
        subscription_status = stripe_sub.status
        subscription.is_active = subscription_status in ["active", "trialing"]
        subscription.start_date = datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=timezone.utc
        )
        subscription.end_date = datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=timezone.utc
        )

        # Atualiza o Payment com base na última invoice
        latest_invoice_id = stripe_sub.latest_invoice
        if latest_invoice_id:
            invoice = stripe.Invoice.retrieve(str(latest_invoice_id))
            payment.payment_status = invoice.status or "unknown"
            payment.payment_date = datetime.fromtimestamp(
                invoice.created, tz=timezone.utc
            )
            payment.amount = (
                invoice.amount_paid or 0
            ) / 100.0  # converte de centavos para valor unitário
            payment.currency = invoice.currency.upper() if invoice.currency else "USD"
        session.add(subscription)
        session.add(payment)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("Erro ao atualizar subscription/payment: %s", str(e))
        raise e


def process_invoice_payment_succeeded(
    session: Session,
    stripe_invoice: stripe.Invoice,
    stripe_subscription: stripe.Subscription,
    user: User,
    plan: SubscriptionPlan,
    subscription: Subscription | None = None,
) -> None:
    """
    Processa o pagamento da invoice, criando ou atualizando a Subscription e registrando o Payment.
    Essa função é reutilizável e assume que todas as instâncias necessárias já foram obtidas.
    """
    stripe_subscription_id = stripe_subscription.id
    amount_paid = stripe_invoice.amount_paid
    currency = stripe_invoice.currency

    # Cria ou atualiza a Subscription
    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            subscription_plan_id=plan.id,
            start_date=datetime.now(timezone.utc),
            is_active=True,
            metric_type=plan.metric_type,
            metric_status=plan.metric_value,
            stripe_subscription_id=stripe_subscription_id,
            end_date=datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            ),
        )
        session.add(subscription)
        session.flush()  # para obter o ID da subscription
        logger.info(
            "Criada nova Subscription para user %s com stripe_subscription_id %s",
            user.id,
            stripe_subscription_id,
        )
    else:
        # Opcional: atualizar o plano se diferente do atual
        if subscription.subscription_plan_id != plan.id:
            subscription.subscription_plan_id = plan.id
            logger.info(
                "Subscription %s atualizada para o novo plano %s",
                subscription.id,
                plan.id,
            )

    # Verifica se o Payment já existe (idempotência)
    existing_payment = session.exec(
        select(Payment).where(Payment.transaction_id == stripe_invoice.id)
    ).first()

    if existing_payment:
        logger.info("Payment já existe para transaction_id %s", stripe_invoice.id)
        raise AlreadyProcessed("This subscription payment has already been processed.")

    payment = Payment(
        subscription_id=subscription.id,
        user_id=user.id,
        amount=amount_paid / 100.0,
        currency=currency.upper() if currency else "USD",
        payment_date=datetime.now(timezone.utc),
        payment_status=stripe_invoice.status or "unknown",
        payment_gateway="stripe",
        transaction_id=str(stripe_invoice.id),
    )
    session.add(payment)
    logger.info("Criado novo Payment para transaction_id %s", stripe_invoice.id)

    session.flush()

    # Atualiza a Subscription com dados atualizados da Stripe
    update_subscription_payment(session, subscription, payment, stripe_subscription)


def handle_invoice_payment_succeeded_in_checkout_callback(
    session: Session,
    checkout: CheckoutSession,
    user: User,
    plan: SubscriptionPlan,
) -> None:
    try:
        stripe_checkout_session: stripe.checkout.Session = (
            stripe.checkout.Session.retrieve(checkout.session_id)
        )
        if not stripe_checkout_session:
            logger.error("CheckoutSession não encontrado na Stripe.")
            raise Exception("CheckoutSession not found.")

        stripe_invoice: stripe.Invoice = stripe.Invoice.retrieve(
            str(stripe_checkout_session.invoice)
        )
        if not stripe_invoice:
            logger.error("Invoice não encontrado na Stripe.")
            raise Exception("Invoice not found.")

        stripe_subscription: stripe.Subscription = stripe.Subscription.retrieve(
            str(stripe_invoice.subscription)
        )
        if not stripe_subscription:
            logger.error("Subscription não encontrado na Stripe.")
            raise Exception("Subscription not found.")

        subscription = session.exec(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription.id
            )
        ).first()

        process_invoice_payment_succeeded(
            session=session,
            stripe_invoice=stripe_invoice,
            stripe_subscription=stripe_subscription,
            user=user,
            plan=plan,
            subscription=subscription or None,
        )
    except AlreadyProcessed as e:
        session.rollback()
        raise e
    except Exception as e:
        logger.exception(
            "Erro no processamento de invoice.payment_succeeded: %s", str(e)
        )
        session.rollback()
        raise e


def handle_invoice_payment_succeeded(session: Session, event: stripe.Event) -> None:
    """
    Webhook handler para 'invoice.payment_succeeded'.

    Junta todos os dados necessários e chama a função process_invoice_payment_succeeded para
    criar/atualizar a Subscription e registrar o Payment.
    """
    try:
        with _begin_transaction(session):
            # Recupera os dados da Stripe
            stripe_invoice = stripe.Invoice.retrieve(event["data"]["object"]["id"])
            stripe_subscription = stripe.Subscription.retrieve(
                stripe_invoice.subscription  # type: ignore
            )
            stripe_plan = stripe.Plan.retrieve(str(stripe_subscription.plan.id))  # type: ignore

            if not all([stripe_subscription, stripe_plan]):
                logger.error("Subscription ou Plan não encontrados na Stripe.")
                raise Exception("Subscription or Plan not found.")

            # Busca o usuário no banco de dados
            user = session.exec(
                select(User).where(User.stripe_customer_id == stripe_invoice.customer)
            ).first()
            if not user:
                logger.error(
                    "User não encontrado para stripe_customer_id: %s",
                    stripe_invoice.customer,
                )
                raise Exception("User not found.")

            # Busca o SubscriptionPlan associado
            plan = session.exec(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.stripe_product_id == stripe_plan.product
                )
            ).first()
            if not plan:
                logger.error(
                    "SubscriptionPlan não encontrada para plan_id: %s",
                    stripe_plan.product,
                )
                raise Exception("SubscriptionPlan not found.")

            # Busca a Subscription existente, se houver
            subscription = session.exec(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_subscription.id
                )
            ).first()
            try:
                # Processa o pagamento e a subscription com a função reutilizável
                process_invoice_payment_succeeded(
                    session=session,
                    stripe_invoice=stripe_invoice,
                    stripe_subscription=stripe_subscription,
                    user=user,
                    plan=plan,
                    subscription=subscription,
                )
            except AlreadyProcessed as e:
                logger.info("Evento já processado: %s", str(e))
            except Exception as e:
                logger.exception(
                    "Erro no processamento de invoice.payment_succeeded: %s", str(e)
                )
                raise e
    except Exception as e:
        session.rollback()
        logger.exception(
            "Erro no processamento de invoice.payment_succeeded: %s", str(e)
        )
        raise e


def handle_checkout_session_expired(session: Session, event: stripe.Event) -> None:
    """
    Webhook handler para 'checkout.session.expired'.
    Marca a CheckoutSession como 'expired' e 'unpaid'.
    """
    try:
        with _begin_transaction(session):
            checkout_obj = event["data"]["object"]
            checkout_session_id = checkout_obj.get("id")

            checkout = session.exec(
                select(CheckoutSession).where(
                    CheckoutSession.session_id == checkout_session_id
                )
            ).first()
            if not checkout:
                logger.error(
                    "CheckoutSession não encontrado para session_id: %s",
                    checkout_session_id,
                )
                raise Exception("CheckoutSession not found.")

            if checkout.status != "complete":
                checkout.status = "expired"
                checkout.payment_status = "unpaid"
                checkout.updated_at = datetime.now(timezone.utc)
                session.add(checkout)
                logger.info(
                    "CheckoutSession %s marcado como expired", checkout.session_id
                )
    except Exception as e:
        session.rollback()
        logger.exception(
            "Falha no processamento de checkout.session.expired: %s", str(e)
        )
        raise e


def handle_checkout_session_async_payment_failed(
    session: Session, event: stripe.Event
) -> None:
    """
    Webhook handler para 'checkout.session.async_payment_failed'.
    Marca a CheckoutSession como 'failed' e 'unpaid'.
    """
    try:
        with _begin_transaction(session):
            checkout_obj = event["data"]["object"]
            checkout_session_id = checkout_obj.get("id")

            checkout = session.exec(
                select(CheckoutSession).where(
                    CheckoutSession.session_id == checkout_session_id
                )
            ).first()
            if not checkout:
                logger.error(
                    "CheckoutSession não encontrado para session_id: %s",
                    checkout_session_id,
                )
                raise Exception("CheckoutSession not found.")

            if checkout.status != "complete":
                checkout.status = "failed"
                checkout.payment_status = "unpaid"
                checkout.updated_at = datetime.now(timezone.utc)
                session.add(checkout)
                logger.info(
                    "CheckoutSession %s marcado como failed", checkout.session_id
                )
    except Exception as e:
        session.rollback()
        logger.exception(
            "Falha no processamento de checkout.session.async_payment_failed: %s",
            str(e),
        )
        raise e


def handle_charge_dispute_created(session: Session, event: stripe.Event) -> None:
    """
    Webhook handler para 'charge.dispute.created'.
    Marca a Subscription como 'disputed' e 'unpaid'.
    """
    try:
        with _begin_transaction(session):
            charge_obj = event["data"]["object"]
            payment_intent_id = charge_obj.get("payment_intent")

            payment = session.exec(
                select(Payment).where(Payment.transaction_id == payment_intent_id)
            ).first()
            if not payment:
                logger.error(
                    "Payment não encontrado para transaction_id: %s",
                    payment_intent_id,
                )
                raise Exception("Payment not found.")

            subscription = session.exec(
                select(Subscription).where(Subscription.id == payment.subscription_id)
            ).first()
            if not subscription:
                logger.error(
                    "Subscription não encontrada para payment_id: %s",
                    payment.id,
                )
                raise Exception("Subscription not found.")

            if subscription.is_active:
                subscription.is_active = False
                subscription.updated_at = datetime.now(timezone.utc)
                session.add(subscription)
                logger.info("Subscription %s marcada como disputed", subscription.id)

            user = session.exec(select(User).where(User.id == payment.user_id)).first()

            if not user:
                raise Exception("User not found")

            user.is_active = False
            session.add(user)
            session.commit()

            logger.exception(
                "Subscription %s marcada como disputed!!!!!", subscription.id
            )
    except Exception as e:
        session.rollback()
        logger.exception("Falha no processamento de charge.dispute.created: %s", str(e))
        raise e

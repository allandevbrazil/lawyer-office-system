import asyncio
import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db import async_session_factory
from app.models import (
    Activity,
    Case,
    CaseEvent,
    CaseParty,
    Client,
    Document,
    Firm,
    FirmConfig,
    Invoice,
    InvoiceItem,
    Service,
    User,
    UserRole,
    UserStatus,
    WikiArticle,
    WikiStatus,
)


async def seed_initial_master() -> None:
    settings = get_settings()
    if not settings.initial_master_email or not settings.initial_master_password:
        raise ValueError("INITIAL_MASTER_EMAIL and INITIAL_MASTER_PASSWORD are required")

    async with async_session_factory() as session:
        existing_user = await session.scalar(
            select(User).where(User.email == settings.initial_master_email.lower())
        )
        if existing_user:
            return

        firm = Firm(name=settings.initial_firm_name)
        session.add(firm)
        await session.flush()
        session.add(FirmConfig(firm_id=firm.id, trade_name=settings.initial_firm_name))
        session.add(
            User(
                firm_id=firm.id,
                email=settings.initial_master_email.lower(),
                password_hash=hash_password(settings.initial_master_password),
                full_name="Master",
                role=UserRole.MASTER,
                status=UserStatus.ACTIVE,
            )
        )
        await session.commit()


async def seed_demo_data() -> None:
    """Create a complete, repeatable local dataset for the authenticated demo firm."""
    settings = get_settings()
    async with async_session_factory() as session:
        master = await session.scalar(
            select(User).where(User.role == UserRole.MASTER).order_by(User.created_at)
        )
        if not master:
            await seed_initial_master()
            master = await session.scalar(
                select(User).where(User.role == UserRole.MASTER).order_by(User.created_at)
            )
        if not master:
            raise ValueError("A MASTER user is required before seeding demo data")

        firm = await session.scalar(select(Firm).where(Firm.id == master.firm_id))
        if not firm:
            raise ValueError("The MASTER user must belong to a firm")

        config = await session.scalar(select(FirmConfig).where(FirmConfig.firm_id == firm.id))
        if not config:
            session.add(
                FirmConfig(
                    firm_id=firm.id,
                    legal_name="LegalSuite Advocacia e Consultoria Ltda.",
                    trade_name="LegalSuite",
                    tax_id="12.345.678/0001-90",
                    email="contato@legalsuite.local",
                    phone="(11) 3000-2024",
                    address_json={"street": "Av. Paulista", "number": "1000", "city": "Sao Paulo", "state": "SP"},
                    settings_json={"demo_data": True},
                )
            )

        staff = await session.scalar(
            select(User).where(User.firm_id == firm.id, User.full_name == "Ana Silva")
        )
        if not staff:
            staff = User(
                firm_id=firm.id,
                email=settings.initial_employee_email.lower(),
                password_hash=hash_password(settings.initial_employee_password),
                full_name="Ana Silva",
                role=UserRole.FUNCIONARIO,
                status=UserStatus.ACTIVE,
                phone="(11) 98888-1000",
            )
            session.add(staff)
        else:
            staff.email = settings.initial_employee_email.lower()
            staff.password_hash = hash_password(settings.initial_employee_password)

        clients: list[Client] = []
        client_specs = [
            ("Mariana Costa", "PF", "mariana.costa@example.com", "123.456.789-00"),
            ("Almeida Tecnologia Ltda.", "PJ", "juridico@almeidatech.example", "12.987.654/0001-10"),
            ("Joao Pereira", "PF", "joao.pereira@example.com", "987.654.321-00"),
        ]
        for name, client_type, email, document_number in client_specs:
            client = await session.scalar(
                select(Client).where(Client.firm_id == firm.id, Client.name == name)
            )
            if not client:
                client = Client(
                    firm_id=firm.id,
                    type=client_type,
                    name=name,
                    email=email,
                    phone="(11) 97777-0000",
                    document_number=document_number,
                    notes="Cliente demonstrativo para ambiente local.",
                )
                session.add(client)
            else:
                client.email = email
            clients.append(client)

        await session.flush()

        client_login = await session.scalar(
            select(User).where(User.email == settings.initial_client_email.lower())
        )
        if not client_login:
            client_login = User(
                firm_id=firm.id,
                email=settings.initial_client_email.lower(),
                password_hash=hash_password(settings.initial_client_password),
                full_name="Mariana Costa",
                role=UserRole.CLIENTE,
                status=UserStatus.ACTIVE,
                phone="(11) 97777-0000",
            )
            session.add(client_login)
        else:
            client_login.firm_id = firm.id
            client_login.full_name = "Mariana Costa"
            client_login.role = UserRole.CLIENTE
            client_login.status = UserStatus.ACTIVE
            client_login.password_hash = hash_password(settings.initial_client_password)
        await session.flush()
        clients[0].user_id = client_login.id

        case_specs = [
            ("Ação de cobrança contratual", clients[0], "HIGH", "0012345-67.2026.8.26.0100"),
            ("Revisão de contrato de tecnologia", clients[1], "NORMAL", "0023456-78.2026.8.26.0100"),
            ("Planejamento sucessório familiar", clients[2], "URGENT", "0034567-89.2026.8.26.0100"),
        ]
        cases: list[Case] = []
        for title, client, priority, case_number in case_specs:
            case = await session.scalar(
                select(Case).where(Case.firm_id == firm.id, Case.case_number == case_number)
            )
            if not case:
                case = Case(
                    firm_id=firm.id,
                    client_id=client.id,
                    responsible_user_id=staff.id,
                    case_number=case_number,
                    title=title,
                    description=f"Processo demonstrativo de {client.name}, criado para validar o fluxo do ERP.",
                    court="Foro Central",
                    jurisdiction="Sao Paulo",
                    case_type="Civel",
                    priority=priority,
                    opened_at=datetime.now(UTC) - timedelta(days=12),
                )
                session.add(case)
            cases.append(case)

        await session.flush()

        if not await session.scalar(select(CaseParty).where(CaseParty.case_id == cases[0].id)):
            session.add_all(
                [
                    CaseParty(case_id=cases[0].id, name="Mariana Costa", role="Autora", document_number="123.456.789-00"),
                    CaseParty(case_id=cases[0].id, name="Comercial Beta S.A.", role="Reu", document_number="98.765.432/0001-11"),
                ]
            )
        if not await session.scalar(select(CaseEvent).where(CaseEvent.case_id == cases[0].id)):
            session.add_all(
                [
                    CaseEvent(case_id=cases[0].id, author_user_id=master.id, event_type="PETITION", title="Peticao inicial protocolada", description="Documento enviado ao tribunal.", occurred_at=datetime.now(UTC) - timedelta(hours=3), visibility="INTERNAL"),
                    CaseEvent(case_id=cases[0].id, author_user_id=staff.id, event_type="DOCUMENT", title="Contrato anexado", description="Contrato principal anexado ao processo.", occurred_at=datetime.now(UTC) - timedelta(days=1), visibility="CLIENT"),
                ]
            )

        service = await session.scalar(
            select(Service).where(Service.firm_id == firm.id, Service.description == "Analise e parecer contratual")
        )
        if not service:
            service = Service(firm_id=firm.id, client_id=clients[0].id, case_id=cases[0].id, description="Analise e parecer contratual", service_type="Consultoria", unit_price=Decimal("350.00"), quantity=Decimal("4"))
            session.add(service)
            await session.flush()

        invoice = await session.scalar(
            select(Invoice).where(Invoice.firm_id == firm.id, Invoice.number == "FAT-DEMO-0001")
        )
        if not invoice:
            invoice = Invoice(firm_id=firm.id, client_id=clients[0].id, case_id=cases[0].id, number="FAT-DEMO-0001", description="Honorarios advocaticios - abril", subtotal=Decimal("1400.00"), discount=Decimal("100.00"), total=Decimal("1300.00"), due_date=date.today() + timedelta(days=15), status="PENDING", issued_at=datetime.now(UTC) - timedelta(days=2))
            session.add(invoice)
            await session.flush()
            session.add(InvoiceItem(invoice_id=invoice.id, service_id=service.id, description="Analise e parecer contratual", quantity=Decimal("4"), unit_price=Decimal("350.00"), amount=Decimal("1400.00")))

        storage_root = Path(settings.local_storage_path)
        document_specs = [("Contrato_social_demo.pdf", clients[1], cases[1], b"Documento demonstrativo LegalSuite\n") , ("Peticao_inicial_demo.txt", clients[0], cases[0], b"Peticao inicial demonstrativa LegalSuite\n")]
        for file_name, client, case, content in document_specs:
            document = await session.scalar(select(Document).where(Document.firm_id == firm.id, Document.file_name == file_name))
            if not document:
                document_id = uuid.uuid4()
                storage_key = f"{firm.id}/{document_id}/{file_name}"
                target = storage_root / storage_key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                session.add(Document(id=document_id, firm_id=firm.id, client_id=client.id, case_id=case.id, uploaded_by=master.id, file_name=file_name, storage_key=storage_key, mime_type="application/pdf" if file_name.endswith(".pdf") else "text/plain", size_bytes=len(content), visibility="INTERNAL", folder="Processos", checksum=hashlib.sha256(content).hexdigest(), uploaded_at=datetime.now(UTC) - timedelta(days=1)))

        wiki_specs = [("Guia de prazos processuais", "prazos-processuais", "Prazos", "# Guia de prazos\n\nConsulte os prazos legais e registre cada movimentacao no processo."), ("Politica de documentos", "politica-documentos", "Operacao", "# Politica de documentos\n\nMantenha os arquivos organizados por cliente e processo.")]
        for title, slug, category, content in wiki_specs:
            if not await session.scalar(select(WikiArticle).where(WikiArticle.firm_id == firm.id, WikiArticle.slug == slug)):
                session.add(WikiArticle(firm_id=firm.id, author_user_id=master.id, title=title, slug=slug, content_markdown=content, category=category, status=WikiStatus.PUBLISHED, published_at=datetime.now(UTC)))

        if not await session.scalar(select(Activity).where(Activity.firm_id == firm.id, Activity.action == "DEMO_SEED")):
            session.add(Activity(firm_id=firm.id, actor_user_id=master.id, entity_type="SYSTEM", action="DEMO_SEED", description="Dados demonstrativos carregados para o ambiente local.", metadata_json={"version": 1}))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_initial_master())
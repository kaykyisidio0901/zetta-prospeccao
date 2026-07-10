import re
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.platypus.flowables import HRFlowable


_CINZA = HexColor("#4A5568")
_VERDE = HexColor("#2C7A7B")
_CLARO = HexColor("#E6FFFA")


def _estilos():
    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        "Titulo", parent=estilos["Title"],
        fontSize=20, leading=26, textColor=_VERDE,
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold",
    ))
    estilos.add(ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"],
        fontSize=9, leading=12, textColor=_CINZA,
        alignment=TA_CENTER, spaceAfter=20,
    ))
    estilos.add(ParagraphStyle(
        "Corpo", parent=estilos["Normal"],
        fontSize=10, leading=15, alignment=TA_JUSTIFY,
        spaceAfter=8, textColor=HexColor("#1A202C"),
    ))
    estilos.add(ParagraphStyle(
        "Clausula", parent=estilos["Normal"],
        fontSize=11, leading=16, fontName="Helvetica-Bold",
        textColor=_VERDE, spaceAfter=4, spaceBefore=12,
    ))
    estilos.add(ParagraphStyle(
        "Rodape", parent=estilos["Normal"],
        fontSize=7.5, leading=10, textColor=_CINZA,
        alignment=TA_CENTER,
    ))
    estilos.add(ParagraphStyle(
        "AssLabel", parent=estilos["Normal"],
        fontSize=9, leading=12, textColor=_CINZA, alignment=TA_LEFT,
    ))
    return estilos


def _cnpj_cpf_formatado(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) <= 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"
    return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"


def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _extenso(valor: float) -> str:
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f} milhão de reais".replace(".", ",")
    if valor >= 1_000:
        return f"{valor / 1_000:.0f} mil reais"
    return _fmt_brl(valor)


def gerar_pdf_contrato(
    cliente_nome: str,
    cliente_doc: str,
    valor_projeto: float,
    valor_entrada: float,
    prazo_dias: int,
) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
    )
    est = _estilos()
    elementos = []

    # Header
    elementos.append(Paragraph("KYSOUND TECNOLOGIA", est["Titulo"]))
    elementos.append(Paragraph("CNPJ: 00.000.000/0001-00", est["Subtitulo"]))
    elementos.append(HRFlowable(
        width="100%", thickness=1, color=_VERDE,
        spaceAfter=16, spaceBefore=4,
    ))

    # Title
    elementos.append(Paragraph(
        "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO WEB",
        est["Titulo"],
    ))
    elementos.append(Paragraph(
        f"Contrato nº KY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        est["Subtitulo"],
    ))
    elementos.append(Spacer(1, 0.4 * cm))

    # Parties
    hoje = datetime.now().strftime("%d/%m/%Y")
    elementos.append(Paragraph(
        f"Pelo presente instrumento particular, de um lado <b>KYSOUND TECNOLOGIA</b>, "
        f"inscrita sob CNPJ 00.000.000/0001-00, doravante denominada <b>CONTRATADA</b>, "
        f"e de outro lado <b>{cliente_nome}</b>, inscrito(a) sob CPF/CNPJ "
        f"<b>{_cnpj_cpf_formatado(cliente_doc)}</b>, doravante denominado <b>CONTRATANTE</b>, "
        f"têm entre si justo e acordado o presente Contrato de Prestação de Serviços "
        f"de Desenvolvimento Web, que se regerá pelas cláusulas seguintes.",
        est["Corpo"],
    ))

    # Cláusulas
    clausulas = [
        (
            "CLÁUSULA PRIMEIRA — OBJETO",
            "A CONTRATADA se obriga a desenvolver, implementar e entregar o projeto "
            "de website/plataforma digital conforme especificações técnicas acordadas "
            "entre as partes, incluindo design responsivo, otimização para mecanismos "
            "de busca (SEO básico), hospedagem inicial por 12 meses e suporte técnico "
            "pelo período de 30 dias corridos após a entrega."
        ),
        (
            "CLÁUSULA SEGUNDA — VALOR E FORMA DE PAGAMENTO",
            f"O valor total do presente contrato é de <b>{_fmt_brl(valor_projeto)} "
            f"({_extenso(valor_projeto)})</b>. O CONTRATANTE pagará à CONTRATADA "
            f"o valor de <b>{_fmt_brl(valor_entrada)} ({_extenso(valor_entrada)})</b> "
            f"a título de sinal, no ato da assinatura deste contrato. O saldo restante "
            f"de <b>{_fmt_brl(valor_projeto - valor_entrada)}</b> será pago em parcelas "
            f"iguais e consecutivas, vencendo-se a primeira 30 dias após a entrega "
            f"do projeto."
        ),
        (
            "CLÁUSULA TERCEIRA — PRAZO DE EXECUÇÃO",
            f"O prazo para conclusão e entrega do projeto é de <b>{prazo_dias} "
            f"({prazo_dias} dias corridos)</b>, contados a partir do recebimento "
            f"do sinal e de todos os materiais necessários ao desenvolvimento "
            f"(textos, imagens, logotipos, etc.) por parte do CONTRATANTE. "
            f"Qualquer atraso na entrega dos materiais pelo CONTRATANTE implicará "
            f"prorrogação automática do prazo pelo mesmo período."
        ),
        (
            "CLÁUSULA QUARTA — OBRIGAÇÕES DA CONTRATADA",
            "A CONTRATADA se compromete a: (a) desenvolver o site conforme "
            "especificações acordadas; (b) entregar o projeto no prazo estipulado; "
            "(c) prestar suporte técnico corretivo por 30 dias após a entrega; "
            "(d) manter sigilo absoluto sobre informações do CONTRATANTE; "
            "(e) fornecer manual básico de administração do site."
        ),
        (
            "CLÁUSULA QUINTA — OBRIGAÇÕES DO CONTRATANTE",
            "O CONTRATANTE se compromete a: (a) fornecer todos os materiais "
            "necessários ao desenvolvimento; (b) aprovar as etapas do projeto "
            "em até 48 horas após a apresentação; (c) efetuar os pagamentos "
            "nas datas acordadas; (d) não copiar, distribuir ou ceder "
            "os códigos-fonte a terceiros sem autorização."
        ),
        (
            "CLÁUSULA SEXTA — DIREITOS AUTORAIS E PROPRIEDADE INTELECTUAL",
            "Após o pagamento integral do valor ajustado, os direitos autorais "
            "sobre o design e o conteúdo textual passarão a ser do CONTRATANTE. "
            "Os códigos-fonte e frameworks utilizados permanecem como propriedade "
            "da CONTRATADA, sendo cedidos ao CONTRATANTE sob licença de uso "
            "perpétua para o funcionamento do site. É vedada a engenharia reversa "
            "ou revenda dos códigos sem autorização expressa da CONTRATADA."
        ),
        (
            "CLÁUSULA SÉTIMA — RESCISÃO",
            "Em caso de inadimplência por prazo superior a 30 dias, a CONTRATADA "
            "poderá suspender os serviços e rescindir o contrato, retendo os "
            "valores já pagos como indenização mínima. O CONTRATANTE poderá "
            "rescindir o contrato a qualquer momento, mediante notificação com "
            "30 dias de antecedência, ficando obrigado ao pagamento dos serviços "
            "já prestados até a data da rescisão."
        ),
        (
            "CLÁUSULA OITAVA — FORO",
            "Fica eleito o foro da comarca de São Paulo/SP para dirimir "
            "quaisquer dúvidas oriundas deste contrato, com renúncia expressa "
            "de qualquer outro, por mais privilegiado que seja."
        ),
    ]

    for titulo, texto in clausulas:
        elementos.append(Paragraph(titulo, est["Clausula"]))
        elementos.append(Paragraph(texto, est["Corpo"]))

    elementos.append(Spacer(1, 0.6 * cm))
    elementos.append(HRFlowable(
        width="100%", thickness=0.5, color=_CINZA,
        spaceAfter=20, spaceBefore=4,
    ))

    # Assinaturas
    elementos.append(Paragraph(
        f"E, por estarem assim justos e contratados, assinam o presente "
        f"instrumento em 2 (duas) vias de igual teor e forma.",
        est["Corpo"],
    ))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        f"São Paulo, {hoje}.",
        est["Corpo"],
    ))
    elementos.append(Spacer(1, 1.2 * cm))

    # Tabela de assinaturas
    ass_data = [
        [
            Paragraph(
                "____________________________________<br/>"
                "<b>KYSOUND TECNOLOGIA</b><br/>"
                "<font size=8>CONTRATADA</font>",
                est["AssLabel"],
            ),
            Paragraph(
                "____________________________________<br/>"
                f"<b>{cliente_nome.upper()}</b><br/>"
                "<font size=8>CONTRATANTE</font>",
                est["AssLabel"],
            ),
        ],
    ]
    ass_tab = Table(ass_data, colWidths=[8 * cm, 8 * cm])
    ass_tab.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elementos.append(ass_tab)
    elementos.append(Spacer(1, 1.5 * cm))

    # Footer
    elementos.append(HRFlowable(
        width="100%", thickness=0.5, color=_CINZA,
        spaceAfter=6, spaceBefore=4,
    ))
    elementos.append(Paragraph(
        "KYSOUND TECNOLOGIA — CNPJ 00.000.000/0001-00 — contato@kysound.com",
        est["Rodape"],
    ))

    doc.build(elementos)
    buf.seek(0)
    return buf

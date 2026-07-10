import random
import re


def _abertura():
    fmt = random.choice([
        "Olá! Tudo bem?",
        "Olá, {saudacao}?",
        "Oi {saudacao2}?",
        "{saudacao3}, tudo {estado}?",
    ])
    return fmt.format(
        saudacao=random.choice(["tudo certo", "tudo bem", "boa tarde"]),
        saudacao2=random.choice(["tudo joia", "boa tarde", "como vai"]),
        saudacao3=random.choice(["Olá", "Oi", "Boa tarde"]),
        estado=random.choice(["certo com vocês", "bem por aí", "em ordem"]),
    )


def _elogio(nome_empresa, nicho):
    variante = random.choice(["a", "b", "c", "d"])
    if variante == "a":
        elogio = random.choice([
            "isso mostra que vocês são referência na área",
            "parabéns pelo trabalho de vocês",
            "isso prova que entregam um bom serviço",
        ])
        return (
            f"Vi que a {nome_empresa} tem uma presença bem legal no Google Maps — {elogio}. "
            f"Analisando o mercado de {nicho}, reparei que muitas empresas do ramo "
            f"estão perdendo clientes por ainda não terem um site profissional "
            f"otimizado para celular. Enquanto isso, quem já tem site "
            f"acaba levando vantagem e faturando mais."
        )
    if variante == "b":
        return (
            f"Primeiro, parabéns pelas avaliações que a {nome_empresa} tem no Google Maps! "
            f"Pesquisando o segmento de {nicho}, notei algo preocupante: "
            f"muitos negócios bem avaliados estão perdendo dinheiro por não terem "
            f"um site próprio que converta visitantes em clientes de verdade. "
            f"Quem tem site bem feito sai na frente."
        )
    if variante == "c":
        return (
            f"A {nome_empresa} se destaca no Google Maps e isso é um ótimo sinal! "
            f"Mas analisando a concorrência de {nicho}, percebi que "
            f"a maioria dos players que estão crescendo mais rápido "
            f"já investiram em um site profissional otimizado. "
            f"Sem site, o negócio fica refém das redes sociais e perde "
            f"quem pesquisa direto no Google por serviços como os de vocês."
        )
    return (
        f"Vocês mandam bem no Google Maps, a {nome_empresa} tem um nome forte "
        f"no segmento de {nicho}. O problema é que muitos clientes em potencial "
        f"estão caindo nos concorrentes — simplesmente porque eles têm site "
        f"e vocês não. Um site profissional hoje é o cartão de visitas "
        f"que mais vende."
    )


def _gancho(nicho):
    fmt = random.choice([
        "Pensando nisso, desenvolvi um modelo visual de site focado em conversão "
        "desenhado especificamente para o segmento de {nicho}.",
        "Criei um conceito de site moderno, pensado para o segmento de {nicho}, "
        "que já nasce pronto para converter visitantes em clientes.",
        "Preparei um layout de site focado em resultado para o ramo de {nicho} — "
        "algo visual, direto e que passa credibilidade na hora.",
        "Desenvolvi um protótipo de site exclusivo para negócios de {nicho}, "
        "com design pensado para gerar mais contatos e vendas.",
    ])
    return fmt.format(nicho=nicho)


def _cta_permissao(nome_empresa):
    fmt = random.choice([
        "Se eu te mandar uma demonstração de 1 minuto desse design "
        "que pensei para vocês, você daria uma olhada?",
        "Posso te enviar um preview rápido desse modelo? "
        "Só 1 minutinho pra ver se faz sentido pra {empresa}.",
        "Te interessa dar uma espiada no conceito que montei? "
        "Se sim, me manda um 'ok' que eu envio o link.",
        "Gostaria de ver uma amostra do que preparei? "
        "Se você me autorizar, eu te mostro em 1 minuto.",
    ])
    return fmt.format(empresa=nome_empresa)


def _dados_impacto(nome_empresa, nicho):
    variante = random.choice(["a", "b", "c", "d"])
    if variante == "a":
        return (
            f"Empresas de {nicho} que investem em um site focado em conversão "
            f"aumentam em até 40% seus agendamentos e vendas — sem depender "
            f"de anúncios ou de terceiros. Ter um site próprio é ter um "
            f"vendedor trabalhando 24 horas por dia pra você."
        )
    if variante == "b":
        return (
            f"Sabia que mais de 70% das pessoas pesquisam no Google antes de "
            f"contratar um serviço de {nicho}? Pois é. Sem site, "
            f"a {nome_empresa} simplesmente não aparece pra essa galera toda. "
            f"É cliente que vai direto pra concorrência."
        )
    if variante == "c":
        return (
            f"Um dado interessante: negócios de {nicho} com site profissional "
            f"conseguem cobrar, em média, 30% mais caro pelos serviços. "
            f"Isso porque o site passa credibilidade e justifica o valor. "
            f"Sem site, o cliente sempre desconfia e barganha."
        )
    return (
        f"Enquanto a {nome_empresa} depende do Google Maps e Instagram "
        f"para ser encontrada, seus concorrentes estão capturando clientes "
        f"24h por dia através do site. O melhor momento para criar um site "
        f"foi ontem. O segundo melhor é hoje."
    )


def _reforco(nicho):
    fmt = random.choice([
        "O modelo exclusivo que preparei pro segmento de {nicho} "
        "resolve exatamente esse problema. É rápido de implementar "
        "e você vê o resultado em poucas semanas. Quer dar uma olhada?",
        "Meu modelo de site pra {nicho} foi desenhado pra "
        "transformar visitantes em leads de forma automática. "
        "Posso te mostrar como funciona em 1 minutinho.",
        "O design que criei pro seu ramo é focado em conversão — "
        "não é só um site bonito, é uma máquina de captar clientes. "
        "Me deixa te mostrar rapidinho?",
    ])
    return fmt.format(nicho=nicho)


def _call(nome_empresa, nicho):
    fmt = random.choice([
        "Que tal uma call super rápida de 5 minutos? "
        "Sem compromisso. Alinhamos o escopo que a {empresa} precisa, "
        "eu mostro como ficaria o design exclusivo pro segmento de {nicho} "
        "e você decide se faz sentido.",
        "Topa 5 minutinhos amanhã ou depois? Posso te mostrar "
        "como funciona o processo, o design exclusivo, a otimização de "
        "velocidade pro Google e o botão de WhatsApp integrado. "
        "Rápido e sem compromisso.",
    ])
    return fmt.format(empresa=nome_empresa, nicho=nicho)


def _beneficios(nicho):
    fmt = random.choice([
        "Você vai ver como é simples: design exclusivo, "
        "site otimizado pra velocidade no Google e botão de WhatsApp "
        "integrado pra seus clientes te chamarem na hora.",
        "Você terá um site com visual profissional, carregamento rápido "
        "(isso o Google ama) e WhatsApp acoplado pra fechar vendas "
        "diretamente pelo navegador. Tudo pensado pra {nicho}.",
        "O projeto inclui identidade visual exclusiva, otimização de "
        "performance para ranquear no Google e integração direta com "
        "WhatsApp. Em 5 minutos eu te mostro o escopo completo.",
    ])
    return fmt.format(nicho=nicho)


def _fechamento():
    return random.choice([
        "Vamos nessa?",
        "Pode ser?",
        "Te atende?",
        "Topa esse bate-papo rápido?",
    ])
def gerar_funil_vendas(nome_empresa: str, nicho: str) -> tuple:
    """Gera 3 mensagens para o funil de vendas B2B (Google Maps).

    Returns:
        (msg_abordagem, msg_gancho, msg_fechamento)
    """
    if re.search(r'https?://|www\.|google\.com/maps', nicho, re.IGNORECASE):
        nicho = "geral"

    msg1 = (
        f"Olá, tudo bem por aí?\n\n"
        f"A {nome_empresa} se destaca no Google Maps e isso é um ótimo sinal! "
        f"Parabéns pelo trabalho. 📊\n\n"
        f"Mas analisando a concorrência da sua região no segmento de "
        f"[DIGITE O NICHO AQUI], percebi que a maioria dos players "
        f"que estão crescendo mais rápido já investiram em um site "
        f"profissional otimizado para celulares. Sem um site próprio "
        f"no Google, o negócio acaba deixando dinheiro na mesa e "
        f"perdendo clientes que pesquisam direto por produtos e "
        f"serviços como os de vocês.\n\n"
        f"Pensando nisso, eu desenvolvi um modelo visual de site "
        f"focado em conversão e vendas, desenhado especificamente "
        f"para o segmento de [DIGITE O NICHO AQUI].\n\n"
        f"Se eu te mandar uma demonstração rápida de 1 minuto desse "
        f"design que pensei exclusivamente para a {nome_empresa}, "
        f"você daria uma olhada para me dar sua opinião?"
    )

    msg2 = (
        f"{_dados_impacto(nome_empresa, nicho)}\n\n"
        f"{_reforco(nicho)}"
    )

    msg3 = (
        f"{_call(nome_empresa, nicho)}\n\n"
        f"{_beneficios(nicho)}\n\n"
        f"{_fechamento()}"
    )

    return msg1, msg2, msg3

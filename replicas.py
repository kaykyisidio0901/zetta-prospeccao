import re


def _detectar_objecao(resposta: str) -> str:
    r = resposta.lower().strip()

    if re.search(r'(?:quanto tempo|demora|prazo|r[áa]pido|urgente)', r):
        return "prazo"
    if re.search(r'(?:quanto|pre[cç]o|valor|custa|or[çc]amento|caro|barato)', r):
        return "preco"
    if re.search(r'(?:j[aá] tem[uo]|j[aá] tenho|j[aá] possui?|j[aá] contrat[ei]|j[aá] fiz|j[aá] tive)', r):
        return "ja_tem"
    if re.search(r'(?:n[aã]o (?:quero|preciso|tenho interesse|agora)|agora n[ãa]o|sem interesse|nada)', r):
        return "nao_agora"
    if re.search(r'(?:manda|enviar|envi[aá]|me mostra|quero ver|exemplo|case|portfolio|modelo)', r):
        return "quero_ver"
    if re.search(r'(?:quem [eé]|sobre [aae]|como funciona|o que [eé]|explica)', r):
        return "info"

    return "geral"


_REPLICAS_POR_OBJECAO = {
    "preco": (
        "Entendo que o investimento é uma preocupação importante! "
        "O valor de um site profissional parte de R$ 1.500, podendo chegar a R$ 5.000 "
        "dependendo da complexidade. Mas o mais legal é que ele se paga rápido: "
        "com apenas 2 ou 3 clientes conquistados via Google, o investimento já volta. "
        "Quer que eu monte uma proposta personalizada pra você?"
    ),
    "prazo": (
        "Fica tranquilo! Um site institucional fica pronto em 5 a 10 dias úteis. "
        "Se for uma loja virtual ou algo mais complexo, de 15 a 25 dias. "
        "E olha: enquanto o site está sendo feito, já podemos ir "
        "preparando os textos e fotos pra não perder tempo. "
        "Qual prazo você está pensando?"
    ),
    "ja_tem": (
        "Que legal que você já tem site! Muitas vezes o site atual "
        "pode estar desatualizado, lento ou com um design que não "
        "converte tão bem. Posso dar uma olhada sem compromisso "
        "e sugerir melhorias pontuais. Topa?"
    ),
    "nao_agora": (
        "Super tranquilo, entendo perfeitamente! "
        "Só não quero que você perca a oportunidade de aparecer "
        "no Google enquanto a concorrência já está lá. "
        "Posso deixar um orçamento salvo e daqui 1 ou 2 meses "
        "a gente retoma a conversa? Combinado?"
    ),
    "quero_ver": (
        "Claro! Vou te enviar alguns cases que fizemos "
        "no segmento de {segmento}. São projetos bem legais!"
    ),
    "info": (
        "Claro! A gente cria sites profissionais do zero — "
        "institucionais, lojas virtuais, landing pages, portfólios. "
        "Tudo otimizado pra aparecer no Google e funcionar "
        "perfeitamente no celular. Também cuidamos de domínio, "
        "hospedagem e manutenção se precisar. "
        "Qual desses você mais se interessou?"
    ),
    "geral": (
        "Obrigado pela resposta! Me conta uma coisa: "
        "o que você mais sentiria falta hoje pra "
        "alavancar o {segmento} online? Posso ajudar com "
        "sugestões rápidas e sinceras."
    ),
}


def gerar_replica(
    nicho: str,
    etapa: str,
    resposta_cliente: str,
) -> str:
    if not resposta_cliente.strip():
        return "O cliente não respondeu ainda. Inicie o funil pelo WhatsApp primeiro."

    objeccao = _detectar_objecao(resposta_cliente)
    texto = _REPLICAS_POR_OBJECAO.get(objeccao, _REPLICAS_POR_OBJECAO["geral"])

    if "{segmento}" in texto:
        texto = texto.replace("{segmento}", nicho or "negócio")

    return texto

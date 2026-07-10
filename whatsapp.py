import re
import urllib.parse


def limpar_numero(numero: str) -> str:
    return re.sub(r"\D", "", str(numero))


def garantir_codigo_pais(numero: str) -> str:
    if numero.startswith("55") and len(numero) >= 12:
        return numero
    return "55" + numero


def gerar_link_whatsapp(numero: str, mensagem: str) -> str:
    numero = garantir_codigo_pais(limpar_numero(numero))
    texto = urllib.parse.quote(mensagem)
    return f"https://web.whatsapp.com/send?phone={numero}&text={texto}"

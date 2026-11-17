import os
import json
import time
import random
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
random.seed(7)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=60,
    max_retries=1,
)

MODELO = "openai/gpt-oss-120b"

TEMAS = ["entrega", "comida", "preço", "atendimento", "embalagem", "aplicativo/pagamento"]

SITUACOES = {
    "entrega": {
        "bom": ["chegou antes do previsto", "entregador avisou que estava chegando e foi gentil",
                "entregador achou o endereço fácil mesmo na chuva", "pedido chegou certinho e no horário"],
        "ruim": ["atrasou muito e ninguém avisou", "entregador não achou o endereço e ficou ligando",
                 "entregador deixou na portaria errada", "app marcou como entregue mas o pedido não chegou",
                 "entregador foi grosseiro"],
        "neutro": ["chegou no horário previsto, sem nada de especial"],
    },
    "comida": {
        "bom": ["comida chegou quente e no ponto", "tempero muito bom", "porção farta",
                "ingredientes frescos"],
        "ruim": ["comida chegou fria", "veio o prato errado", "faltou item do pedido",
                 "comida sem sabor", "ingrediente estragado"],
        "neutro": ["comida normal, nem boa nem ruim", "prato veio como descrito no cardápio"],
    },
    "preço": {
        "bom": ["promoção boa e preço justo", "cupom de desconto funcionou", "frete grátis ajudou"],
        "ruim": ["taxa que não aparecia antes de fechar o pedido", "preço bem acima do restaurante",
                 "taxa de entrega alta", "porção pequena para o valor cobrado"],
        "neutro": ["preço dentro do esperado para o tipo de comida"],
    },
    "atendimento": {
        "bom": ["suporte resolveu rápido", "atendente educado resolveu o problema",
                "reembolso feito sem dificuldade"],
        "ruim": ["suporte só mandou mensagem automática", "ninguém respondeu o chat",
                 "reembolso demorou semanas", "atendente não resolveu e transferiu várias vezes"],
        "neutro": ["fui atendido pelo chat, resposta padrão e sem problemas"],
    },
    "embalagem": {
        "bom": ["embalagem bem fechada e organizada", "embalagem manteve a comida quente",
                "talheres e guardanapos incluídos"],
        "ruim": ["embalagem rasgada", "molho vazou dentro da sacola", "caixa amassada",
                 "bebida veio sem tampa"],
        "neutro": ["embalagem simples, sem problemas"],
    },
    "aplicativo/pagamento": {
        "bom": ["app fácil de usar", "pagamento por pix rápido", "acompanhar o pedido no mapa foi útil"],
        "ruim": ["app travou na hora de pagar", "cartão recusado sem explicação",
                 "cobrança duplicada", "cupom não aplicou"],
        "neutro": ["usei o app normalmente, sem erros"],
    },
}

ESTILOS = [
    "informal, com gírias",
    "muito curto, uma frase só",
    "longo, 3 frases, contando o que aconteceu",
    "digitado rápido no celular, sem acentos e sem pontuação",
    "irritado, com exclamações",
    "seco e direto",
    "como mensagem para um amigo",
    "educado e calmo",
    "formal e educado",
]
PESOS = [3, 3, 2, 3, 2, 3, 2, 3, 1]  # o formal tem peso baixo

TIPOS = {
    "positivo": "elogia o serviço, sem nenhuma reclamação",
    "negativo": "reclama do serviço, sem nenhum elogio",
    "misto": "tem uma parte boa e uma parte ruim, escritas de forma natural",
    "neutro": "relata o que aconteceu de forma factual, sem elogio, sem reclamação e sem palavras de emoção",
}

# 30 + 35 + 35 + 20 = 120 avaliações (lotes de 5)
PLANO = [("positivo", 6), ("negativo", 7), ("misto", 7), ("neutro", 4)]

usadas = set()


def sortear(tema, polaridade):
    todas = SITUACOES[tema][polaridade]
    livres = [s for s in todas if s not in usadas] or todas
    escolhida = random.choice(livres)
    usadas.add(escolhida)
    return escolhida


def montar_itens(tipo, qtd=5):
    itens = []
    for n in range(1, qtd + 1):
        estilo = random.choices(ESTILOS, weights=PESOS)[0]
        if tipo == "misto":
            tema_bom, tema_ruim = random.sample(TEMAS, 2)
            foco = (f"parte boa: {sortear(tema_bom, 'bom')}; "
                    f"parte ruim: {sortear(tema_ruim, 'ruim')}")
        else:
            tema = random.choice(TEMAS)
            polaridade = {"positivo": "bom", "negativo": "ruim", "neutro": "neutro"}[tipo]
            foco = f"situação: {sortear(tema, polaridade)}"
        itens.append(f"{n}. Avaliação que {TIPOS[tipo]}. {foco}. Estilo: {estilo}.")
    return "\n".join(itens)


def gerar_lote(tipo, tentativas=2):
    pedido = f"""Crie 5 avaliações FICTÍCIAS de clientes de um app de delivery de comida, em português do Brasil, como pessoas reais escrevem.
Siga as instruções de cada item:
{montar_itens(tipo)}

Regras: não cite o estilo nem copie as instruções; não comece com "Prezados"; evite exagerar em "super" e "top"; erros de digitação nunca podem ser parte da história.
Responda APENAS com uma lista JSON de 5 textos, sem nada além disso."""
    for n in range(tentativas):
        try:
            resposta = client.chat.completions.create(
                model=MODELO,
                messages=[{"role": "user", "content": pedido}],
                temperature=0.9,
                reasoning_effort="low",
            )
            conteudo = resposta.choices[0].message.content
            conteudo = conteudo[conteudo.find("["): conteudo.rfind("]") + 1]
            return json.loads(conteudo)
        except Exception as erro:
            print("   falhou:", str(erro)[:100], flush=True)
            time.sleep(20)
    return []


linhas = []
for tipo, lotes in PLANO:
    for i in range(lotes):
        print(tipo, "lote", i + 1, "gerando...", flush=True)
        textos = gerar_lote(tipo)
        for t in textos:
            linhas.append({"avaliacao": t, "sentimento_esperado": tipo})
        print("   pronto -", len(linhas), "no total", flush=True)
        time.sleep(5)

df = pd.DataFrame(linhas).drop_duplicates(subset="avaliacao").reset_index(drop=True)
df.insert(0, "id", df.index + 1)
df.to_csv("avaliacoes_v3.csv", index=False, encoding="utf-8-sig")
print(len(df), "avaliações salvas em avaliacoes_v3.csv")
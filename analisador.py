import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=60,
    max_retries=1,
)

MODELO = "openai/gpt-oss-120b"
ENTRADA = "avaliacoes_v3.csv"
SAIDA = "resultados_v3.csv"
PAUSA = 5  # segundos entre chamadas, para respeitar o limite do plano grátis

PEDIDO = """Você analisa avaliações de clientes de um app de delivery.
Responda APENAS com um JSON válido, sem nenhum texto extra, neste formato:
{"sentimento": "positivo" ou "negativo" ou "misto" ou "neutro",
 "temas": lista com itens escolhidos entre: "entrega", "comida", "preço", "atendimento", "embalagem", "aplicativo/pagamento"}

Use "misto" quando há uma parte boa e uma ruim, e "neutro" quando não há elogio nem reclamação.

Avaliação: """


def analisar(texto):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": PEDIDO + texto}],
        temperature=0,
    )
    conteudo = resposta.choices[0].message.content
    conteudo = conteudo[conteudo.find("{"): conteudo.rfind("}") + 1]
    return json.loads(conteudo)


def analisar_com_retentativa(texto, tentativas=3):
    for n in range(tentativas):
        try:
            return analisar(texto)
        except Exception as erro:
            print("   falhou (tentativa", n + 1, "):", str(erro)[:80], flush=True)
            time.sleep(15)
    return None


df = pd.read_csv(ENTRADA)
resultados = []
erros_seguidos = 0

for i, (_, linha) in enumerate(df.iterrows(), start=1):
    r = analisar_com_retentativa(linha["avaliacao"])
    if r is None:
        sentimento, temas = "erro", ""
        erros_seguidos += 1
    else:
        sentimento = r.get("sentimento")
        temas = ", ".join(r.get("temas", []))
        erros_seguidos = 0

    resultados.append({
        "id": linha["id"],
        "avaliacao": linha["avaliacao"],
        "sentimento": sentimento,
        "temas": temas,
        "sentimento_esperado": linha["sentimento_esperado"],
    })
    print(f"{i}/{len(df)}", sentimento, temas, flush=True)

    if erros_seguidos >= 3:
        print("3 erros seguidos: provavelmente o limite da API. Parando e salvando o que já deu certo.")
        break
    time.sleep(PAUSA)

saida = pd.DataFrame(resultados)
saida.to_csv(SAIDA, index=False, encoding="utf-8-sig")

print()
print("Resumo dos sentimentos (resposta da IA):")
print(saida["sentimento"].value_counts())

# comparação com o gabarito
valido = saida[saida["sentimento"] != "erro"]
if len(valido) > 0:
    acertos = (valido["sentimento"] == valido["sentimento_esperado"]).sum()
    print()
    print(f"Acertos: {acertos} de {len(valido)} ({acertos / len(valido):.0%})")
    print()
    print("Gabarito (linhas) x resposta da IA (colunas):")
    print(pd.crosstab(valido["sentimento_esperado"], valido["sentimento"]))

    divergentes = valido[valido["sentimento"] != valido["sentimento_esperado"]]
    divergentes.to_csv("divergencias.csv", index=False, encoding="utf-8-sig")
    print()
    print(len(divergentes), "divergências salvas em divergencias.csv")
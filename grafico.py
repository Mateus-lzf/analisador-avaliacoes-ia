import pandas as pd
import matplotlib.pyplot as plt

ARQUIVO = "resultados_v3.csv"

df = pd.read_csv(ARQUIVO)
df["temas"] = df["temas"].fillna("")
df["tema"] = df["temas"].str.split(", ")
df = df.explode("tema")
df = df[df["tema"] != ""]


def fazer_grafico(sentimento, titulo, cor, arquivo):
    filtrado = df[df["sentimento"] == sentimento]
    contagem = filtrado["tema"].value_counts()

    print(titulo)
    print(contagem)
    print()

    plt.figure(figsize=(8, 5))
    contagem.plot(kind="bar", color=cor)
    plt.title(titulo)
    plt.ylabel("Quantidade de avaliações")
    plt.xlabel("")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(arquivo, dpi=150)


fazer_grafico("negativo", "Temas mais citados nas avaliações negativas", "#EA1D2C", "temas_negativos.png")
fazer_grafico("positivo", "Temas mais citados nas avaliações positivas", "#2E9E5B", "temas_positivos.png")

plt.show()
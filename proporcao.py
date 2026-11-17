import pandas as pd
import matplotlib.pyplot as plt

ARQUIVO = "resultados_v3.csv"

df = pd.read_csv(ARQUIVO)
df["temas"] = df["temas"].fillna("")
df["tema"] = df["temas"].str.split(", ")
df = df.explode("tema")
df = df[df["tema"] != ""]

SENTIMENTOS = ["positivo", "misto", "neutro", "negativo"]

# tabela: para cada tema, quantas avaliações de cada sentimento
tabela = pd.crosstab(df["tema"], df["sentimento"])
tabela = tabela.reindex(columns=SENTIMENTOS, fill_value=0)
tabela["total"] = tabela.sum(axis=1)

# porcentagem de cada sentimento dentro de cada tema
porcentagens = tabela[SENTIMENTOS].div(tabela["total"], axis=0) * 100
porcentagens = porcentagens.sort_values("negativo", ascending=False)

# coloca o total de menções no nome de cada barra
porcentagens.index = [
    f"{tema}\n(n={tabela.loc[tema, 'total']})" for tema in porcentagens.index
]

print(tabela)
print()
print(porcentagens.round(0))

# gráfico
fig, ax = plt.subplots(figsize=(10, 6))
porcentagens.plot(
    kind="bar",
    stacked=True,
    color=["#2E9E5B", "#F5B731", "#9AA0A6", "#EA1D2C"],
    ax=ax,
)

# escreve a porcentagem dentro de cada pedaço (só nos maiores, pra não poluir)
cores_texto = ["white", "black", "black", "white"]
for container, cor in zip(ax.containers, cores_texto):
    rotulos = [f"{v:.0f}%" if v >= 5 else "" for v in container.datavalues]
    ax.bar_label(container, labels=rotulos, label_type="center",
                 color=cor, fontsize=10, fontweight="bold")

ax.set_title("Sentimento por tema (%)\nn = número de menções do tema")
ax.set_ylabel("% das avaliações")
ax.set_xlabel("")
ax.set_ylim(0, 100)
plt.xticks(rotation=0)
ax.legend(title="Sentimento", loc="center left", bbox_to_anchor=(1.02, 0.5))
plt.tight_layout()
plt.savefig("proporcao_sentimento.png", dpi=150, bbox_inches="tight")
plt.show()
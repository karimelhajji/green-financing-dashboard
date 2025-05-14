import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openai  # ou utilisez openrouter ci-dessous
import os

# === Configuration initiale ===
st.set_page_config(layout="wide", page_title="🧠 Green Finance Intelligence Dashboard")
st.title("🌍 Green Finance Intelligence Dashboard")
st.markdown("""
Ce tableau de bord vous permet de :
- Charger vos propres données publiques et privées
- Suivre les émissions de CO2, subventions, dettes et BFV
- Simuler des scénarios économiques (crise, réforme fiscale, incitations privées)
- Interagir avec un assistant IA pour arbitrer les politiques publiques
""")

# === Upload des fichiers ===
st.sidebar.header("📂 Charger les données")
public_file = st.sidebar.file_uploader("Fichier de financement public", type="csv")
private_file = st.sidebar.file_uploader("Fichier de financement privé", type="csv")

if public_file and private_file:
    df_pub = pd.read_csv(public_file, encoding="latin1")
    df_priv = pd.read_csv(private_file, encoding="latin1")

    df_pub.rename(columns=lambda x: x.strip(), inplace=True)
    df_priv.rename(columns=lambda x: x.strip(), inplace=True)

    df = pd.merge(df_pub, df_priv, on=["Pays", "Année"], how="inner", suffixes=("_pub", "_priv"))

    st.success("✅ Données fusionnées avec succès")
    st.dataframe(df.head())

    # === Calcul du Besoin de Financement Vert ===
    CUC = 80  # €/tonne CO2
    df["BFV (Mds €)"] = (
        df["Emission_CO2(Mt)"] * CUC / 1000
        - df["Subventions_vertes (en Milliards €)"]
        - df["Recettes_fiscales_env (en Milliards €)"]
    )

    df["Dette_sur_PIB"] = df["Dette_publique( en % du PIB )"]
    df["Espace_budgétaire"] = df["Dette_sur_PIB"] < 90

    # === Visualisation double axe ===
    country_focus = st.selectbox("Choisir un pays pour visualiser", sorted(df["Pays"].unique()))
    df_focus = df[df["Pays"] == country_focus]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    sns.barplot(x="Année", y="BFV (Mds €)", data=df_focus, ax=ax1, color="seagreen")
    sns.lineplot(x="Année", y="Emission_CO2(Mt)", data=df_focus, ax=ax2, color="crimson", marker="o")

    ax1.set_ylabel("BFV (Mds €)", color="seagreen")
    ax2.set_ylabel("Émissions CO2 (Mt)", color="crimson")
    ax1.set_title(f"{country_focus} - Besoin de Financement Vert & CO2")
    st.pyplot(fig)

    # === Statistiques résumées ===
    st.subheader("📊 Résumé par pays")
    summary = df.groupby("Pays")["BFV (Mds €)"].mean().sort_values(ascending=False)
    st.dataframe(summary)

    # === Simulations de scénarios ===
    st.subheader("🔮 Simulation de Scénarios")
    scenario = st.selectbox("Choisir un scénario", [
        "Réforme fiscale (taxe Zucman, 1pt TVA)",
        "Crise de la dette (perte de confiance)",
        "Retrait de l'État & incitation privée"
    ])

    if scenario == "Réforme fiscale (taxe Zucman, 1pt TVA)":
        st.info("Hypothèse : recettes fiscales environnementales +10% dès 2025")
        df.loc[df["Année"] >= 2025, "Recettes_fiscales_env (en Milliards €)"] *= 1.10
    elif scenario == "Crise de la dette (perte de confiance)":
        st.warning("Hypothèse : dette publique augmente +5pts à partir de 2025")
        df.loc[df["Année"] >= 2025, "Dette_publique( en % du PIB )"] += 5
    elif scenario == "Retrait de l'État & incitation privée":
        st.error("Hypothèse : subventions baissent -20%, investissements privés +30%")
        df.loc[df["Année"] >= 2025, "Subventions_vertes (en Milliards €)"] *= 0.8
        df.loc[df["Année"] >= 2025, "Investissements_Privés"] *= 1.3

    # Recalcul BFV après scénario
    df["BFV (Mds €)"] = (
        df["Emission_CO2(Mt)"] * CUC / 1000
        - df["Subventions_vertes (en Milliards €)"]
        - df["Recettes_fiscales_env (en Milliards €)"]
    )

    # Nouveau graphe après scénario
    fig2, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    df_focus = df[df["Pays"] == country_focus]
    sns.barplot(x="Année", y="BFV (Mds €)", data=df_focus, ax=ax1, color="teal")
    sns.lineplot(x="Année", y="Investissements_Privés", data=df_focus, ax=ax2, color="orange", marker="o")

    ax1.set_ylabel("BFV (Mds €)", color="teal")
    ax2.set_ylabel("Invest. Privés (Mds €)", color="orange")
    ax1.set_title(f"{country_focus} - BFV & Investissements privés (après scénario)")
    st.pyplot(fig2)

    # === Chat IA (copilote) ===
    st.subheader("🤖 Copilote IA (politique verte)")
    user_input = st.text_input("Pose ta question à l'IA (ex: comment optimiser le financement vert en France ?) :")

    if user_input:
        openai.api_key = st.secrets["OPENAI_API_KEY"]  # ou utilise OpenRouter
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en finance publique verte et transition énergétique."},
                    {"role": "user", "content": user_input}
                ]
            )
            st.chat_message("ai").markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Erreur IA : {e}")

else:
    st.info("Veuillez importer les deux fichiers pour commencer l'analyse.")

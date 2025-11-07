import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    return mo,


@app.cell
def __(mo):
    mo.md(
        r"""
        3 datasets

            | Title | Description | Link |
            | --- | --- | --- |
            | INE Population | População residente (N.º) por Local de residência à data dos Censos [2021] (NUTS - 2013), Sexo, Grupo etário e Nacionalidade | https://tabulador.ine.pt/indicador/?id=0011627 |
            | INE Income per municipality | Income per municipality | https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y |
            | EREDES | Location by region of connection points for Electric Vehicle Charging Stations. Information on the number of connection points for charging stations and maximum admissible connection power. | https://e-redes.opendatasoft.com/explore/dataset/postos_carregamento_ves/information/ |
        """
    )
    return


@app.cell
def __():
    import pandas as pd
    from ydata_profiling import ProfileReport
    return ProfileReport, pd


@app.cell
def __(pd):
    # Warning
    # Donwload "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder named 'data' in the repository root

    url_INE = "data/ERendimentoNLocal2023.xlsx"
    df_INE = pd.read_excel(url_INE, sheet_name="Agregados_pub_2023", header=1)

    #profile_INE = ProfileReport(df_INE, title="Profiling Report INE")
    #profile_INE.to_file("reports/profile_INE.html")

    df_INE = df_INE[df_INE["Nível territorial"] == "Município"]
    df_INE
    return df_INE, url_INE


@app.cell
def __(pd):
    # Income per municipality

    # Warning
    # Donwload "https://tabulador.ine.pt/indicador/?id=0011627" and put it in a folder named 'data' in the repository root

    url_INE_income = "data/ine_indicador_0011627.csv"
    df_INE_income = pd.read_csv(url_INE_income, sep=";")

    #profile_INE_income = ProfileReport(
    #    df_INE_income, title="Profiling Report INE Income"
    #)
    #profile_INE_income.to_file("reports/profile_INE_income.html")

    df_INE_income
    return df_INE_income, url_INE_income


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")

    #profile_EREDES = ProfileReport(df_EREDES, title="Profiling Report EREDES")
    #profile_EREDES.to_file("reports/profile_EREDES.html")

    df_EREDES
    return df_EREDES, url_EREDES


if __name__ == "__main__":
    app.run()

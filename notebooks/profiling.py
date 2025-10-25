import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    import pandas as pd
    from ydata_profiling import ProfileReport
    return ProfileReport, pd


@app.cell
def __(pd):
    url_INE = "data/ERendimentoNLocal2023.xlsx" # Donwload "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder called data in the repository
    df_INE = pd.read_excel(url_INE, sheet_name="Agregados_pub_2023")
    df_INE
    return df_INE, url_INE


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")
    df_EREDES
    return df_EREDES, url_EREDES


@app.cell
def __(ProfileReport, df_EREDES):
    profile_EREDES = ProfileReport(df_EREDES, title="Profiling Report EREDES")
    profile_EREDES.to_file("reports/profile_EREDES.html")
    return profile_EREDES,


@app.cell
def __(ProfileReport, df_INE):
    profile_INE = ProfileReport(df_INE, title="Profiling Report INE")
    profile_INE.to_file("reports/profile_INE.html")
    return profile_INE,


if __name__ == "__main__":
    app.run()

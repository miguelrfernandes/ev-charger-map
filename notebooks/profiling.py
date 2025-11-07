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
    # Warning
    # Donwload "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder named 'data' in the repository root

    url_INE = "data/ERendimentoNLocal2023.xlsx" 
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
def __(pd):
    # Income per municipality

    # Warning
    # Donwload "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder named 'data' in the repository root

    url_INE_income = "data/ine_indicador_0011627.csv" 
    df_INE_income = pd.read_csv(url_INE_income)
    df_INE_income

                           
    return df_INE_income, url_INE_income


if __name__ == "__main__":
    app.run()

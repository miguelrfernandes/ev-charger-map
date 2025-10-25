import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    import pandas as pd
    from ydata_profiling import ProfileReport
    return ProfileReport, pd


@app.cell
def __():
    # url_INE = "" # TODO: Add url
    # df_INE = pd.read_csv(url_INE, sep=";")
    return


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")
    return df_EREDES, url_EREDES


@app.cell
def __(ProfileReport, df_EREDES):
    profile_EREDES = ProfileReport(df_EREDES, title="Profiling Report EREDES")
    profile_EREDES.to_file("reports/profile_EREDES.html")
    return profile_EREDES,


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    import pandas as pd
    return pd,


@app.cell
def __(pd):
    url_INE = "" # TODO: Add url
    df_INE = pd.read_csv(url_INE, sep=";")
    return df_INE, url_INE


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")
    return df_EREDES, url_EREDES


@app.cell
def __():
    from ydata_profiling import ProfileReport
    # TODO use y_profiling
    dataset_name = "postos_carregamento_ves"
    minimal = True
    mode = "minimal"
    output_path = None
    return ProfileReport, dataset_name, minimal, mode, output_path


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()

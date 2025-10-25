import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    from pathlib import Path
    import time
    from ydata_profiling import ProfileReport
    import pandas as pd

    url = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df = pd.read_csv(url, sep=";")

    dataset_name = "postos_carregamento_ves"
    minimal = True
    mode = "minimal"
    output_path = None
    return (
        Path,
        ProfileReport,
        dataset_name,
        df,
        minimal,
        mode,
        output_path,
        pd,
        time,
        url,
    )


@app.cell
def __(df):
    df
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()

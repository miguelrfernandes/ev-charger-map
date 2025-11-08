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

            | Title | Description | Source |
            | --- | --- | --- |
            | Population | População residente (N.º) por Local de residência à data dos Censos [2021] (NUTS - 2013), Sexo, Grupo etário e Nacionalidade | [INE](https://censos.ine.pt/xportal/xmain?xpid=INE&xpgid=ine_indicadores&userLoadSave=Load&userTableOrder=13050&tipoSeleccao=1&contexto=pq&selTab=tab1&submitLoad=true&xlang=pt) |
            | Income | Income per municipality | [INE](https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y) |
            | EV Stations | Location by region of connection points for Electric Vehicle Charging Stations. Includes the number of connection points for charging stations. | [EREDES](https://e-redes.opendatasoft.com/explore/dataset/postos_carregamento_ves/information/) |

        
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
    # Income
    # Donwload "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder named 'data' in the repository root

    url_INE = "data/ERendimentoNLocal2023.xlsx"
    df_INE = pd.read_excel(url_INE, sheet_name="Agregados_pub_2023", header=1)

    #profile_INE = ProfileReport(df_INE, title="Profiling Report INE")
    #profile_INE.to_file("reports/profile_INE.html")

    # Filter
    df_INE = df_INE[df_INE["Nível territorial"] == "Município"]

    # Rename Nível territorial to Concelho
    df_INE = df_INE.rename(columns={"Designação": "Concelho"})

    # Only keep desired columns
    df_INE = df_INE[["Concelho", "Rendimento bruto declarado"]]
    df_INE
    return df_INE, url_INE


@app.cell
def __(pd):
    # Population Density
    # Download "https://tabulador.ine.pt/indicador/?id=0011627" and put it in a folder named 'data' in the repository root

    # Load the CSV file, skipping the metadata header rows

    url_INE_densidade = "data/ine_densidade_populacional.csv"

    df_INE_densidade = pd.read_csv(
        url_INE_densidade,
        sep=";",
        skiprows=7,  # Skip metadata lines
        decimal=",",  # Portuguese CSV uses comma as decimal separator
        encoding="latin-1",  # Portuguese INE files use latin-1 encoding
    )

    #profile_INE_densidade = ProfileReport(
    #    df_INE_densidade, title="Profiling Report INE Income"
    #)
    #profile_INE_densidade.to_file("reports/profile_INE_densidade.html")

    # The CSV has 7 columns
    # Columns: Year, Region, Density, Cidades, Freguesias, Vilas, Unnamed
    column_mapping = {
        df_INE_densidade.columns[0]: "Ano",
        df_INE_densidade.columns[1]: "Região",
        df_INE_densidade.columns[2]: "Densidade_Populacional_km2",
        df_INE_densidade.columns[4]: "Freguesias",
    }

    # Select and rename columns (excluding the last Unnamed column)
    df_INE_densidade = df_INE_densidade[list(column_mapping.keys())].rename(
        columns=column_mapping
    )

    # Extract NUTS code from Região column (format: "code: Name")
    df_INE_densidade["Código_NUTS"] = df_INE_densidade["Região"].str.extract(r"^([^:]+):")
    df_INE_densidade["Região"] = df_INE_densidade["Região"].str.replace(
        r"^[^:]+:\s*", "", regex=True
    )

    # Remove rows where Região is null
    df_INE_densidade = df_INE_densidade[df_INE_densidade["Região"].notna()]

    # Replace 'x' values with NaN
    df_INE_densidade = df_INE_densidade.replace("x", pd.NA)

    # Fix densidade values: replace commas with periods for proper float conversion
    # The decimal="," parameter doesn't work when the column is read as object type
    df_INE_densidade["Densidade_Populacional_km2"] = (
        df_INE_densidade["Densidade_Populacional_km2"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    # Forward fill the year column (it only appears in the first row of each year)
    df_INE_densidade["Ano"] = df_INE_densidade["Ano"].ffill()

    # Remove footer metadata rows - keep only rows where Ano is '2024'
    df_INE_densidade = df_INE_densidade[df_INE_densidade["Ano"].isin(["2024"])]

    # Remove rows where Região is null or contains metadata patterns
    df_INE_densidade = df_INE_densidade[
        df_INE_densidade["Região"].notna()
        & ~df_INE_densidade["Região"]
        .astype(str)
        .str.contains("Fonte:|Última atualização|Dimensão", na=False)
    ]

    # Convert numeric columns to proper numeric types
    for col in ["Densidade_Populacional_km2",  "Freguesias"]:
        df_INE_densidade[col] = pd.to_numeric(df_INE_densidade[col], errors="coerce")

    # Convert year to integer
    df_INE_densidade["Ano"] = df_INE_densidade["Ano"].astype(int)

    # Only select Concelho
    df_INE_densidade = df_INE_densidade[df_INE_densidade['Código_NUTS'].str.len() == 7]

    # Rename região to Concelho
    df_INE_densidade = df_INE_densidade.rename(columns={"Região": "Concelho"})

    # Only keep desired columns
    df_INE_densidade = df_INE_densidade[["Concelho", "Densidade_Populacional_km2"]]

    # Display basic info
    print("Shape:", df_INE_densidade.shape)
    print("\nFirst 10 rows:")
    print(df_INE_densidade.head(10))
    print("\nLast 5 rows:")
    print(df_INE_densidade.tail())
    print("\nColumn names:")
    print(df_INE_densidade.columns.tolist())
    print("\nData types:")
    print(df_INE_densidade.dtypes)

    df_INE_densidade

    # Save cleaned data to a new CSV
    # output_file = "data/ine_densidade_populacional_clean.csv"
    # df_INE_densidade.to_csv(output_file, index=False, encoding="utf-8-sig")
    # print(f"\n✓ Cleaned data saved to {output_file}")
    return col, column_mapping, df_INE_densidade, url_INE_densidade


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")

    #profile_EREDES = ProfileReport(df_EREDES, title="Profiling Report EREDES")
    #profile_EREDES.to_file("reports/profile_EREDES.html")

    #print(unique_trimestres = df_EREDES['Trimestre'].unique())

    df_EREDES[df_EREDES["Trimestre"]=="2025T3"]

    agg_by_freguesia = df_EREDES.groupby('Freguesia').agg(
        count_rows=('Freguesia', 'size'),
        sum_pontos_de_ligacao=('Pontos de ligação para instalações de PCVE', 'sum')
    ).reset_index()

    agg_by_concelho = df_EREDES.groupby('Concelho').agg(
        count_rows=('Concelho', 'size'),
        sum_pontos_de_ligacao=('Pontos de ligação para instalações de PCVE', 'sum')
    ).reset_index()

    agg_by_concelho
    return agg_by_concelho, agg_by_freguesia, df_EREDES, url_EREDES


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()

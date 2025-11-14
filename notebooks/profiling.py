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
    df_INE = df_INE[["Concelho", "Rendimento bruto declarado médio por agregado fiscal"]]
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

    # Rename Código_NUTS to Código territorial
    # df_INE_densidade = df_INE_densidade.rename(columns={"Código_NUTS": "Código territorial"})

    # Remove first 3 digits in Código territorial
    # df_INE_densidade["Código territorial"] = df_INE_densidade["Código territorial"].str[3:]

    # Only keep desired columns
    df_INE_densidade = df_INE_densidade[["Concelho", "Densidade_Populacional_km2"]]#, "Código territorial"]]

    df_INE_densidade
    return col, column_mapping, df_INE_densidade, url_INE_densidade


@app.cell
def __(pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES = pd.read_csv(url_EREDES, sep=";")

    #profile_EREDES = ProfileReport(df_EREDES, title="Profiling Report EREDES")
    #profile_EREDES.to_file("reports/profile_EREDES.html")
    df_EREDES
    # Rename CodDistritoConcelho to Código territorial
    df_EREDES = df_EREDES.rename(columns={"CodDistritoConcelho": "Código territorial"})

    # Only keep latest quarter
    df_EREDES[df_EREDES["Trimestre"]=="2025T3"]
    df_EREDES
    return df_EREDES, url_EREDES


@app.cell
def __(df_EREDES):
    # Fix typos in EREDES
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Castro daire", "Castro Daire")
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Miranda do douro", "Miranda do Douro")
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Freixo de Espada \u00c0 Cinta", "Freixo de Espada \u00e0 Cinta")

    df_EREDES_agg = df_EREDES.groupby('Concelho').agg(
        count_rows=('Concelho', 'size'),
        sum_pontos_de_ligacao=('Pontos de ligação para instalações de PCVE', 'sum')
    ).reset_index()

    df_EREDES_agg
    return df_EREDES_agg,


@app.cell
def __(df_EREDES_agg, df_INE, df_INE_densidade):
    # Join all three dataframes on 'Concelho'
    join_df = df_INE.merge(
        df_INE_densidade, 
        on='Concelho', 
        how='inner'
    ).merge(
        df_EREDES_agg, 
        on='Concelho', 
        how='inner'
    )

    # Rename columns for clarity
    join_df = join_df.rename(columns={
        'count_rows': 'num_charging_stations',
        'sum_pontos_de_ligacao': 'total_charging_points'
    })

    join_df
    return join_df,


@app.cell
def __(df_EREDES_agg, df_INE, df_INE_densidade, join_df):
    # Identify lost concelhos
    # lost from df_INE
    lost_from_INE = df_INE[~df_INE['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()
    # lost from df_INE_densidade
    lost_from_densidade = df_INE_densidade[~df_INE_densidade['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()
    # lost from df_EREDES_agg
    lost_from_EREDES = df_EREDES_agg[~df_EREDES_agg['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()

    result = {
        'joined_dataframe': join_df,
        'lost_from_INE': lost_from_INE,
        'lost_from_INE_densidade': lost_from_densidade,
        'lost_from_EREDES': lost_from_EREDES
    }

    result
    return lost_from_EREDES, lost_from_INE, lost_from_densidade, result


@app.cell
def __(join_df):
    plot_df = join_df.copy()
    plot_df['rank_stations'] = join_df['num_charging_stations'].rank(ascending=True, method='first')
    plot_df['rank_points'] = join_df['total_charging_points'].rank(ascending=True, method='first')
    plot_df['rank_density'] = join_df['Densidade_Populacional_km2'].rank(ascending=True, method='first')
    plot_df['rank_income'] = join_df['Rendimento bruto declarado médio por agregado fiscal'].rank(ascending=True, method='first')
    plot_df
    return plot_df,


@app.cell
def __(plot_df, plt):
    # Population density <---> charging points

    # Select top municipalities by one metric
    _top_n_density = 10
    _df_density_plot = plot_df.nlargest(_top_n_density, 'rank_points')[
        ['Concelho', 'rank_density', 'rank_points', 'Densidade_Populacional_km2', 'total_charging_points']
    ]

    # Create figure
    _fig_density, _ax_density = plt.subplots(figsize=(6, 10))

    # Rank total_charging_points adjusted
    _df_density_plot['rank_density_adjusted'] = _df_density_plot.apply(
        lambda r: r['rank_density'] if r['rank_density'] >= 279 - _top_n_density 
                    else 279 - _top_n_density - 1 - sum((_df_density_plot['rank_density'] < 279 - _top_n_density) & 
                                                          (_df_density_plot['rank_density'] > r['rank_density'])),
        axis=1
    )

    # Plot lines for each municipality
    for _i, _r in _df_density_plot.iterrows():
        _ax_density.plot([0, 1], [_r['rank_points'], _r['rank_density_adjusted']], 
                'o-', linewidth=2, markersize=8, alpha=0.7)
        
        # Add labels on the left
        _ax_density.text(-0.05, _r['rank_points'], 
                f"{_r['Concelho']}: {_r['total_charging_points']:.2f} ({int(279 - _r['rank_points'])}º)", 
                ha='right', va='center', fontsize=10)
        
        # Add labels on the right
        _ax_density.text(1.05, _r['rank_density_adjusted'], 
                f"{_r['Densidade_Populacional_km2']:.1f}/km² ({int(279 - _r['rank_density'])}º)", 
                ha='left', va='center', fontsize=10)

    # Customize plot
    _ax_density.set_xlim(-0.3, 1.3)
    _ax_density.set_xticks([0, 1])
    _ax_density.set_xticklabels(['Number of\nCharging Points', 'Population Density'], 
                        fontsize=12, fontweight='bold')
    _ax_density.spines['top'].set_visible(False)
    _ax_density.spines['right'].set_visible(False)
    _ax_density.spines['bottom'].set_visible(False)
    _ax_density.spines['left'].set_visible(False)
    _ax_density.yaxis.set_visible(False)
    _ax_density.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.show()
    return


@app.cell
def __(plot_df):
    import matplotlib.pyplot as plt

    # Select top municipalities by one metric
    top_n = 10
    df_plot = plot_df.nlargest(top_n, 'rank_points')[['Concelho', 'rank_points', 'rank_income', 'Rendimento bruto declarado médio por agregado fiscal', 'total_charging_points']]

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 10))

    # Rank income adjusted - those in top 10 get their reverse rank (265, 264...), others get 11, 12, 13...
    df_plot['rank_income_adjusted'] = df_plot.apply(
        lambda row: row['rank_income'] if row['rank_income'] >= 279 - top_n 
                    else 279 - top_n - 1 - sum((df_plot['rank_income'] < 279 - top_n) & (df_plot['rank_income'] > row['rank_income'])),
        axis=1
    )

    # Plot lines for each municipality
    for idx, row in df_plot.iterrows():
        ax.plot([0, 1], [row['rank_points'], row['rank_income_adjusted']], 
                'o-', linewidth=2, markersize=8, alpha=0.7)
        
        # Add labels on the left
        ax.text(-0.05, row['rank_points'], 
                f"{row['Concelho']}: {row['total_charging_points']} ({int(279 - row['rank_points'])}º)", 
                ha='right', va='center', fontsize=10)
        
        # Add labels on the right
        ax.text(1.05, row['rank_income_adjusted'], 
                f"{row['Rendimento bruto declarado médio por agregado fiscal']}€ ({int(279 - row['rank_income'])}º)", 
                ha='left', va='center', fontsize=10)


    # Customize plot
    ax.set_xlim(-0.3, 1.3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Number of\nCharging Points', 'Average Income\nper Household'], 
                        fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.set_visible(False)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    #plt.title('Charging Infrastructure Comparison by Municipality', 
    #          fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.show()

    return ax, df_plot, fig, idx, plt, row, top_n


@app.cell
def __(plot_df):
    # Get the concelhos that are in top n income but NOT in top n charging points
    _top_n = 30
    df_top_n_points = plot_df.nlargest(_top_n, 'rank_points')['Concelho']
    df_top_n_income = plot_df.nlargest(_top_n, 'rank_income')['Concelho']
    df_top_n_density = plot_df.nlargest(_top_n, 'rank_density')['Concelho']

    # Concelhos in top n income but NOT in top n charging points
    in_income_not_points = set(df_top_n_income) - set(df_top_n_points)
    print(f"In top {_top_n} income but NOT in top {_top_n} charging points:")
    print(in_income_not_points)

    # Concelhos in top n density but NOT in top n charging points
    in_density_not_points = set(df_top_n_density) - set(df_top_n_points)
    print(f"In top {_top_n} density but NOT in top {_top_n} charging points:")
    print(in_density_not_points)

    # 
    in_both = set(in_income_not_points) & set(in_density_not_points)
    print(f"In BOTH income AND density top {_top_n}, but NOT in charging points top {_top_n}:")
    print(in_both)
    return (
        df_top_n_density,
        df_top_n_income,
        df_top_n_points,
        in_both,
        in_density_not_points,
        in_income_not_points,
    )


if __name__ == "__main__":
    app.run()

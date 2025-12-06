import marimo

__generated_with = "0.7.20"
app = marimo.App(width="medium", layout_file="layouts/profiling.slides.json")


@app.cell
def __():
    import marimo as mo
    return mo,


@app.cell
def __(mo):
    mo.md(
        r"""
        EV Charging Points - Relation with Population Density and Income
        ================================================================

        - Do municipalities with more population density have more charging points?

        - Are charging points more common in higher income municipalities?

        - What municipalities should invest more in EV chargers?
        """
    )
    return


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
def __(mo, pd):
    # Download "https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y" and put it in a folder named 'data' in the repository root

    url_INE = "data/ERendimentoNLocal2023.xlsx"
    df_INE_raw = pd.read_excel(url_INE, sheet_name="Agregados_pub_2023", header=1)
    df_INE_raw


    mo.vstack([
        mo.md("# Income"),
        df_INE_raw
    ])
    return df_INE_raw, url_INE


@app.cell
def __(ProfileReport, df_INE):
    profile_INE = ProfileReport(df_INE, title="Profiling Report INE")
    profile_INE.to_file("reports/profile_INE.html")
    return profile_INE,


@app.cell
def __(df_INE_raw, mo):
    # Filter
    df_INE = df_INE_raw[df_INE_raw["Nível territorial"] == "Município"]

    # Rename Nível territorial to Concelho
    df_INE = df_INE.rename(columns={"Designação": "Concelho"})

    # Only keep desired columns
    df_INE = df_INE[["Concelho", "Rendimento bruto declarado médio por agregado fiscal"]]

    mo.vstack([
        mo.md("# Income (Processed)"),
        df_INE
    ])
    return df_INE,


@app.cell
def __(mo):
    import html

    with open("data/ine_densidade_populacional.csv", "r", encoding="latin-1") as f:
        output = f.read()
            
    mo.vstack([
        mo.md("# Density"),
        mo.Html(f"<pre>{output}</pre>")
    ])
    return f, html, output


@app.cell
def __(mo, pd):
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

    df_INE_densidade_display = df_INE_densidade.copy()     

    # Only keep desired columns
    df_INE_densidade = df_INE_densidade[["Concelho", "Densidade_Populacional_km2"]]

    mo.vstack([
        mo.md("# Density (Processed)"),
        df_INE_densidade_display
    ])
    return (
        col,
        column_mapping,
        df_INE_densidade,
        df_INE_densidade_display,
        url_INE_densidade,
    )


@app.cell
def __(mo, pd):
    url_EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/postos_carregamento_ves/exports/csv?lang=pt&timezone=Europe%2FLisbon&use_labels=true&delimiter=%3B"
    df_EREDES_raw = pd.read_csv(url_EREDES, sep=";")

    mo.vstack([
        mo.md("# Charging Points"),
        df_EREDES_raw
    ])
    return df_EREDES_raw, url_EREDES


@app.cell
def __(ProfileReport, df_EREDES_raw):
    profile_EREDES = ProfileReport(df_EREDES_raw, title="Profiling Report EREDES")
    profile_EREDES.to_file("reports/profile_EREDES.html")
    return profile_EREDES,


@app.cell
def __(df_EREDES_raw, mo):
    # Rename CodDistritoConcelho to Código territorial
    df_EREDES = df_EREDES_raw.rename(columns={"CodDistritoConcelho": "Código territorial"})

    # Only keep latest quarter
    df_EREDES[df_EREDES["Trimestre"]=="2025T3"]

    mo.vstack([
        mo.md("# Charging Points (Processed)"),
        df_EREDES
    ])
    return df_EREDES,


@app.cell
def __(df_EREDES, mo):
    # Fix typos in EREDES
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Castro daire", "Castro Daire")
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Miranda do douro", "Miranda do Douro")
    df_EREDES['Concelho'] = df_EREDES['Concelho'].replace("Freixo de Espada \u00c0 Cinta", "Freixo de Espada \u00e0 Cinta")

    df_EREDES_agg = df_EREDES.groupby('Concelho').agg(
        count_rows=('Concelho', 'size'),
        sum_pontos_de_ligacao=('Pontos de ligação para instalações de PCVE', 'sum')
    ).reset_index()

    mo.vstack([
        mo.md("# Charging Points (Aggregated)"),
        df_EREDES_agg
    ])
    return df_EREDES_agg,


@app.cell
def __(df_EREDES_agg, df_INE, df_INE_densidade, mo):
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

    mo.vstack([
        mo.md("# Joint Dataframe"),
        join_df
    ])
    return join_df,


@app.cell
def __(df_EREDES_agg, df_INE, df_INE_densidade, join_df, mo):
    # Identify lost concelhos
    # lost from df_INE
    lost_from_INE = df_INE[~df_INE['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()
    # lost from df_INE_densidade
    lost_from_densidade = df_INE_densidade[~df_INE_densidade['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()
    # lost from df_EREDES_agg
    lost_from_EREDES = df_EREDES_agg[~df_EREDES_agg['Concelho'].isin(join_df['Concelho'])]['Concelho'].tolist()

    mo.vstack([
        mo.md("# Lost Municipalities"),
        mo.md("Lost from Income (INE)"),
        lost_from_INE,
        mo.md("Lost from Population Density (INE)"),
        lost_from_densidade,
        mo.md("Lost from Charging Points (EREDES)"),
        lost_from_EREDES,
    ])
    return lost_from_EREDES, lost_from_INE, lost_from_densidade


@app.cell
def __(join_df, mo):
    plot_df = join_df.copy()
    plot_df['rank_stations'] = join_df['num_charging_stations'].rank(ascending=True, method='first')
    plot_df['rank_points'] = join_df['total_charging_points'].rank(ascending=True, method='first')
    plot_df['rank_density'] = join_df['Densidade_Populacional_km2'].rank(ascending=True, method='first')
    plot_df['rank_income'] = join_df['Rendimento bruto declarado médio por agregado fiscal'].rank(ascending=True, method='first')
    plot_df

    mo.vstack([
        mo.md("# Ranked"),
        plot_df
    ])
    return plot_df,


@app.cell
def __(mo, plot_df, plt):
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

    mo.vstack([
        mo.md("# Charging Infrastructure Comparison by Municipality"),
        _fig_density
    ])
    return


@app.cell
def __(mo, plot_df):
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

    mo.vstack([
        mo.md("# Charging Infrastructure Comparison by Municipality"),
        fig
    ])
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


@app.cell
def __(mo):
    mo.md(
        r"""
        Conclusions
        ===========
        The data provided by INE, a Portuguese official institution whose focus evolves around data and statistics, is not computer processing friendly as it favours a Excel-power user layout that does not compute easily; includes unnecessary metadata; and its serialized using a non-global encoding (“latin-1”). Also, their datasets are not consistent in how the same information is captured (e.g., municipalities). Still, the data is mostly of decent quality in the sense that it includes complete and valid records.
        The data used in this experiments has two major limitations:

        - Not all datasets are in the same timeframe (year)
        - One of the datasets (charging points) does not include all municipalities, hence the investigation was limited to those available

        In this experiment we used the total number of charging points, but that could be biased towards municipalities with larger areas. In a future experiment we could consider metrics that take into account geographical or demographical dimension, e.g., charging points per km2 or per household.
        The experiment seems to support the intuitive belief that more densely populated municipalities have more charging points. On the other hand, the relation between number of charging points and family income is not so direct, which might be unfortunate as these municipalities with higher income families are probably more likely to be renewing and upgrading their vehicle more regularly, and thus should be a priority to accelerate the transition to greener transportation. This relation is yet to be proven and could be subject of future work.

        With this work we listed a set of municipalities that could invest in new charging points using a heuristic that related the municipality position in both income and population density with the number of charging points. Under this heuristic Entrocamento is the only municipality present in both.
        """
    )
    return


@app.cell
def __(join_df, mo):
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    from scipy import stats

    # Create 4 separate plots with trendlines
    _fig1 = px.scatter(join_df, 
                       x='Rendimento bruto declarado médio por agregado fiscal',
                       y='num_charging_stations',
                       hover_name='Concelho',
                       trendline='ols',
                       color_discrete_sequence=['#3498db'])

    _fig2 = px.scatter(join_df,
                       x='Densidade_Populacional_km2',
                       y='num_charging_stations',
                       hover_name='Concelho',
                       trendline='ols',
                       color_discrete_sequence=['#e74c3c'])

    _fig3 = px.scatter(join_df,
                       x='Rendimento bruto declarado médio por agregado fiscal',
                       y='total_charging_points',
                       hover_name='Concelho',
                       trendline='ols',
                       color_discrete_sequence=['#2ecc71'])

    _fig4 = px.scatter(join_df,
                       x='Densidade_Populacional_km2',
                       y='total_charging_points',
                       hover_name='Concelho',
                       trendline='ols',
                       color_discrete_sequence=['#f39c12'])

    # Combine into subplots
    _fig_interactive = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Income vs Charging Stations', 
                        'Population Density vs Charging Stations',
                        'Income vs Total Charging Points', 
                        'Population Density vs Total Charging Points'),
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )

    # Add traces from fig1 with custom styling
    for trace in _fig1.data:
        if trace.mode == 'markers':
            trace.marker.size = 10
            trace.marker.opacity = 0.6
            trace.marker.line = dict(width=1.5, color='white')
            trace.hovertemplate = '<b>%{hovertext}</b><br>Income: €%{x:,.0f}<br>Stations: %{y}<extra></extra>'
        _fig_interactive.add_trace(trace, row=1, col=1)

    # Add traces from fig2 with custom styling
    for trace in _fig2.data:
        if trace.mode == 'markers':
            trace.marker.size = 10
            trace.marker.opacity = 0.6
            trace.marker.line = dict(width=1.5, color='white')
            trace.hovertemplate = '<b>%{hovertext}</b><br>Density: %{x:.1f} per km²<br>Stations: %{y}<extra></extra>'
        _fig_interactive.add_trace(trace, row=1, col=2)

    # Add traces from fig3 with custom styling
    for trace in _fig3.data:
        if trace.mode == 'markers':
            trace.marker.size = 10
            trace.marker.opacity = 0.6
            trace.marker.line = dict(width=1.5, color='white')
            trace.hovertemplate = '<b>%{hovertext}</b><br>Income: €%{x:,.0f}<br>Points: %{y}<extra></extra>'
        _fig_interactive.add_trace(trace, row=2, col=1)

    # Add traces from fig4 with custom styling
    for trace in _fig4.data:
        if trace.mode == 'markers':
            trace.marker.size = 10
            trace.marker.opacity = 0.6
            trace.marker.line = dict(width=1.5, color='white')
            trace.hovertemplate = '<b>%{hovertext}</b><br>Density: %{x:.1f} per km²<br>Points: %{y}<extra></extra>'
        _fig_interactive.add_trace(trace, row=2, col=2)

    # Update axes labels
    _fig_interactive.update_xaxes(title_text="Average Income per Household (€)", row=1, col=1, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_xaxes(title_text="Population Density (per km²)", row=1, col=2, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_xaxes(title_text="Average Income per Household (€)", row=2, col=1, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_xaxes(title_text="Population Density (per km²)", row=2, col=2, showgrid=True, gridcolor='lightgray')

    _fig_interactive.update_yaxes(title_text="Number of Charging Stations", row=1, col=1, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_yaxes(title_text="Number of Charging Stations", row=1, col=2, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_yaxes(title_text="Total Charging Points", row=2, col=1, showgrid=True, gridcolor='lightgray')
    _fig_interactive.update_yaxes(title_text="Total Charging Points", row=2, col=2, showgrid=True, gridcolor='lightgray')

    # Update layout
    _fig_interactive.update_layout(
        title_font_size=18,
        title_font_family='Arial Black',
        showlegend=False,
        height=900,
        width=1200,
        plot_bgcolor='white',
        hovermode='closest'
    )

    mo.vstack([
        mo.md("# Addressing Presentation Comments and Notes"),
        _fig_interactive,
    ])

    return go, make_subplots, np, px, stats, trace


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()

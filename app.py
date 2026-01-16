# Million-Dollar Flat Dashboard

# Load libraries 
import pandas as pd
import plotly.express as px
from shinywidgets import output_widget, render_widget
from shiny import App, ui
from shiny import render, reactive
from pathlib import Path
from htmltools import HTML

# Load data
this_dir = Path(__file__).parent
data_path = this_dir / "HDB_Resale_Transactions_Merged_20260113.csv.gz"
df = pd.read_csv(data_path, compression='gzip')
css_path = this_dir / "styles.css"

# Ensure a proper date column
df["date"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str).str.zfill(2) + "-01"
)

# Rename flat types to combine executive and multi-generation flats 
df["Flat_Type"] = df["Flat_Type"].replace(
            {"EXECUTIVE": "EXECUTIVE/MG", "MULTI-GENERATION": "EXECUTIVE/MG"}
        )
df["PSF"] = df["Resale_Price"] / (df["Floor_Area_Sqm"] * 10.764)

# Define unique list of HDB towns
hdbtowns = df["Town"].unique()

# Set the Last Updated tracker for the page
latest_date_dt = df["date"].max()
up_date = latest_date_dt.strftime("%b %Y")

# UI
app_ui = ui.page_navbar(  
    ui.nav_panel("LATEST TRENDS", 
        ui.input_selectize(
            "Period1", "Select Period:",
            ["Monthly", "Quarterly", "Yearly"],
            selected= "Quarterly",
        ), 
        # ---- Row 1 ----
        ui.layout_columns(
            ui.card(
                ui.card_header("Chart 1: Number of Million-Dollar Transactions by Flat Type"), 
                output_widget("Chart_1"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Chart 2: Million-Dollar Flats as Share of Resale Transactions (%)"), 
                output_widget("Chart_2"),
                full_screen=True
            ),
        ),

        # ---- Row 2 ----
        ui.layout_columns(
            ui.card(
                ui.card_header("Chart 3: Proportion of Resale Transactions by Price Category (%)"), 
                output_widget("Chart_3"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Chart 4: Resale PSF Trends of Million Dollar Flats"), 
                output_widget("Chart_4"),
                full_screen=True
            ),
        ),

        # ---- Row 3 ----
        ui.layout_columns(
            # --- Card for Chart 5 ---
            ui.card(
                ui.card_header("Chart 5: Median Price/PSF of Transactions (By Flat Type)"),
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_selectize(
                            "select_flat_type",
                            "Flat Type:",
                            {"3 ROOM": "3 ROOM", "4 ROOM": "4 ROOM", "5 ROOM": "5 ROOM", "EXECUTIVE/MG" : "EXECUTIVE/MG"},
                            selected=["4 ROOM", "5 ROOM", "EXECUTIVE/MG"],
                            multiple=True,
                        ),
                        ui.input_radio_buttons(  
                            "select_PSF", 
                            "Select:",  
                            {"PSF": "PSF", "PRICE": "PRICE"}, 
                            selected="PSF" 
                        ),  
                        bg="#f8f8f8",
                        width=225, 
                        open="closed"  
                    ),
                    output_widget("Chart_5"),
                ),
                full_screen=True
            ),

            # --- Card for Chart 6 ---
            ui.card(
                ui.card_header("Chart 6: Median Price/PSF of Transactions (Top 5 Towns)"),
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_selectize(
                            "select_town",
                            "HDB Towns:",
                            hdbtowns.tolist(),
                            multiple=True,
                            selected=None
                        ),
                        ui.input_radio_buttons(
                            "select_PSF_town", 
                            "Select:",  
                            {"PSF": "PSF", "PRICE": "PRICE"}, 
                            selected="PSF",  
                        ),  
                        bg="#f8f8f8",
                        width=225,
                        open="closed"
                    ),
                    output_widget("Chart_6"),
                ),
                full_screen=True
            ),
        ),
        # ---- Row 4 ----
        ui.layout_columns(
                ui.input_selectize(
                                "Flattype1", "Select Flat Type:",
                                ["All", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE/MG"],
                                selected= "All",
                            ),
        ), 

        ui.layout_columns(
                ui.navset_card_tab(
                    ui.nav_panel("Volume", ui.output_data_frame("table_volume")),   
                    ui.nav_panel("Share", ui.output_data_frame("table_share")),
                    ui.nav_panel("Max Price", ui.output_data_frame("table_max_price")),
                    ui.nav_panel("Max PSF", ui.output_data_frame("table_max_psf")),
                    ui.nav_panel("Median Price", ui.output_data_frame("table_median_price")),
                    ui.nav_panel("Median PSF", ui.output_data_frame("table_median_psf")),
                    id="tab",  
                    title= "Table 7: Transactions by HDB Town" + "\u00A0\u00A0",  
                ),
                col_widths=[12]
        ),
        ui.layout_columns(
                ui.navset_card_tab(
                    ui.nav_panel("Volume", ui.output_data_frame("project_volume")),   
                    ui.nav_panel("Share", ui.output_data_frame("project_share")),
                    ui.nav_panel("Max Price", ui.output_data_frame("project_max_price")),
                    ui.nav_panel("Max PSF", ui.output_data_frame("project_max_psf")),
                    ui.nav_panel("Median Price", ui.output_data_frame("project_median_price")),
                    ui.nav_panel("Median PSF", ui.output_data_frame("project_median_psf")),
                    ui.nav_panel("Median Lease Remaining", ui.output_data_frame("project_median_lease")),
                    id="tab2",  
                    title= "Table 8: Transactions by HDB Projects" + "\u00A0\u00A0",  
                ),
                col_widths=[12]
        ),
        ui.layout_columns(
                ui.navset_card_tab(
                    ui.nav_panel("Max Price (Top 3)", ui.output_data_frame("high_max_price")),
                    ui.nav_panel("Max PSF (Top 3)", ui.output_data_frame("high_max_psf")),
                    ui.nav_panel("Town-level (Top 3)", ui.output_data_frame("high_town_level")),
                    id="tab3",
                    title="Table 9: Historical High Transactions" + "\u00A0\u00A0",
                ),
                col_widths=[12]
            ),
        ui.hr(),  # Horizontal line
        ui.div(
            ui.p(ui.tags.b("Source: "), "HDB, data.gov.sg, ", "OneMap.gov.sg", style="font-size: 12.5px; margin-bottom: 1px;"),
            ui.p(ui.tags.b("Notes: "), style="font-size: 12.5px; margin-bottom: 1px;"),
            ui.tags.ul(
                ui.tags.li("Charts and tables use detailed HDB resale price and transaction data and are based on date of registration of resale transactions."),
                ui.tags.li("Addresses and geocharacteristics are obtained from OneMap API."),
                ui.tags.li("The transactions exclude resale transactions that may not reflect the full market price such as resale between relatives and resale of part shares."),
                ui.tags.li("Remaining lease is the number of years left before the lease ends, and the property is returned to HDB."),
                style="font-size: 12px; color: #555; line-height: 1.2;"
            ),
            style="padding: 1px; margin-top: 1px;"
        )
    ),  
    ui.nav_panel("GEOGRAPHICAL DISTRIBUTION", "Page B content"),  
    ui.nav_panel("ANALYSIS", "Page C content"),  
    ui.nav_panel("TRANSACTIONS", "Page C content"),
    ui.nav_spacer(),
    ui.nav_control(
        ui.div(
            f"Last updated: {up_date}",
            style="font-size: 13px; color: #666; padding-top: 12px; margin-right: 15px;", 
            class_="last-updated"
        )
    ),
    ui.nav_control(
        ui.tags.a(
            ui.tags.i(class_="fa-brands fa-github fa-lg"),
            href="https://github.com/benjamintee/HDB-Million-Dollar.git",
            target="_blank",
            title="View source on GitHub",
            class_="github-link"
        )
    ),
    header=ui.tags.head(
        ui.HTML('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">'),
    
        # Import font for the page and set it for the body of the page 
        ui.tags.style("""
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

            /* 1. Global Font and Background */
            html, body {
                font-family: 'Inter', sans-serif !important;
                background-color: #f8fafc; 
            }

            /* 2. Header / Navbar Customization */
            .navbar {
                background-color: #064e3b !important; /* Heritage Emerald */
                border-bottom: 3px solid #059669;    /* Subtle lighter green accent line */
            }

            /* 3. Specific Navbar Text and Links (Restricted to .navbar) */
            .navbar .navbar-brand {
                color: #ffffff !important;
                font-weight: 550;
            }

            .navbar .nav-link {
                color: rgba(255, 255, 255, 0.85) !important;
                font-weight: 500;
                transition: all 0.2s ease-in-out;
            }

            .navbar .nav-link:hover {
                color: #ffffff !important;
            }

            .navbar .nav-link.active {
                color: #ffffff !important;
                font-weight: 600;
            }

            /* 4. Navbar Metadata and Icons */
            .navbar-text, .navbar .last-updated {
                color: rgba(255, 255, 255, 0.85) !important;
                font-size: 0.85rem;
                font-weight: 400;
            }

            .navbar .github-link, .navbar .nav-link i.fa-github {
                color: rgba(255, 255, 255, 0.85) !important;
                transition: transform 0.2s ease;
            }

            .navbar .nav-link:hover i.fa-github {
                color: #ffffff !important;
                transform: scale(1.1);
            }

            /* 5. Ensure Table Content stays readable */
            /* Styling the table header */
            table thead th, 
            .shiny-data-frame thead th,
            .dataTables_wrapper table thead th {
                font-size: 13px !important;
                font-weight: 600 !important; /* Semi-bold for better readability */
                vertical-align: middle !important;
            }
            .shiny-data-frame {
                font-family: 'Inter', sans-serif !important;
                color: #2d3436;
            }
            /* 6. Color the text in the table tabs in grey */
            .card .nav-link {
                color: #94a3b8 !important; /* Soft grey */
                font-weight: 500;
                border-bottom: 2px solid transparent;
                transition: color 0.2s ease-in-out;
            }

            .card .nav-link:hover {
                color: #475569 !important; /* Medium charcoal on hover */
                background-color: transparent !important;
            }

            .card .nav-link.active {
                color: #070708 !important; 
                font-weight: 550;
                background-color: transparent !important;
            }

            div.main.bslib-gap-spacing.html-fill-container {
                padding-right: 5px !important;
                padding-left: 8px !important;
                padding-top: 5px !important;
                padding-bottom: 8px !important;
            }

            /* EDITING THE UI INPUT SELECTORS */
            /* 1. Reduce the size of the Label (e.g., "Flat Type:") */
            .control-label {
                font-size: 0.85rem !important;
                font-weight: 600;
                margin-bottom: 4px;
            }

            /* 2. Reduce the size of the selected items (the "pills") and the input text */
            .selectize-input, .selectize-input input {
                font-size: 0.85rem !important;
                min-height: 32px !important;
                line-height: 1.2 !important;
            }

            /* 3. Reduce the size of the options in the dropdown menu */
            .selectize-dropdown {
                font-size: 0.85rem !important;
                line-height: 1.2 !important;
            }

            /* 4. Specifically for 'multiple=True', shrink the item badges */
            .selectize-control.multi .selectize-input > div {
                font-size: 0.8rem !important;
                padding: 1px 5px !important;
                margin: 2px !important;
            }

            hr {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }
        """)
    ),
    title="MILLION DOLLAR HDB FLATS IN SINGAPORE",  
    id="page",  
)  

# Helper function to filter data
def filter_period(df, period, n=10):
    latest_date = df["date"].max()
    
    if period == "Monthly":
        start_date = latest_date - pd.DateOffset(months=n-1)
        df_filtered = df[df["date"] >= start_date].copy()
        df_filtered["Period"] = df_filtered["date"].dt.strftime("%b%y")  # e.g., Jan25
        df_filtered["Period_sort"] = df_filtered["date"]
    elif period == "Quarterly":
        start_date = latest_date - pd.DateOffset(months=3*(n-1))
        df_filtered = df[df["date"] >= start_date].copy()
        df_filtered["Period_sort"] = df_filtered["date"].dt.to_period("Q").dt.start_time
        df_filtered["Period"] = df_filtered["Period_sort"].dt.to_period("Q").apply(lambda x: f"{x.quarter}Q{x.year%100}")
    else:  # Yearly
        start_date = latest_date - pd.DateOffset(years=n-1)
        df_filtered = df[df["date"] >= start_date].copy()
        df_filtered["Period_sort"] = df_filtered["date"].dt.to_period("Y").dt.start_time
        df_filtered["Period"] = df_filtered["Period_sort"].dt.year.astype(str)
    
    return df_filtered

# Set custom styles for the charts on Page 1. 
def apply_custom_theme(fig):
    fig.update_layout(
        # Background & Font
        paper_bgcolor='rgba(0,0,0,0)', # Transparent to match card
        plot_bgcolor='white',          # White plot area
        font=dict(family="Inter, sans-serif", color="#2d3436"),
        
        # Legend Styling
        legend=dict(font=dict(size=13)),
        
        # Chart Title / Labels (If using fig.update_layout(title=...))
        title=dict(font=dict(size=12.5, family="Inter, sans-serif", weight="bold")),
        
        margin=dict(t=10, b=20, l=40, r=20)
    )

    # X-Axis Styling
    fig.update_xaxes(
        showgrid=False,               # Remove vertical grid lines
        linecolor='#475569',          # Dark grey x-axis line
        linewidth=1.5,
        title=dict(font=dict(size=13)), # Axis Label
        tickfont=dict(size=12),       # Tick Labels
        zeroline=False
    )

    # Y-Axis Styling
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#e2e8f0',          # Lighter grey major grid lines
        linecolor='#475569',          # Dark grey y-axis line
        linewidth=1.5,
        title=dict(font=dict(size=13), standoff=8), # Axis Label
        tickfont=dict(size=12),       # Tick Labels
        zeroline=False
    )
    
    return fig

# Server
def server(input, output, session):

    # ---- Chart 1: Number of Million-Dollar Flats by Flat Type ----
    @render_widget
    def Chart_1():

        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]

        df_md = filter_period(df[df["Resale_Price"] >= 1_000_000], period_choice, n=n_periods)

        # Recode flat types
        flat_order = ["EXECUTIVE/MG", "5 ROOM", "4 ROOM", "3 ROOM"]
        df_md["Flat_Type"] = pd.Categorical(df_md["Flat_Type"], categories=flat_order, ordered=True)

        # Summary grouped by period_sort and flat type
        summary = (
            df_md.groupby(["Period_sort", "Flat_Type"], observed=True)
            .size()
            .reset_index(name="Number")
            .sort_values("Period_sort")
        )

        # Totals per period
        totals = (
            df_md.groupby("Period_sort")
            .size()
            .reset_index(name="Total")
            .sort_values("Period_sort")
        )

        fig = px.bar(
            summary,
            x="Period_sort",
            y="Number",
            color="Flat_Type",
            barmode="stack",
            category_orders={"Flat_Type": flat_order},
        )

        # Add total labels above bars
        fig.add_scatter(
            x=totals["Period_sort"],
            y=totals["Total"],
            text=[f"{int(val):,}" for val in totals["Total"]],
            mode="text",
            textposition="top center",
            textfont=dict(size=14, weight = "bold"),
            showlegend=False
        )

        # Replace x-axis with formatted labels, keeping order
        period_labels = df_md[["Period_sort", "Period"]].drop_duplicates().sort_values("Period_sort")
        fig.update_layout(
            xaxis=dict(
                tickvals=period_labels["Period_sort"],
                ticktext=period_labels["Period"]
            ),
            xaxis_title=period_choice,
            yaxis_title="Number of Transactions",
            yaxis=dict(range=[0, totals["Total"].max() * 1.12], tickformat=","),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.00,
                xanchor="center",
                x=0.5,
                traceorder="reversed"
            ),
            legend_title_text=None
        )

        fig = apply_custom_theme(fig)

        return fig


    # ---- Chart 2: Million-Dollar Flats as Share of Resale Transactions ----
    @render_widget
    def Chart_2():

        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]

        df_filtered = filter_period(df, period_choice, n=n_periods)

        # Totals and million-dollar counts per period
        total_by_period = df_filtered.groupby(["Period_sort", "Period"]).size().reset_index(name="Total_Transactions")
        md_by_period = df_filtered[df_filtered["Resale_Price"] >= 1_000_000].groupby(["Period_sort", "Period"]).size().reset_index(name="MD_Transactions")

        share = total_by_period.merge(md_by_period, on=["Period_sort", "Period"], how="left").fillna(0)
        share["MD_Share_Percent"] = (share["MD_Transactions"] / share["Total_Transactions"] * 100).round(1)

        fig = px.line(
            share,
            x="Period_sort",
            y="MD_Share_Percent",
            markers=True
        )

        fig.update_traces(line=dict(width=3), marker=dict(size=10))

        # Add % labels above points
        fig.add_scatter(
            x=share["Period_sort"],
            y=share["MD_Share_Percent"] + 0.14,
            text=share["MD_Share_Percent"].astype(str) + "%",
            mode="text",
            textposition="top center",
            textfont=dict(size=14, weight = "bold"),
            showlegend=False
        )

        # Replace x-axis with nice labels
        fig.update_layout(
            xaxis=dict(
                tickvals=share["Period_sort"].unique(),
                ticktext=share["Period"].unique()
            ),
            xaxis_title=period_choice,
            yaxis_title="Share of Transactions (%)",
            yaxis_ticksuffix="%",
            yaxis=dict(range=[0, share["MD_Share_Percent"].max() * 1.15])
        )

        fig = apply_custom_theme(fig)
        return fig

    # ---- Chart 3: Distribution of resale prices ----
    @render_widget
    def Chart_3():

        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]

        df_filtered = filter_period(df, period_choice, n=n_periods)

        # ---- Define price bands ----
        bins = [0, 400_000, 600_000, 800_000, 1_000_000, 1_200_000, 1_400_000, 1_600_000, float("inf")]
        labels = ["Below 400k", "400k–600k", "600k–800k", "800k–1M", "1M–1.2M", "1.2M–1.4M", "1.4M–1.6M", ">1.6M"]

        df_filtered["Price_Band"] = pd.cut(
            df_filtered["Resale_Price"],
            bins=bins,
            labels=labels,
            right=False
        )

        df_filtered["Price_Band"] = pd.Categorical(
            df_filtered["Price_Band"],
            categories=labels,
            ordered=True
        )

        # ---- Aggregate counts ----
        counts = (
            df_filtered
            .groupby(["Period_sort", "Period", "Price_Band"], observed=True)
            .size()
            .reset_index(name="Count")
        )

        totals = (
            df_filtered
            .groupby(["Period_sort", "Period"], observed=True)
            .size()
            .reset_index(name="Total")
        )

        # ---- Convert to percentages and format labels ----
        share = counts.merge(totals, on=["Period_sort", "Period"])
        share["Percent"] = (share["Count"] / share["Total"] * 100)
        
        # 1. Create rounded labels for the first 4 bands only (>= 3%)
        label_bands = labels[:4]
        share["Display_Label"] = share.apply(
            lambda r: f"{int(round(r['Percent']))}%" 
            if r["Price_Band"] in label_bands and r["Percent"] >= 3 
            else "", 
            axis=1
        )

        share = share.sort_values("Period_sort")
        # Convert Period_sort to string to ensure correct x-axis mapping
        share["Period_sort"] = share["Period_sort"].astype(str)

        # ---- Stacked percentage bar ----
        fig = px.bar(
            share,
            x="Period_sort",
            y="Percent",
            color="Price_Band",
            text="Display_Label",  # Use the rounded labels
            barmode="stack",
            category_orders={"Price_Band": labels}
        )

        # Style the text inside the bars
        fig.update_traces(
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=13, color="white", weight = "bold")
        )

        # ---- Axis and Legend formatting ----
        period_labels = (
            df_filtered[["Period_sort", "Period"]]
            .drop_duplicates()
            .sort_values("Period_sort")
        )

        fig.update_layout(
            xaxis=dict(
                type='category',
                tickvals=period_labels["Period_sort"].astype(str),
                ticktext=period_labels["Period"]
            ),
            xaxis_title=period_choice,
            yaxis_title="Percentage of Resale Transactions",
            yaxis_ticksuffix="%",
            yaxis=dict(range=[0, 100]),
            legend_title_text=None,
            legend=dict(
                traceorder="reversed",  # 2. Reverse the legend display order
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=1.02
            ),
            margin=dict(r=120)
        )

        fig = apply_custom_theme(fig)
        return fig

    # ---- Chart 4: Resale PSF Trends ----
    @render_widget
    def Chart_4():

        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]

        df_filtered = filter_period(df, period_choice, n=n_periods).copy()

        # Compute PSF
        df_filtered["PSF"] = (
            df_filtered["Resale_Price"]
            / df_filtered["Floor_Area_Sqm"]
            / 10.764
        )

        # Million-dollar subset
        df_md = df_filtered[df_filtered["Resale_Price"] >= 1_000_000]

        # Aggregate
        psf = (
            df_filtered
            .groupby("Period_sort", observed=False)
            .agg(
                Median_PSF_All=("PSF", "median")
            )
            .reset_index()
            .merge(
                df_md
                .groupby("Period_sort", observed=False)
                .agg(
                    Max_PSF=("PSF", "max"),
                    Median_PSF=("PSF", "median")
                )
                .reset_index(),
                on="Period_sort",
                how="left"
            )
        )

        # Add readable period labels
        period_labels = (
            df_filtered[["Period_sort", "Period"]]
            .drop_duplicates()
            .sort_values("Period_sort")
        )
        psf = psf.merge(period_labels, on="Period_sort", how="left")

        psf["Period_sort"] = psf["Period_sort"].astype(str)

        # ---- Plot ----
        fig = px.line(
            psf,
            x="Period_sort",
            y=["Max_PSF", "Median_PSF", "Median_PSF_All"],
            markers=True,
            labels={"value": "PSF", "variable": ""},
        )

        fig.update_traces(line=dict(width=3), marker=dict(size=8))

        # Rename legend entries
        fig.for_each_trace(lambda t: t.update(
            name={
                "Max_PSF": "MAX PSF",
                "Median_PSF": "MEDIAN PSF",
                "Median_PSF_All": "MEDIAN PSF (ALL RESALE)"
            }[t.name]
        ))

        # ---- Add annotations (correct way) ----
        series_map = {
            "MAX PSF": "Max_PSF",
            "MEDIAN PSF": "Median_PSF",
            "MEDIAN PSF (ALL RESALE)": "Median_PSF_All"
        }

        for trace in fig.data:
            col = series_map[trace.name]
            for _, r in psf.iterrows():
                y = r[col]
                if pd.isna(y): continue

                label = f"{int(round(y)):,}"

                fig.add_annotation(
                    # 2. Ensure x matches the string in the dataframe exactly
                    x=str(r["Period_sort"]), 
                    y=y,
                    text=label,
                    showarrow=False,
                    # 3. Explicitly link to data coordinates
                    xref="x",
                    yref="y",
                    font=dict(color="white", size=13, weight = "bold"), 
                    bgcolor=trace.line.color,
                    bordercolor=trace.line.color,
                    borderpad=3,
                    xanchor="center",
                    yanchor="middle"
                )

        # ---- Layout ----
        fig.update_layout(
            xaxis=dict(
                type='category',
                tickvals=psf["Period_sort"],
                ticktext=psf["Period"]
            ),
            xaxis_title=period_choice,
            yaxis=dict(
                tickformat="," 
            ),
            yaxis_title="Price per Square Foot, PSF ($)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            legend_title_text=None
        )

        fig = apply_custom_theme(fig)
        return fig

    # ---- Chart 5: Median PSF/Price by Flat Type ----
    @render_widget
    def Chart_5():
        # 1. Period Filtering
        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        df_filtered = filter_period(df, period_choice, n=n_periods).copy()

        # 2. Price Filtering
        df_md = df_filtered[df_filtered["Resale_Price"] >= 1_000_000].copy()
        if df_md.empty:
            return px.scatter(title="No million-dollar transactions in this period.")

        # 3. Aggregation
        df_md["PSF"] = df_md["Resale_Price"] / df_md["Floor_Area_Sqm"] / 10.764
        agg_df = (
            df_md.groupby(["Period_sort", "Period", "Flat_Type"], observed=False)
            .agg(Median_PSF=("PSF", "median"), Median_Price=("Resale_Price", "median"))
            .reset_index()
        )

        # Identify the absolute latest period in the aggregate data
        latest_period_val = agg_df["Period_sort"].max()

        # 4. Filter by User Input
        selected_types = input.select_flat_type()
        metric_choice = input.select_PSF()
        agg_df = agg_df[agg_df["Flat_Type"].isin(selected_types)].copy()
        
        if agg_df.empty:
            return px.scatter(title="Please select flat types with million-dollar transactions.")

        agg_df = agg_df.sort_values("Period_sort")
        agg_df["Period_sort_str"] = agg_df["Period_sort"].astype(str)
        
        y_col = "Median_PSF" if metric_choice == "PSF" else "Median_Price"
        y_label = "Median PSF ($)" if metric_choice == "PSF" else "Median Price ($)"

        # 5. Plotting
        fig = px.line(
            agg_df,
            x="Period_sort_str",
            y=y_col,
            color="Flat_Type",
            markers=True,
            labels={y_col: y_label, "Period_sort_str": period_choice},
            category_orders={"Flat_Type": ["3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE/MG"]}
        )

        fig.update_traces(line=dict(width=3), marker=dict(size=10))

        # 6. Label Logic & Deconfliction (Right-aligned, Last period only)
        last_points = []
        for trace in fig.data:
            trace_data = agg_df[agg_df["Flat_Type"] == trace.name]
            if not trace_data.empty:
                last_row = trace_data.iloc[-1]
                
                # Only label if the data point exists in the latest period
                if last_row["Period_sort"] == latest_period_val:
                    last_points.append({
                        "name": trace.name,
                        "x": last_row["Period_sort_str"],
                        "y": last_row[y_col],
                        "color": trace.line.color
                    })

        # Sort points by Y to nudge overlapping labels
        last_points.sort(key=lambda x: x["y"])
        y_range = agg_df[y_col].max() - agg_df[y_col].min()
        min_dist = y_range * 0.08  # 8% threshold for deconfliction

        for i in range(len(last_points)):
            if i > 0:
                diff = last_points[i]["y"] - last_points[i-1]["y"]
                if diff < min_dist:
                    last_points[i]["y"] = last_points[i-1]["y"] + min_dist

        # Add the labels
        for pt in last_points:
            label_text = f"${pt['y']/1e6:.2f}M" if metric_choice == "PRICE" else f"{int(round(pt['y'])):,}"
            
            fig.add_annotation(
                x=pt["x"],
                y=pt["y"],
                text=label_text,
                showarrow=False,
                xanchor="left",
                xshift=12,
                font=dict(color=pt["color"], size=13),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=pt["color"],
                borderwidth=1.2,
                borderpad=4,
                align="left"
            )

        # 7. Final Layout
        fig.update_layout(
            xaxis=dict(
                type='category', 
                tickvals=agg_df["Period_sort_str"].unique(), 
                ticktext=agg_df["Period"].unique()
            ),
            yaxis=dict(showgrid=True, gridcolor='lightgrey', tickformat="," ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            legend_title_text=None, 
            margin=dict(t=10), 
            hovermode="x unified"
        )

        fig = apply_custom_theme(fig)
        return fig       

    # ---- Chart 6: Additional Logic to update UI based on reactive function --- 
    @reactive.Effect
    @reactive.event(input.Period1, input.select_PSF_town)
    def _update_town_selection():
        # 1. Get the current filtered data
        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        df_filtered = filter_period(df, period_choice, n=n_periods).copy()
        
        # Filter for Million-Dollar transactions
        df_md = df_filtered[df_filtered["Resale_Price"] >= 1_000_000].copy()
        
        if not df_md.empty:
            # 2. Calculate Metric
            df_md["PSF"] = df_md["Resale_Price"] / df_md["Floor_Area_Sqm"] / 10.764
            metric_choice = input.select_PSF_town()
            y_col = "PSF" if metric_choice == "PSF" else "Resale_Price"
            
            # 3. Identify the Latest Period to find the "Top 5"
            # We use the raw sort value to find the most recent time slot
            latest_period_val = df_md["Period_sort"].max()
            latest_towns_df = df_md[df_md["Period_sort"] == latest_period_val]
            
            # 4. Group by Town and find the Top 5
            top_5_towns = (
                latest_towns_df.groupby("Town")[y_col]
                .median()
                .sort_values(ascending=False)
                .head(5)
                .index.tolist()
            )
            
            # 5. Push these selections to the UI
            ui.update_selectize("select_town", selected=top_5_towns)

    # ---- Chart 6: Top 5 Towns by Metric ----
    @render_widget
    def Chart_6():
        # 1. Initial Filtering
        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        df_filtered = filter_period(df, period_choice, n=n_periods).copy()
        df_md = df_filtered[df_filtered["Resale_Price"] >= 1_000_000].copy()

        if df_md.empty:
            return px.scatter(title="No million-dollar transactions found.")

        # 2. Metric Calculation
        df_md["PSF"] = df_md["Resale_Price"] / df_md["Floor_Area_Sqm"] / 10.764
        metric_choice = input.select_PSF_town()
        y_col = "Median_PSF" if metric_choice == "PSF" else "Median_Price"
        y_label = "Median PSF ($)" if metric_choice == "PSF" else "Median Price ($)"
        
        agg_df = (
            df_md.groupby(["Period_sort", "Period", "Town"], observed=False)
            .agg(Median_PSF=("PSF", "median"), Median_Price=("Resale_Price", "median"))
            .reset_index()
        )
        latest_period_val = agg_df["Period_sort"].max()

        # 3. Dynamic "Top 5" Logic + Freshness Filter
        selected_towns = input.select_town()
        
        if not selected_towns:
            return px.scatter(title="Please select at least one town in the sidebar.")

        # Filter the data based on the selection
        plot_df = agg_df[agg_df["Town"].isin(selected_towns)].copy()
        plot_df = plot_df.sort_values("Period_sort")
        plot_df["Period_sort_str"] = plot_df["Period_sort"].astype(str)

        # 4. Plotting
        fig = px.line(
            plot_df,
            x="Period_sort_str",
            y=y_col,
            color="Town",
            markers=True,
            labels={y_col: y_label, "Period_sort_str": period_choice}
        )

        fig.update_traces(line=dict(width=3), marker=dict(size=10))

        # 5. Label Deconfliction (Updated to filter out "stale" lines)
        last_points = []
        for trace in fig.data:
            trace_data = plot_df[plot_df["Town"] == trace.name]
            if not trace_data.empty:
                last_row = trace_data.iloc[-1]
                
                # ONLY add a label if this town's last data point is the latest period
                # This prevents labels from appearing for lines that end early
                if last_row["Period_sort"] == latest_period_val:
                    last_points.append({
                        "town": trace.name,
                        "x": last_row["Period_sort_str"],
                        "y": last_row[y_col],
                        "color": trace.line.color
                    })

        # Sort points by Y value to identify overlaps
        last_points.sort(key=lambda x: x["y"])
        
        # Simple Deconfliction: If labels are within 3% of the Y-range, nudge them
        y_range = plot_df[y_col].max() - plot_df[y_col].min()
        min_dist = y_range * 0.08 # 10% threshold
        
        for i in range(len(last_points)):
            if i > 0:
                diff = last_points[i]["y"] - last_points[i-1]["y"]
                if diff < min_dist:
                    # Nudge the current label up
                    last_points[i]["y"] = last_points[i-1]["y"] + min_dist 

        # 6. Add the Deconflicted Labels (Value Only) to the Right
        for pt in last_points:
            # Format label: $1.25M for PRICE, or 1,250 for PSF
            if metric_choice == "PRICE":
                # Using the original y from the dataframe row might be better for accuracy 
                # if the nudging distance is very large, but pt['y'] works for visual alignment
                label_text = f"${pt['y']/1e6:.2f}M"
            else:
                label_text = f"{int(round(pt['y'])):,}"
            
            fig.add_annotation(
                x=pt["x"],
                y=pt["y"],
                text=label_text, 
                showarrow=False,
                xanchor="left",    
                xshift=12,         # Gap between the marker and the text
                font=dict(color=pt["color"], size=13),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=pt["color"],
                borderwidth=1,
                borderpad=2,
                align="left"
            )

        fig.update_layout(
            xaxis=dict(
                type='category', 
                tickvals=plot_df["Period_sort_str"].unique(), 
                ticktext=plot_df["Period"].unique()
            ),
            yaxis=dict(tickformat=","), 
            legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5),
            legend_title_text=None, 
            margin=dict(t=5),
            hovermode="x unified"
        )

        fig = apply_custom_theme(fig)
        return fig

    # ---- Chart 7: Filtering Data to Show Trends by Town ----
    @reactive.Calc
    def table_data_base():
        # 1. Initial Filtering for Million Dollar Flats
        df_md = df[df["Resale_Price"] >= 1_000_000].copy()
        
        # 2. Apply Flat Type Filter
        ft_choice = input.Flattype1()
        if ft_choice != "All":
            df_md = df_md[df_md["Flat_Type"] == ft_choice]
        
        # 3. Use your existing helper to create Period/Period_sort
        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        df_filtered = filter_period(df_md, period_choice, n=n_periods)
        
        return df_filtered, period_choice

    @reactive.Calc
    def prepared_table_df():
        df_filtered, period_choice = table_data_base()
        
        if df_filtered.empty:
            return pd.DataFrame(), [], pd.DataFrame(), input.Flattype1()
        
        # Identify unique periods to show as columns 
        recent_periods = sorted(df_filtered["Period_sort"].unique())
        
        # Calculate Last 12 Months separately
        # We filter the million-dollar records from the last 365 days
        latest_date = df["date"].max()
        twelve_months_ago = latest_date - pd.DateOffset(months=12)
        
        # Filter base df_md for the 12-month stat
        df_md_all = df[df["Resale_Price"] >= 1_000_000].copy()
        ft_choice = input.Flattype1()
        if ft_choice != "All":
            df_md_all = df_md_all[df_md_all["Flat_Type"] == ft_choice]
            
        last_12m_df = df_md_all[df_md_all["date"] > twelve_months_ago]
        
        return df_filtered, recent_periods, last_12m_df, ft_choice

    def apply_heatmap_style(df, target_cols_indices):
        if df.empty or not target_cols_indices:
            return []

        # 1. Extract and convert to numeric for math
        # We use the full df here to keep indices aligned
        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        data_subset = numeric_df.iloc[:, target_cols_indices]
        
        v_max = data_subset.max().max()
        v_min = data_subset[data_subset > 0].min().min()
        if pd.isna(v_min): v_min = 0
        v_range = v_max - v_min if v_max > v_min else 1

        styles = []
        
        # 2. Iterate using the indices relative to the FULL dataframe
        for col_idx in target_cols_indices:
            for row_idx in range(len(df)):
                # Pull from numeric_df using the actual column index from the original table
                val = numeric_df.iloc[row_idx, col_idx]
                
                # Handle Zero or NaN
                if pd.isna(val) or val == 0:
                    styles.append({
                        "rows": [row_idx],
                        "cols": [col_idx],
                        "style": {
                            "background-color": "#f1f5f9",
                        }
                    })
                    continue

                # 3. Apply Power Scale
                norm = (val - v_min) / v_range
                norm_adj = norm ** 2 
                alpha = 0.05 + (norm_adj * 0.45)
                
                styles.append({
                    "rows": [row_idx],
                    "cols": [col_idx],
                    "style": {
                        "background-color": f"rgba(6, 78, 59, {alpha:.2f})",
                        "color": "#070708",
                        "font-weight": "600" if norm > 0.75 else "normal"
                    }
                })
        return styles

    # ---- Chart 7: Filtering Data to Show Trends by Town ----
    # 7A: Volume Trends
    @render.data_frame
    def table_volume():
        df_filtered, recent_periods, last_12m_df, ft_choice = prepared_table_df()
        
        if df_filtered.empty:
            return pd.DataFrame({"Result": ["No data for selection"]})

        # 1. Pivot and Sort
        pivot = df_filtered.pivot_table(
            index="Town", columns="Period", values="Resale_Price", aggfunc="count"
        ).fillna(0)
        trend_cols = df_filtered.sort_values("Period_sort")["Period"].unique()
        pivot = pivot[trend_cols]

        # 2. Summary Columns
        l12m = last_12m_df.groupby("Town").size().rename("Last 12 Months")
        df_md_total = df[df["Resale_Price"] >= 1_000_000].copy()
        if ft_choice != "All":
            df_md_total = df_md_total[df_md_total["Flat_Type"] == ft_choice]
        cumulative = df_md_total.groupby("Town").size().rename("Historical All")
        
        # 3. Combine and Reset Index
        result = pivot.join(l12m, how="left").join(cumulative, how="left").fillna(0).astype(int)
        result = result.reset_index() # "Town" is now index 0
        result.insert(1, "Flat Type", ft_choice) # "Flat Type" is index 1
        
        result = result.sort_values(by="Last 12 Months", ascending=False)

        # 4. Define Column Indices for Styling
        n_cols = len(result.columns)
        # Period cells start at index 2 and end before the last two summary columns
        period_col_indices = list(range(2, n_cols - 2))
        l12m_idx = n_cols - 2
        hist_idx = n_cols - 1

        # 5. Dynamic Coloring Logic (Heatmap)
        heatmap_styles = apply_heatmap_style(result, period_col_indices)

        # 6. Final Render
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}},
                # Static highlighting for summary columns
                {"cols": [l12m_idx, hist_idx], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
                # Inject dynamic heatmap styles
                *heatmap_styles 
            ],
            height="auto"
        )
    # Chart 7B: Share of transactions by Town 
    @render.data_frame
    def table_share():
        # 1. Get filtered Million-Dollar data and L12M slice from reactive calc
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        if df_md_filtered.empty:
            return render.DataTable(pd.DataFrame({"Message": ["No data available"]}))

        # 2. Get Total Market data (All HDB flats) for the same periods
        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        
        # Filter the global 'df' (entire market) to match chosen timeframe
        df_all_market = filter_period(df, period_choice, n=n_periods)

        # 3. Create Pivot for Numerator (MD Counts)
        md_pivot = df_md_filtered.pivot_table(
            index="Town", columns="Period", values="Resale_Price", aggfunc="count"
        ).fillna(0)

        # 4. Create Pivot for Denominator (Total Market Counts)
        total_pivot = df_all_market.pivot_table(
            index="Town", columns="Period", values="Resale_Price", aggfunc="count"
        ).fillna(0)

        # 5. Calculate Share Percentage
        # Use .reindex_like to ensure denominators align with numerators
        share_result = (md_pivot / total_pivot.reindex_like(md_pivot) * 100).fillna(0)

        # 6. Reorder columns chronologically
        # Use df_all_market for the sort to ensure all time slots are captured
        chronological_cols = df_all_market.sort_values("Period_sort")["Period"].unique()
        # Filter to only include columns that actually exist in the share_result
        existing_cols = [c for c in chronological_cols if c in share_result.columns]
        share_result = share_result[existing_cols]

        # 7. Calculate Last 12 Months Share (%)
        latest_date = df["date"].max()
        l12m_start = latest_date - pd.DateOffset(months=12)
        
        # Total Market (All Sales) in last 12 months
        all_12m = df[df["date"] > l12m_start].groupby("Town").size()
        # Million Dollar Market in last 12 months
        md_12m = last_12m_md.groupby("Town").size()
        
        l12m_share = (md_12m / all_12m * 100).fillna(0).rename("Last 12 Months (%)")

        # 8. Final Join and Row Sorting
        result = share_result.join(l12m_share, how="left").fillna(0).reset_index()
        result.insert(1, "Flat Type", ft_choice)
        result = result.sort_values(by="Last 12 Months (%)", ascending=False)

        # 9. Formatting: Convert to string with 1 decimal place and % sign
        cols_to_format = [c for c in result.columns if c not in ["Town", "Flat Type"]]
        for col in cols_to_format:
            result[col] = result[col].map("{:.1f}%".format)

        # 10. Render with Compact Styling
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1","white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
                {"cols": [len(result.columns)-1, len(result.columns)-2], "style": {"background-color": "#f8fafc", "font-weight": "600"}}
            ],
            height="auto",
            width="100%"
        )
    # Table 7C: Max Price for each town 
    @render.data_frame
    def table_max_price():
        # 1. Get filtered Million-Dollar data from reactive calc
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        if df_md_filtered.empty:
            return render.DataTable(pd.DataFrame({"Message": ["No data available"]}))

        # 2. Pivot for the selected periods (Max Price per Town/Period)
        max_pivot = df_md_filtered.pivot_table(
            index="Town", 
            columns="Period", 
            values="Resale_Price", 
            aggfunc="max"
        ).fillna(0)

        # 3. Reorder columns chronologically using your preferred syntax
        max_pivot = max_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]

        # 4. Calculate Historical Max (All-time MD record for each town)
        selected_flat_type = input.Flattype1()
        
        # Start with all Million-Dollar sales
        df_hist = df[df["Resale_Price"] >= 1_000_000].copy()
        
        # Apply the same Flat Type filter used in the rest of the app
        if selected_flat_type != "All":
            df_hist = df_hist[df_hist["Flat_Type"] == selected_flat_type]
            
        historical_max = df_hist.groupby("Town")["Resale_Price"].max().rename("ATH Max")
        
        # 5. Calculate Last 12 Months Max
        l12m_max = last_12m_md.groupby("Town")["Resale_Price"].max().rename("L12M Max")

        # 6. Final Join and Sort
        result = max_pivot.join([l12m_max, historical_max], how="left").fillna(0).reset_index()
        result.insert(1, "Flat Type", ft_choice)
        result = result.sort_values(by= "L12M Max", ascending=False)

        # 7. Generate styles using the updated helper
        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 2)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        # 8. Formatting: Convert to "$X.XXM" strings
        cols_to_format = [c for c in result.columns if c not in ["Town", "Flat Type"]]
        for col in cols_to_format:
            result[col] = result[col].apply(
                lambda x: f"${x/1_000_000:.2f}M" if x > 0 else "-"
            )

        # 9. Render with same compact styling
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
                {"cols": [len(result.columns)-1, len(result.columns)-2], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
                *heatmap_styles
            ],
            height="auto",
            width="100%"
        )
    # Chart 7D: Max PSF for each town
    @render.data_frame
    def table_max_psf():
        # 1. Get filtered Million-Dollar data from reactive calc
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        if df_md_filtered.empty:
            return render.DataTable(pd.DataFrame({"Message": ["No data available"]}))

        # 2. Pivot for the selected periods (Max PSF per Town/Period)
        psf_pivot = df_md_filtered.pivot_table(
            index="Town", 
            columns="Period", 
            values="PSF", 
            aggfunc="max"
        ).fillna(0)

        # 3. Reorder columns chronologically
        psf_pivot = psf_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]

        # 4. Calculate All-Time High (ATH) PSF BASED ON FLAT TYPE
        selected_flat_type = input.Flattype1()
        
        # Start with global data where price >= 1M
        df_hist = df[df["Resale_Price"] >= 1_000_000].copy()
        
        # Calculate PSF for the historical dataset
        df_hist["PSF"] = df_hist["Resale_Price"] / (df_hist["Floor_Area_Sqm"] * 10.764)
        
        if selected_flat_type != "All":
            df_hist = df_hist[df_hist["Flat_Type"] == selected_flat_type]
            
        historical_psf = df_hist.groupby("Town")["PSF"].max().rename("ATH Max PSF")
        
        # 5. Calculate Last 12 Months Max PSF
        l12m_psf = last_12m_md.groupby("Town")["PSF"].max().rename("L12M Max PSF")

        # 6. Final Join and Sort
        result = psf_pivot.join([l12m_psf, historical_psf], how="left").fillna(0).reset_index()
        result.insert(1, "Flat Type", ft_choice)
        result = result.sort_values(by="L12M Max PSF", ascending=False)

        # 7. Generate styles using the updated helper
        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 2)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        # 8. Formatting: Convert to "$X,XXX" strings
        cols_to_format = [c for c in result.columns if c not in ["Town", "Flat Type"]]
        for col in cols_to_format:
            result[col] = result[col].apply(
                lambda x: f"${x:,.0f}" if x > 0 else "-"
            )

        # 9. Render with compact styling
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
                {"cols": [len(result.columns)-1, len(result.columns)-2], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
                *heatmap_styles
            ],
            height="auto",
            width="100%"
        )
    # Table 7D/7E: Median Price and Median PSF 
    def render_median_table(column_name, is_price=True):
        # 1. Get filtered Million-Dollar data
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        if df_md_filtered.empty:
            return render.DataTable(pd.DataFrame({"Message": ["No data available"]}))

        # 2. Pivot for Million-Dollar Medians
        md_pivot = df_md_filtered.pivot_table(
            index="Town", columns="Period", values=column_name, aggfunc="median"
        ).fillna(0)
        
        # Ensure correct chronological order
        correct_order = df_md_filtered.sort_values("Period_sort")["Period"].unique()
        md_pivot = md_pivot[correct_order]

        # 3. Calculate "All Resale" Benchmark (Global Data)
        selected_flat_type = input.Flattype1()
        
        # Filter global df for the last 12 months
        latest_date = df["date"].max()
        l12m_start = latest_date - pd.DateOffset(months=12)
        df_all_12m = df[df["date"] > l12m_start].copy()
        
        # Apply Flat Type filter to benchmark
        if selected_flat_type != "All":
            df_all_12m = df_all_12m[df_all_12m["Flat_Type"] == selected_flat_type]

        # Calculate Medians
        l12m_md_median = last_12m_md.groupby("Town")[column_name].median().rename("L12M MD Median")
        all_resale_median = df_all_12m.groupby("Town")[column_name].median().rename("L12M Resale All")

        # 4. Join and Sort
        # The order will be: Town, [Months...], L12M MD Median, All Resale
        result = md_pivot.join([l12m_md_median, all_resale_median], how="left").fillna(0).reset_index()
        result.insert(1, "Flat Type", ft_choice)
        result = result.sort_values(by="L12M MD Median", ascending=False)

        # 5. Generate styles using the updated helper
        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 2)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        # 6. Formatting Logic
        cols_to_format = [c for c in result.columns if c not in ["Town", "Flat Type"]]
        for col in cols_to_format:
            if is_price:
                result[col] = result[col].apply(lambda x: f"${x/1e6:.2f}M" if x > 0 else "-")
            else:
                result[col] = result[col].apply(lambda x: f"${x:,.0f}" if x > 0 else "-")

        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}},
                {"cols": [len(result.columns)-1, len(result.columns)-2], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
                *heatmap_styles
            ],
            height="auto",
            width="100%"
        )

    @render.data_frame
    def table_median_price():
        return render_median_table("Resale_Price", is_price=True)

    @render.data_frame
    def table_median_psf():
        return render_median_table("PSF", is_price=False)

    # ---- Table 8A: Project Volume ----
    @render.data_frame
    def project_volume():
        df_filtered, recent_periods, last_12m_df, ft_choice = prepared_table_df()
        df_filtered = df_filtered[df_filtered["BUILDING"] != "NIL"]
        if df_filtered.empty:
            return pd.DataFrame({"Result": ["No data"]})

        # Pivot by Project (BUILDING)
        pivot = df_filtered.pivot_table(
            index="BUILDING", columns="Period", values="Resale_Price", aggfunc="count"
        ).fillna(0)

        # Sort columns chronologically
        pivot = pivot[df_filtered.sort_values("Period_sort")["Period"].unique()]
        
        # Metadata: Get the Town for each Project (first occurrence)
        project_towns = df_filtered.groupby("BUILDING")["Town"].first()
        
        # Stats: L12M and Historical All
        l12m = last_12m_df.groupby("BUILDING").size().rename("Last 12 Months")
        
        # "Historical All" based on selected Flat Type
        df_md_all = df[df["Resale_Price"] >= 1_000_000]
        if ft_choice != "All":
            df_md_all = df_md_all[df_md_all["Flat_Type"] == ft_choice]
        hist_all = df_md_all.groupby("BUILDING").size().rename("Historical All")
        
        # Combine
        result = pivot.join([project_towns, l12m, hist_all], how="left").fillna(0)
        
        # Reset and Organize Columns
        result = result.reset_index().rename(columns={"BUILDING": "Project Name"})
        result.insert(1, "Town", result.pop("Town")) # Move Town to index 1
        
        # Sort and Format
        result = result.sort_values(by="Last 12 Months", ascending=False)

        # Generate styles using the updated helper
        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 2)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)
        
        # Ensure counts are integers
        count_cols = [c for c in result.columns if c not in ["Project Name", "Town"]]
        result[count_cols] = result[count_cols].astype(int)

        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}},
            {"cols": [len(result.columns)-1, len(result.columns)-2], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
            *heatmap_styles 
            ])

    # ---- Table 8B: Project Share ----
    @render.data_frame
    def project_share():
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        df_md_filtered = df_md_filtered[df_md_filtered["BUILDING"] != "NIL"]
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data"]})

        period_choice = input.Period1()
        n_periods = {"Monthly": 10, "Quarterly": 8, "Yearly": 8}[period_choice]
        df_all_market = filter_period(df, period_choice, n=n_periods)

        md_pivot = df_md_filtered.pivot_table(index="BUILDING", columns="Period", values="Resale_Price", aggfunc="count").fillna(0)
        total_pivot = df_all_market.pivot_table(index="BUILDING", columns="Period", values="Resale_Price", aggfunc="count").fillna(0)

        share_result = (md_pivot / total_pivot.reindex_like(md_pivot) * 100).fillna(0)
        chrono_cols = [c for c in df_all_market.sort_values("Period_sort")["Period"].unique() if c in share_result.columns]
        share_result = share_result[chrono_cols]

        # Metadata
        project_towns = df_md_filtered.groupby("BUILDING")["Town"].first()
        
        # L12M Share
        l12m_start = df["date"].max() - pd.DateOffset(months=12)
        all_12m = df[df["date"] > l12m_start].groupby("BUILDING").size()
        md_12m = last_12m_md.groupby("BUILDING").size()
        l12m_share = (md_12m / all_12m * 100).fillna(0).rename("Last 12 Months (%)")

        result = share_result.join([project_towns, l12m_share], how="left").fillna(0).reset_index().rename(columns={"BUILDING": "Project Name"})
        result.insert(1, "Town", result.pop("Town"))
        result = result.sort_values(by="Last 12 Months (%)", ascending=False)

        cols_to_format = [c for c in result.columns if c not in ["Project Name", "Town"]]
        for col in cols_to_format:
            result[col] = result[col].map("{:.1f}%".format)

        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
            {"cols": [len(result.columns)-1], "style": {"background-color": "#f8fafc", "font-weight": "600"}}
        ])

    # ---- Table 8C: Project Max Price ----
    @render.data_frame
    def project_max_price():
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        df_md_filtered = df_md_filtered[df_md_filtered["BUILDING"] != "NIL"]
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data"]})

        max_pivot = df_md_filtered.pivot_table(index="BUILDING", columns="Period", values="Resale_Price", aggfunc="max").fillna(0)
        max_pivot = max_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]
        
        project_towns = df_md_filtered.groupby("BUILDING")["Town"].first()
        l12m_max = last_12m_md.groupby("BUILDING")["Resale_Price"].max().rename("L12M Max")

        result = max_pivot.join([project_towns, l12m_max], how="left").fillna(0).reset_index().rename(columns={"BUILDING": "Project Name"})
        result.insert(1, "Town", result.pop("Town"))
        result = result.sort_values(by="L12M Max", ascending=False)

        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 1)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        cols_to_format = [c for c in result.columns if c not in ["Project Name", "Town"]]
        for col in cols_to_format:
            result[col] = result[col].map(lambda x: f"${x/1e6:.2f}M" if x > 0 else "-")

        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
            {"cols": [len(result.columns)-1], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
            *heatmap_styles
        ])

    # ---- Table 8D: Project Max PSF ----
    @render.data_frame
    def project_max_psf():
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        df_md_filtered = df_md_filtered[df_md_filtered["BUILDING"] != "NIL"]
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data"]})

        psf_pivot = df_md_filtered.pivot_table(index="BUILDING", columns="Period", values="PSF", aggfunc="max").fillna(0)
        psf_pivot = psf_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]
        
        project_towns = df_md_filtered.groupby("BUILDING")["Town"].first()
        l12m_psf = last_12m_md.groupby("BUILDING")["PSF"].max().rename("L12M Max PSF")

        result = psf_pivot.join([project_towns, l12m_psf], how="left").fillna(0).reset_index().rename(columns={"BUILDING": "Project Name"})
        result.insert(1, "Town", result.pop("Town"))
        result = result.sort_values(by="L12M Max PSF", ascending=False)

        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 1)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        cols_to_format = [c for c in result.columns if c not in ["Project Name", "Town"]]
        for col in cols_to_format:
            result[col] = result[col].map(lambda x: f"${x:,.0f}" if x > 0 else "-")

        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
            {"cols": [len(result.columns)-1], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
            *heatmap_styles
        ])

    # ---- Table 8E/F: Project Median Helper ----
    def render_project_median(column_name, is_price=True):
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        df_md_filtered = df_md_filtered[df_md_filtered["BUILDING"] != "NIL"]
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data"]})

        md_pivot = df_md_filtered.pivot_table(index="BUILDING", columns="Period", values=column_name, aggfunc="median").fillna(0)
        md_pivot = md_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]

        project_towns = df_md_filtered.groupby("BUILDING")["Town"].first()
        l12m_md_median = last_12m_md.groupby("BUILDING")[column_name].median().rename("L12M Median")

        result = md_pivot.join([project_towns, l12m_md_median], how="left").fillna(0).reset_index().rename(columns={"BUILDING": "Project Name"})
        result.insert(1, "Town", result.pop("Town"))
        result = result.sort_values(by="L12M Median", ascending=False)

        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 1)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        cols_to_format = [c for c in result.columns if c not in ["Project Name", "Town"]]
        for col in cols_to_format:
            if is_price:
                result[col] = result[col].map(lambda x: f"${x/1e6:.2f}M" if x > 0 else "-")
            else:
                result[col] = result[col].map(lambda x: f"${x:,.0f}" if x > 0 else "-")

        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
            {"cols": [len(result.columns)-1], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
            *heatmap_styles
        ])

    @render.data_frame
    def project_median_price():
        return render_project_median("Resale_Price", is_price=True)

    @render.data_frame
    def project_median_psf():
        return render_project_median("PSF", is_price=False)

    # ---- Table 8G: Project Median Lease Remaining ----
    @render.data_frame
    def project_median_lease():
        # 1. Get filtered Million-Dollar data
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        # 2. Filter out "NIL" Buildings
        df_md_filtered = df_md_filtered[df_md_filtered["BUILDING"] != "NIL"]
        
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data"]})

        # 3. Pivot for Median Lease Remaining
        # Group by Project (BUILDING) and Period
        lease_pivot = df_md_filtered.pivot_table(
            index="BUILDING", 
            columns="Period", 
            values="Lease.Remain", 
            aggfunc="median"
        ).fillna(0)

        # 4. Ensure Chronological Column Order
        lease_pivot = lease_pivot[df_md_filtered.sort_values("Period_sort")["Period"].unique()]

        # 5. Metadata and L12M Benchmarks
        project_towns = df_md_filtered.groupby("BUILDING")["Town"].first()
        
        # Filter NIL from L12M slice before grouping
        l12m_clean = last_12m_md[last_12m_md["BUILDING"] != "NIL"]
        l12m_lease_median = l12m_clean.groupby("BUILDING")["Lease.Remain"].median().rename("L12M Median Lease")

        # 6. Combine everything
        result = lease_pivot.join([project_towns, l12m_lease_median], how="left").fillna(0).reset_index()
        result = result.rename(columns={"BUILDING": "Project Name"})
        
        # Move Town to the second column
        result.insert(1, "Town", result.pop("Town"))
        
        # Sort by L12M Median (Newest buildings at the top)
        result = result.sort_values(by="L12M Median Lease", ascending=False)

        n_cols = len(result.columns)
        period_indices = list(range(2, n_cols - 2)) 
        heatmap_styles = apply_heatmap_style(result, period_indices)

        # 7. Formatting: Apply " Yrs" suffix to all numeric columns
        cols_to_format = [c for c in result.columns if c not in ["Project Name", "Town"]]
        for col in cols_to_format:
            # We use 1 decimal place to show half-years in medians
            result[col] = result[col].map(lambda x: f"{x:.0f} Yrs" if x > 0 else "-")

        # 8. Render with standard Table 8 styling
        return render.DataTable(result, styles=[
            {"style": {"padding": "4px 8px", "line-height": "1.1", "font-size": "13px", "white-space": "nowrap"}}, 
            {"cols": [0], "style": {"font-weight": "bold", "min-width": "220px"}}, 
            {"cols": [len(result.columns)-1], "style": {"background-color": "#f8fafc", "font-weight": "600"}},
            *heatmap_styles
        ])

    # ---- Table 9 Helper: Ranking Transactions with Highlighting ----
    def get_top_transactions(group_cols, sort_col):
        df_md_filtered, recent_periods, last_12m_md, ft_choice = prepared_table_df()
        
        if df_md_filtered.empty:
            return pd.DataFrame({"Message": ["No data available"]})

        # 1. Select and initial copy
        result = df_md_filtered[[
            "Flat_Type", "date", "Town", "BUILDING", "ADDRESS", 
            "Flat_Model", "Floor_Area_Sqm", "Storey_Range", "Lease.Remain", 
            "Resale_Price", "PSF"
        ]].copy()

        # 2. Format the Date column (MMM YYYY)
        result["Date"] = result["date"].dt.strftime("%b %Y").str.upper()
        
        # 3. Rename columns
        result = result.rename(columns={
            "Flat_Type": "Flat Type",
            "BUILDING": "Project Name",
            "ADDRESS": "Address",
            "Flat_Model": "Flat Model",
            "Floor_Area_Sqm": "Flat Size",
            "Storey_Range": "Storey Range",
            "Lease.Remain": "Lease Remaining",
            "Resale_Price": "Price"
        })

        mapped_groups = [c.replace("_", " ") if c == "Flat_Type" else c for c in group_cols]

        # 4. Rank and Filter for Top 3
        # We sort first, then assign a rank within each group
        result = result.sort_values(by=mapped_groups + [sort_col], ascending=[True] * len(mapped_groups) + [False])
        result["Rank"] = result.groupby(mapped_groups).cumcount() + 1
        result = result[result["Rank"] <= 3]

        # 5. Final column selection
        final_cols = [
            "Rank", "Flat Type", "Date", "Town", "Project Name", "Address", 
            "Flat Model", "Flat Size", "Storey Range", "Lease Remaining", 
            "Price", "PSF"
        ]
        result = result[final_cols]

        # 6. Formatting Numerics
        result["Price"] = result["Price"].map(lambda x: f"${x/1e6:.2f}M" if isinstance(x, (int, float)) else x)
        result["PSF"] = result["PSF"].map(lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) else x)
        result["Flat Size"] = result["Flat Size"].map(lambda x: f"{x:.0f} sqm" if isinstance(x, (int, float)) else x)
        result["Lease Remaining"] = result["Lease Remaining"].map(lambda x: f"{x:.0f} Yrs" if isinstance(x, (int, float)) else x)

        # 7. Render with Conditional Styling for Rank 1
        return render.DataTable(
            result,
            styles=[
                # Global Styles
                {"style": {"padding": "4px 8px", "font-size": "12.5px", "white-space": "nowrap"}},
                
                # Column Widths (Adjusted indices because Rank is now col 0)
                {"cols": [1, 2, 3], "style": {"min-width": "80px"}},
                {"cols": [4], "style": {"min-width": "120px"}},
                {"cols": [5], "style": {"min-width": "180px"}},
                {"cols": [6, 7], "style": {"min-width": "60px"}},
                {"cols": [10, 11], "style": {"min-width": "60px"}},
                
                # Conditional seperator after the third ranked entry for each flat type
                {
                    "rows": [i for i, r in enumerate(result["Rank"]) if r == 3],
                    "style": {
                        "border-bottom": "1.5px dotted #cbd5e1"  # Soft slate color
                    }
                },

                # Conditional Highlight: If Rank (Col 0) is 1, highlight the row
                {
                    "rows": [i for i, r in enumerate(result["Rank"]) if r == 1],
                    "style": {"background-color": "#f8f9fa"}
                }
            ],
            height="auto",
            width="100%"
        )
    @render.data_frame
    def high_max_price():
        return get_top_transactions(["Flat_Type"], "Price")

    @render.data_frame
    def high_max_psf():
        return get_top_transactions(["Flat_Type"], "PSF")

    @render.data_frame
    def high_town_level():
        return get_top_transactions(["Town", "Flat_Type"], "Price")

# Run app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)

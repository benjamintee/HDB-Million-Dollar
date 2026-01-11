# Million-Dollar Flat Dashboard

# Load libraries 
import pandas as pd
import plotly.express as px
from shinywidgets import output_widget, render_widget
from shiny import App, ui
from shiny import render, reactive
from pathlib import Path

# Load data
data_path = r"data\clean\HDB_Resale_Transactions_Merged_20260108.csv.gz"
df = pd.read_csv(data_path, compression='gzip')
css_path = Path(__file__).parent / "styles.css"

# Ensure a proper date column
df["date"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str).str.zfill(2) + "-01"
)

df["Flat_Type"] = df["Flat_Type"].replace(
            {"EXECUTIVE": "EXECUTIVE/MG", "MULTI-GENERATION": "EXECUTIVE/MG"}
        )

df["PSF"] = df["Resale_Price"] / (df["Floor_Area_Sqm"] * 10.764)

hdbtowns = df["Town"].unique()

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
                    ui.nav_panel("Median PSF", ui.output_data_frame("table_median_psf"),),
                    id="tab",  
                    title= "Table 7: Transactions by HDB Town" + "\u00A0\u00A0",  
                ),
                col_widths=[12]
        ),
    ),  
    ui.nav_panel("GEOGRAPHICAL DISTRIBUTION", "Page B content"),  
    ui.nav_panel("ANALYSIS", "Page C content"),  
    ui.nav_panel("TRANSACTIONS", "Page C content"),
    title="MILLION DOLLAR FLATS IN SINGAPORE",  
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
            text=totals["Total"],
            mode="text",
            textposition="top center",
            textfont=dict(size=12),
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
            yaxis=dict(range=[0, totals["Total"].max() * 1.12]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5,
                traceorder="reversed"
            ),
            legend_title_text=None
        )

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

        # Add % labels above points
        fig.add_scatter(
            x=share["Period_sort"],
            y=share["MD_Share_Percent"] + 0.12,
            text=share["MD_Share_Percent"].astype(str) + "%",
            mode="text",
            textposition="top center",
            textfont=dict(size=12),
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
            textfont=dict(size=11, color="white")
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
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(r=120)
        )

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
                "Max_PSF": "Max PSF",
                "Median_PSF": "Median PSF",
                "Median_PSF_All": "Median PSF (All Resale)"
            }[t.name]
        ))

        # ---- Add annotations (correct way) ----
        series_map = {
            "Max PSF": "Max_PSF",
            "Median PSF": "Median_PSF",
            "Median PSF (All Resale)": "Median_PSF_All"
        }

        for trace in fig.data:
            col = series_map[trace.name]
            for _, r in psf.iterrows():
                y = r[col]
                if pd.isna(y): continue

                label = f"{int(round(y)):,}" if y >= 1000 else f"{round(y,1)}"

                fig.add_annotation(
                    # 2. Ensure x matches the string in the dataframe exactly
                    x=str(r["Period_sort"]), 
                    y=y,
                    text=label,
                    showarrow=False,
                    # 3. Explicitly link to data coordinates
                    xref="x",
                    yref="y",
                    font=dict(color="white", size=10), # Slightly smaller to avoid overlap
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
            yaxis_title="Price per Square Foot (PSF)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.08,
                xanchor="center",
                x=0.5
            ),
            legend_title_text=None
        )

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
                font=dict(color=pt["color"], size=11, family="Arial Black"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=pt["color"],
                borderwidth=1,
                borderpad=2,
                align="left"
            )

        # 7. Final Layout
        fig.update_layout(
            xaxis=dict(
                type='category', 
                tickvals=agg_df["Period_sort_str"].unique(), 
                ticktext=agg_df["Period"].unique()
            ),
            yaxis=dict(showgrid=True, gridcolor='lightgrey'),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            legend_title_text=None, 
            margin=dict(t=20), 
            hovermode="x unified"
        )

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
            labels={y_col: f"Median {metric_choice} ($)", "Period_sort_str": period_choice}
        )

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
                font=dict(color=pt["color"], size=11, family="Arial Black"),
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
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            legend_title_text=None, 
            margin=dict(t=20),
            hovermode="x unified"
        )

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
        
        # This creates the Period_sort and Period columns
        df_filtered = filter_period(df_md, period_choice, n=n_periods)
        
        return df_filtered, period_choice

    @reactive.Calc
    def prepared_table_df():
        df_filtered, period_choice = table_data_base()
        
        if df_filtered.empty:
            return pd.DataFrame(), [], pd.DataFrame()
        
        # Identify unique periods to show as columns (already limited by filter_period)
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
        
        return df_filtered, recent_periods, last_12m_df

    # ---- Chart 7: Filtering Data to Show Trends by Town ----
    # 7A: Volume Trends
    @render.data_frame
    def table_volume():
        df_filtered, recent_periods, last_12m_df = prepared_table_df()
        
        if df_filtered.empty:
            return pd.DataFrame({"Result": ["No data for selection"]})

        # Pivot: Index=Town, Columns=Display Period, Values=Count
        pivot = df_filtered.pivot_table(
            index="Town", 
            columns="Period", 
            values="Resale_Price", 
            aggfunc="count"
        ).fillna(0)

        # Sort columns based on Period_sort to ensure chronological order in the table
        # Filter_period helper makes Period_sort a datetime, so this works:
        pivot = pivot[df_filtered.sort_values("Period_sort")["Period"].unique()]

        # Add Last 12 Months column
        l12m = last_12m_df.groupby("Town").size().rename("Last 12 Months")
        
        # Combine
        result = pivot.join(l12m, how="left").fillna(0).astype(int)
        
        # Sort by the value in the 'Last 12 Months'
        result = result.sort_values(by="Last 12 Months", ascending=False).reset_index()
        
        return render.DataTable(
            result,
            styles=[
                {
                    # Styling for every cell in the data table
                    "style": {
                        "padding": "4px 8px", 
                        "font-size": "13.5px", 
                        "line-height": "1.1",
                        "white-space": "nowrap"
                    }
                },
                {
                    # Bold the Town names in the first column
                    "cols": [0],
                    "style": {"font-weight": "bold"}
                }
            ],
            height="auto",
            width="100%"
        )
    # Chart 7B: Share of transactions by Town 
    @render.data_frame
    def table_share():
        # 1. Get filtered Million-Dollar data and L12M slice from reactive calc
        df_md_filtered, recent_periods, last_12m_md = prepared_table_df()
        
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
        result = result.sort_values(by="Last 12 Months (%)", ascending=False)

        # 9. Formatting: Convert to string with 1 decimal place and % sign
        cols_to_format = [c for c in result.columns if c != "Town"]
        for col in cols_to_format:
            result[col] = result[col].map("{:.1f}%".format)

        # 10. Render with Compact Styling
        return render.DataTable(
            result,
            styles=[
                {
                    "style": {
                        "padding": "4px 8px", 
                        "font-size": "13px", 
                        "line-height": "1.1",
                        "white-space": "nowrap"
                    }
                },
                {
                    "cols": [0], # Bold the Town column
                    "style": {"font-weight": "bold"}
                }
            ],
            height="auto",
            width="100%"
        )
    # Table 7C: Max Price for each town 
    @render.data_frame
    def table_max_price():
        # 1. Get filtered Million-Dollar data from reactive calc
        df_md_filtered, recent_periods, last_12m_md = prepared_table_df()
        
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
        result = max_pivot.join([historical_max, l12m_max], how="left").fillna(0).reset_index()
        
        # Sort by Historical Max to see the "Prestige" towns at the top
        result = result.sort_values(by= "ATH Max", ascending=False)

        # 7. Formatting: Convert to "$X.XXM" strings
        cols_to_format = [c for c in result.columns if c != "Town"]
        for col in cols_to_format:
            result[col] = result[col].apply(
                lambda x: f"${x/1_000_000:.2f}M" if x > 0 else "-"
            )

        # 8. Render with same compact styling
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold"}}
            ],
            height="auto",
            width="100%"
        )
    # Chart 7D: Max PSF for each town
    @render.data_frame
    def table_max_psf():
        # 1. Get filtered Million-Dollar data from reactive calc
        df_md_filtered, recent_periods, last_12m_md = prepared_table_df()
        
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
        result = psf_pivot.join([historical_psf, l12m_psf], how="left").fillna(0).reset_index()
        
        # Sort by L12M Max PSF to see current "hot" areas
        result = result.sort_values(by="L12M Max PSF", ascending=False)

        # 7. Formatting: Convert to "$X,XXX" strings
        cols_to_format = [c for c in result.columns if c != "Town"]
        for col in cols_to_format:
            result[col] = result[col].apply(
                lambda x: f"${x:,.0f}" if x > 0 else "-"
            )

        # 8. Render with compact styling
        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold"}}
            ],
            height="auto",
            width="100%"
        )
    # Table 7D/7E: Median Price and Median PSF 
    def render_median_table(column_name, is_price=True):
        # 1. Get filtered Million-Dollar data
        df_md_filtered, recent_periods, last_12m_md = prepared_table_df()
        
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
        all_resale_median = df_all_12m.groupby("Town")[column_name].median().rename("All Resale")

        # 4. Join and Sort
        # The order will be: Town, [Months...], L12M MD Median, All Resale
        result = md_pivot.join([l12m_md_median, all_resale_median], how="left").fillna(0).reset_index()
        
        # Sort by the Million Dollar Median performance
        result = result.sort_values(by="L12M MD Median", ascending=False)

        # 5. Formatting Logic
        cols_to_format = [c for c in result.columns if c != "Town"]
        for col in cols_to_format:
            if is_price:
                result[col] = result[col].apply(lambda x: f"${x/1e6:.2f}M" if x > 0 else "-")
            else:
                result[col] = result[col].apply(lambda x: f"${x:,.0f}" if x > 0 else "-")

        return render.DataTable(
            result,
            styles=[
                {"style": {"padding": "4px 8px", "font-size": "13px", "line-height": "1.1", "white-space": "nowrap"}},
                {"cols": [0], "style": {"font-weight": "bold"}},
                # Highlight the "All Resale" column in a light grey to distinguish it
                {"cols": [len(result.columns)-1], "style": {"background-color": "#f8f9fa", "font-style": "italic"}}
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

# Run app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)

# HDB Million Dollar Flat Dashboard

## Overview
This interactive dashboard provides a comprehensive overview of trends and insights relating to **Million Dollar HDB resale flat transactions** in Singapore. As these transactions tend to form and shape market expectations about the public housing market, this tool allows users to analyze the specific market dynamics, geographical distributions, and price movements to bring out emerging trends. 

## Data Sources & Methodology
The application utilizes the following resources:

* **HDB Resale Data:** All transaction records are sourced from the [Official HDB Resale Dataset on Data.gov.sg](https://beta.data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view).
* **Geospatial Data:** To map and analyze the proximity of transactions, addresses were geocoded using the **OneMap API**. Detailed information on the geocoding process and technical implementation can be found in the [OneMap.gov.sg API Documentation](https://www.onemap.gov.sg/apidocs/).

## Features & Navigation

The dashboard is organized into thematic sections to facilitate deep dives into the data:

* **Market Trends:** Analyze volume and price movements over time with dynamic charts.
* **Geographical Distribution:** Identify "million-dollar hotspots" across different HDB Towns and specific projects.
* **Price & PSF Analysis:** Compare Maximum and Median prices, as well as Price Per Square Foot (PSF) metrics.
* **Heatmap Insights:** Real-time table styling that uses an emerald-tinted power scale to highlight areas of significant market activity.

## Tech Stack
The dashboard is built using **Python [Shiny](https://shiny.posit.co/py/)** and **[bslib](https://rstudio.github.io/bslib/)** for a clean, professional-grade, and responsive dashboard experience. It leverages `pandas` for data processing and `plotly` for interactive visualizations.

---
*Note: This dashboard is for informational purposes and reflects data available as of the latest registration of resale transactions.*

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analizador S&P 500 y NASDAQ", layout="wide")

@st.cache_data(ttl=86400)
def obtener_tickers():
    """Obtiene la lista de componentes principal del S&P 500 mediante Wikipedia"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tabla = pd.read_html(url)[0]
        tickers = tabla['Symbol'].str.replace('.', '-').tolist()
        return tickers
    except Exception:
        # Fallback de activos principales en caso de restricción de scraping
        return ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "V"]

st.title("📈 Monitor de Rendimientos S&P 500")

# Panel lateral - Filtros
st.sidebar.header("Parámetros de Filtrado")

ticker_list = obtener_tickers()
activos_seleccionados = st.sidebar.multiselect(
    "Seleccionar Tickers específicos:",
    options=ticker_list,
    default=ticker_list[:10]
)

periodo = st.sidebar.selectbox(
    "Agrupar rendimiento por:",
    options=["Día", "Semana", "Mes", "Año"]
)

rango_dias = st.sidebar.slider("Días de historial a descargar:", 30, 365, 180)

if st.sidebar.button("Descargar y Calcular Data"):
    if not activos_seleccionados:
        st.warning("Selecciona al menos un ticker para continuar.")
    else:
        with st.spinner("Obteniendo cotizaciones en vivo..."):
            # Descarga de datos masivos con yfinance
            data = yf.download(activos_seleccionados, period=f"{rango_dias}d")['Close']
            
            if data.empty:
                st.error("No se pudieron obtener datos. Intenta con otros tickers.")
            else:
                # Regla de re-muestreo según opción seleccionada
                freq_map = {"Día": "D", "Semana": "W", "Mes": "M", "Año": "Y"}
                freq = freq_map[periodo]

                # Resampleo y cálculo de variaciones porcentuales
                resampled = data.resample(freq).last()
                pct_change = resampled.pct_change() * 100

                st.subheader(f"Variación Porcentual Agrupada por {periodo}")
                st.dataframe(pct_change.style.highlight_max(axis=0, color='lightgreen').highlight_min(axis=0, color='pink'))

                # Formateo de tabla para gráficos
                df_melted = pct_change.reset_index().melt(id_vars=['Date'], var_name='Ticker', value_name='Variacion_%')
                df_melted = df_melted.dropna()

                # Visualización interactiva
                fig = px.bar(
                    df_melted, 
                    x='Date', 
                    y='Variacion_%', 
                    color='Ticker', 
                    barmode='group',
                    title=f"Evolución Porcentual ({periodo})"
                )
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Configura los parámetros en el panel izquierdo y presiona 'Descargar y Calcular Data'.")
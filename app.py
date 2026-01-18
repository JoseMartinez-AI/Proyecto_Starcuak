import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

from models import StarcuakDB, AnalizadorIA, FileManager

# Instancias
db = StarcuakDB()
ia = AnalizadorIA()
fm = FileManager()

st.set_page_config(page_title="Starcuak Admin Pro", page_icon="☕", layout="wide")

# --- ESTADO DE SESIÓN ---
if "modulo_seleccionado" not in st.session_state:
    st.session_state.modulo_seleccionado = "Nueva Reseña"

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- BARRA LATERAL ---
st.sidebar.title("☕ Starcuak Panel")

# -- MENÚ DE NAVEGACIÓN ---
opciones = ["Nueva Reseña", "Carga CSV", "Base de Datos", "Dashboard Pro"]
indice_actual = opciones.index(st.session_state.modulo_seleccionado)
menu = st.sidebar.selectbox(
    "Módulo", opciones, index=indice_actual, key="menu_seleccion"
)
st.session_state.modulo_seleccionado = menu

# --- MÓDULO: NUEVA RESEÑA ---
if menu == "Nueva Reseña":
    st.header("📝 Nueva Reseña Manual")
    with st.form("form_manual", clear_on_submit=True):
        prod = st.selectbox("Café", ["Espresso", "Americano", "Latte", "Capuccino"])
        txt = st.text_area("Comentario", placeholder="Escriba el comentario aquí...")

        if st.form_submit_button("Analizar"):
            if txt.strip():
                label, score = ia.analizar(txt)
                current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                db.insertar_resena(prod, txt, label, score, current_date)
                fm.registrar_log(f"Analisis Manual: {prod} -> {label}")

                st.info(f'**Comentario procesado:**\n "{txt}"')
                st.success(
                    f"**✅ Sentimiento:** {label} | **Confianza del Modelo:** {score:.2f}"
                )
            else:
                st.warning("⚠️ El comentario no puede estar vacío.")

# --- MÓDULO: CARGA CSV ---
elif menu == "Carga CSV":
    st.header("📁 Procesamiento Masivo de Archivos")
    st.info("Asegúrese de que el CSV tenga las columnas: producto, comentario, fecha")
    archivo = st.file_uploader(
        "Subir CSV", type=["csv"], key=f"uploader_{st.session_state.uploader_key}"
    )

    if archivo:
        df = fm.leer_csv(archivo)
        df.columns = df.columns.str.strip().str.lower()
        df["comentario"] = df["comentario"].astype(str)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")

        st.write("Vista previa de los datos a cargar:")
        st.dataframe(df.head(), use_container_width=True)

        if st.button("🚀 Procesar"):
            for _, r in df.iterrows():
                label, score = ia.analizar(str(r["comentario"]))
                f_val = r.get("fecha")
                f_final = f_val.strftime("%d/%m/%Y %H:%M") if pd.notna(f_val) else None
                db.insertar_resena(
                    r.get("producto", "Café"), r["comentario"], label, score, f_final
                )

            fm.registrar_log(f"Carga masiva: {len(df)} registros procesados.")
            st.success(f"Carga completada: {len(df)} registros procesados.")

# --- MÓDULO: BASE DE DATOS ---
elif menu == "Base de Datos":
    st.header("💾 Gestión de Datos")
    df_data = db.obtener_datos()
    if not df_data.empty:
        st.write(f"Total de registros: {len(df_data)}")
        busqueda = st.text_input("🔍 Buscar en comentarios")
        if busqueda:
            df_data = df_data[df_data["comentario"].str.contains(busqueda, case=False)]
        st.dataframe(df_data, use_container_width=True, hide_index=True)
    else:
        st.info("La base de datos está vacía.")

# --- MÓDULO: DASHBOARD PRO (CORREGIDO) ---
elif menu == "Dashboard Pro":
    st.header("📊 Análisis de Sentimiento Avanzado")
    df_data = db.obtener_datos()

    if not df_data.empty:
        # --- 1. NORMALIZACIÓN DE DATOS (Soluciona el error del 0.0%) ---
        # Aseguramos que los nombres coincidan con el mapa de colores
        df_data["sentimiento"] = (
            df_data["sentimiento"].fillna("NEU").astype(str).str.strip()
        )
        df_data["producto"] = (
            df_data["producto"].fillna("Otros").astype(str).str.strip()
        )
        df_data["fecha_dt"] = pd.to_datetime(
            df_data["fecha"], dayfirst=True, errors="coerce"
        )

        # Mapa de colores institucional
        colores_map = {"POS": "#2ecc71", "NEG": "#e74c3c", "NEU": "#f1c40f"}

        # --- 2. FILA 1: KPIs (Métricas principales) ---
        kpi1, kpi2, kpi3 = st.columns(3)
        total = len(df_data)
        # Conteo exacto tras normalizar
        pos_count = len(df_data[df_data["sentimiento"] == "POS"])
        pos_perc = (pos_count / total) * 100 if total > 0 else 0

        kpi1.metric("Total Reseñas", total)
        kpi2.metric("Sentimiento Positivo", f"{pos_perc:.1f}%")
        kpi3.metric("Confianza Promedio", f"{df_data['confianza'].mean():.2f}")

        st.divider()

        # --- 3. FILA 2: GRÁFICOS DE DISTRIBUCIÓN ---
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Estado de Ánimo del Cliente")
            fig1, ax1 = plt.subplots()
            counts = df_data["sentimiento"].value_counts()
            # Asignamos colores según el sentimiento presente
            pie_colors = [colores_map.get(x, "#3498db") for x in counts.index]
            counts.plot(
                kind="pie", autopct="%1.1f%%", ax=ax1, colors=pie_colors, startangle=140
            )
            ax1.set_ylabel("")  # ELIMINA LA ETIQUETA 'count'
            st.pyplot(fig1)
            plt.close(fig1)

        with col_b:
            st.subheader("Sentimiento por Producto")
            ct = pd.crosstab(df_data["producto"], df_data["sentimiento"])
            fig2, ax2 = plt.subplots()
            # Mapeo seguro de colores para evitar 'ValueError'
            bar_colors = [colores_map.get(col, "#3498db") for col in ct.columns]
            ct.plot(kind="bar", stacked=True, ax=ax2, color=bar_colors)
            ax2.set_xlabel("Productos de Starcuak")
            ax2.set_ylabel("Cantidad de Reseñas")
            plt.xticks(rotation=45)
            plt.tight_layout()  # Evita que se corten los nombres de productos
            st.pyplot(fig2)
            plt.close(fig2)

        # --- 4. FILA 3: TENDENCIA TEMPORAL CON COLORES (CORRECCIÓN GRÁFICO AZUL) ---
        st.subheader("📈 Evolución Diaria de Opiniones")
        df_trend = df_data.copy()
        df_trend["fecha_solo"] = df_trend["fecha_dt"].dt.date

        if not df_trend["fecha_solo"].dropna().empty:
            # Agrupamos por fecha y sentimiento
            trend_data = (
                df_trend.groupby(["fecha_solo", "sentimiento"])
                .size()
                .unstack(fill_value=0)
            )

            # Ordenamos columnas para que los colores coincidan siempre
            ordered_cols = [c for c in ["NEG", "NEU", "POS"] if c in trend_data.columns]
            trend_data = trend_data[ordered_cols]

            # Asignamos los colores específicos (Rojo, Amarillo, Verde)
            line_colors = [colores_map.get(c) for c in ordered_cols]

            # Graficamos con el parámetro 'color'
            st.line_chart(trend_data, color=line_colors, y_label="Número de Reseñas")

        # --- 5. CUADRO DE RESUMEN EJECUTIVO ---
        st.divider()
        st.subheader("📋 Resumen Ejecutivo")
        r1, r2 = st.columns(2)

        prod_pos = df_data[df_data["sentimiento"] == "POS"]["producto"].value_counts()
        prod_neg = df_data[df_data["sentimiento"] == "NEG"]["producto"].value_counts()

        with r1:
            if not prod_pos.empty:
                st.success(f"🌟 **Producto Estrella:** {prod_pos.idxmax()}")
            else:
                st.info("No hay suficientes datos positivos aún.")

        with r2:
            if not prod_neg.empty:
                st.error(f"⚠️ **Punto de Mejora:** {prod_neg.idxmax()}")
            else:
                st.success("✅ No se detectan quejas recurrentes.")

    else:
        st.info("Sin datos para graficar.")

st.sidebar.divider()

# --- BOTÓN DE LIMPIEZA DE DATOS ---
if st.sidebar.button("🗑️ Limpiar Base de Datos"):
    try:
        db.limpiar_datos()
        fm.registrar_log("Base de datos limpiada por el usuario.")
        st.sidebar.success("¡Datos eliminados!")
        st.session_state.uploader_key += 1
        st.session_state.modulo_seleccionado = "Base de Datos"
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al limpiar datos: {e}")

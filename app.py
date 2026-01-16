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

# Inicializa el contador para resetear el cargador de archivos
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
        prod = st.selectbox(
            "Café", ["Espresso", "Americano", "Latte", "Capuccino"]
        )
        txt = st.text_area("Comentario", placeholder="Escriba el comentario aquí...")

        if st.form_submit_button("Analizar"):
            if txt.strip():
                label, score = ia.analizar(txt)
                current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                db.insertar_resena(prod, txt, label, score, current_date)
                fm.registrar_log(f"Analisis Manual: {prod} -> {label}")

                st.info(f"**Comentario procesado:**\n \"{txt}\"")
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

        # Casteo previo para normalizar los tipos de datos
        df["comentario"] = df["comentario"].astype(str)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")

        st.write("Vista previa de los datos a cargar:")
        st.dataframe(df.head(), use_container_width=True)

        if st.button("🚀 Procesar"):
            for _, r in df.iterrows():
                label, score = ia.analizar(str(r["comentario"]))
                # Validar fecha del CSV
                f_val = r.get("fecha")
                f_final = f_val.strftime("%d/%m/%Y %H:%M") if pd.notna(f_val) else None

                db.insertar_resena(
                    r.get("producto", "Café"), r["comentario"], label, score, f_final
                )

            fm.registrar_log(f"Carga masiva: {len(df)} registros procesados.")
            st.success(f"Carga completada: {len(df)} registros procesados.")

# --- MÓDULO: BASE DE DATOS (NUEVO) ---
elif menu == "Base de Datos":
    st.header("💾 Gestión de Datos ")
    df_data = db.obtener_datos()
    if not df_data.empty:
        st.write(f"Total de registros: {len(df_data)}")
        # Buscador simple
        busqueda = st.text_input("🔍 Buscar en comentarios")
        if busqueda:
            df_data = df_data[df_data["comentario"].str.contains(busqueda, case=False)]

        st.dataframe(df_data, use_container_width=True, hide_index=True)
    else:
        st.info("La base de datos está vacía.")

# --- MÓDULO: DASHBOARD PRO (MEJORADO) ---
elif menu == "Dashboard Pro":
    st.header("📊 Análisis de Sentimiento Avanzado")
    df_data = db.obtener_datos()

    if not df_data.empty:
        # Preparación de datos para gráficos
        df_data["fecha_dt"] = pd.to_datetime(df_data["fecha"], dayfirst=True)

        # FILA 1: KPIs
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Reseñas", len(df_data))
        pos_perc = (
            len(df_data[df_data["sentimiento"] == "Positivo"]) / len(df_data)
        ) * 100
        kpi2.metric("Sentimiento Positivo", f"{pos_perc:.1f}%")
        kpi3.metric("Confianza Promedio", f"{df_data['confianza'].mean():.2f}")

        # FILA 2: Gráficos principales
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Distribución Global")
            fig1, ax1 = plt.subplots()
            df_data["sentimiento"].value_counts().plot(
                kind="pie",
                autopct="%1.1f%%",
                ax=ax1,
                colors=["#2ecc71", "#e74c3c", "#f1c40f"],
            )
            st.pyplot(fig1)

        with col_b:
            st.subheader("Sentimiento por Producto")
            # Gráfico de barras apiladas
            ct = pd.crosstab(df_data["producto"], df_data["sentimiento"])
            fig2, ax2 = plt.subplots()
            ct.plot(kind="bar", stacked=True, ax=ax2)
            plt.xticks(rotation=45)
            st.pyplot(fig2)

        # FILA 3: Tendencia Temporal
        st.subheader("📈 Tendencia de Reseñas por Día")
        df_line = (
            df_data.groupby(df_data["fecha_dt"].dt.date)
            .size()
            .reset_index(name="cantidad")
        )
        st.line_chart(df_line.set_index("fecha_dt"))

    else:
        st.info("Sin datos para graficar.")

st.sidebar.divider()

# --- BOTÓN DE LIMPIEZA DE DATOS ---
if st.sidebar.button("🗑️ Limpiar Base de Datos"):
    try:
        db.limpiar_datos()
        fm.registrar_log("Base de datos limpiada por el usuario.")
        st.sidebar.success("¡Datos eliminados!")

        st.session_state.uploader_key += 1 # Reinicia el cargador de archivos
        st.session_state.modulo_seleccionado = "Base de Datos"
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al limpiar datos: {e}")

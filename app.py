import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Importación centralizada gracias al __init__.py en la carpeta models
from models import StarcuakDB, AnalizadorIA, FileManager

# 1. INSTANCIAS DE CLASES
db = StarcuakDB()
ia = AnalizadorIA()
fm = FileManager()

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Starcuak Admin Pro", page_icon="☕", layout="wide")

# 3. ESTADO DE SESIÓN (Persistencia de datos en la interfaz)
if "modulo_seleccionado" not in st.session_state:
    st.session_state.modulo_seleccionado = "Nueva Reseña"

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- BARRA LATERAL (Navegación y Mantenimiento) ---
st.sidebar.title("☕ Starcuak Panel")

opciones = ["Nueva Reseña", "Carga CSV", "Base de Datos", "Dashboard Pro"]
indice_actual = opciones.index(st.session_state.modulo_seleccionado)
menu = st.sidebar.selectbox(
    "Módulo", opciones, index=indice_actual, key="menu_seleccion"
)
st.session_state.modulo_seleccionado = menu

st.sidebar.divider()

# --- BOTÓN DE LIMPIEZA DE DATOS ---
if st.sidebar.button("🗑️ Limpiar Base de Datos"):
    try:
        db.limpiar_datos()
        fm.registrar_log("Base de datos limpiada por el usuario.")
        st.sidebar.success("¡Base de datos vaciada!")

        # Reseteamos el cargador de archivos y redirigimos a Base de Datos
        st.session_state.uploader_key += 1
        st.session_state.modulo_seleccionado = "Base de Datos"
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al limpiar datos: {e}")

# --- MÓDULO 1: NUEVA RESEÑA ---
if menu == "Nueva Reseña":
    st.header("📝 Nueva Reseña Manual")
    # clear_on_submit limpia el texto automáticamente después de analizar
    with st.form("form_manual", clear_on_submit=True):
        prod = st.selectbox("Café", ["Espresso", "Americano", "Latte", "Capuccino"])
        txt = st.text_area("Comentario", placeholder="Escriba el comentario aquí...")

        if st.form_submit_button("Analizar"):
            if txt.strip():
                label, score = ia.analizar(txt)
                current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                db.insertar_resena(prod, txt, label, score, current_date)
                fm.registrar_log(f"Analisis Manual: {prod} -> {label}")

                # Resultado visual para el usuario
                st.info(f"**Comentario procesado:**\n\n{txt}")
                st.success(f"**✅ Sentimiento:** {label} | **Confianza:** {score:.2f}")
            else:
                st.warning("⚠️ El comentario no puede estar vacío.")

# --- MÓDULO 2: CARGA CSV ---
elif menu == "Carga CSV":
    st.header("📁 Procesamiento Masivo de Archivos")
    st.info("Requisito: El CSV debe contener la columna 'comentario'.")

    archivo = st.file_uploader(
        "Subir CSV", type=["csv"], key=f"uploader_{st.session_state.uploader_key}"
    )

    if archivo:
        df = fm.leer_csv(archivo)
        df.columns = df.columns.str.strip().str.lower()

        if "comentario" not in df.columns:
            st.error("❌ Error: No se encontró la columna 'comentario' en el archivo.")
        else:
            df["comentario"] = df["comentario"].astype(str)
            if "fecha" in df.columns:
                df["fecha"] = pd.to_datetime(
                    df["fecha"], dayfirst=True, errors="coerce"
                )

            st.write("Vista previa de los datos:")
            st.dataframe(df.head(3), use_container_width=True)

            if st.button("🚀 Iniciar Procesamiento Masivo"):
                progreso = st.progress(0)
                total_filas = len(df)

                for i, r in df.iterrows():
                    label, score = ia.analizar(str(r["comentario"]))
                    f_val = r.get("fecha")
                    f_final = (
                        f_val.strftime("%d/%m/%Y %H:%M") if pd.notna(f_val) else None
                    )

                    db.insertar_resena(
                        r.get("producto", "Café"),
                        r["comentario"],
                        label,
                        score,
                        f_final,
                    )
                    progreso.progress((i + 1) / total_filas)

                fm.registrar_log(f"Carga masiva: {total_filas} registros.")
                st.success(f"✅ Carga completada: {total_filas} registros procesados.")

# --- MÓDULO 3: BASE DE DATOS ---
elif menu == "Base de Datos":
    st.header("💾 Gestión de Datos")
    df_data = db.obtener_datos()
    if not df_data.empty:
        st.write(f"Total de registros: **{len(df_data)}**")
        busqueda = st.text_input("🔍 Buscar en comentarios o productos")
        if busqueda:
            df_data = df_data[
                df_data["comentario"].str.contains(busqueda, case=False)
                | df_data["producto"].str.contains(busqueda, case=False)
            ]
        st.dataframe(df_data, use_container_width=True, hide_index=True)
    else:
        st.info("La base de datos está vacía.")

# --- MÓDULO 4: DASHBOARD PRO ---
elif menu == "Dashboard Pro":
    st.header("📊 Análisis de Sentimiento Avanzado")
    df_raw = db.obtener_datos()

    if not df_raw.empty:
        # --- 1. NORMALIZACIÓN Y FILTRO DE FECHAS ---
        df_raw["fecha_dt"] = pd.to_datetime(
            df_raw["fecha"], dayfirst=True, errors="coerce"
        )
        df_raw["sentimiento"] = (
            df_raw["sentimiento"].fillna("NEU").astype(str).str.strip().str.upper()
        )

        # Filtro de Rango en Sidebar
        st.sidebar.subheader("Filtros")
        min_d = df_raw["fecha_dt"].min().date()
        max_d = df_raw["fecha_dt"].max().date()
        rango = st.sidebar.date_input("Rango de Análisis", [min_d, max_d])

        if len(rango) == 2:
            inicio, fin = rango
            df_data = df_raw[
                (df_raw["fecha_dt"].dt.date >= inicio)
                & (df_raw["fecha_dt"].dt.date <= fin)
            ]
        else:
            df_data = df_raw

        # --- 2. KPIs ---
        kpi1, kpi2, kpi3 = st.columns(3)
        total = len(df_data)
        pos_count = len(df_data[df_data["sentimiento"] == "POS"])
        pos_perc = (pos_count / total) * 100 if total > 0 else 0

        kpi1.metric("Total Reseñas", total)
        kpi2.metric("Sentimiento Positivo", f"{pos_perc:.1f}%")
        kpi3.metric("Confianza Promedio", f"{df_data['confianza'].mean():.2f}")

        st.divider()

        # --- 3. GRÁFICOS (Matplotlib) ---
        col_a, col_b = st.columns(2)
        colores_map = {"POS": "#2ecc71", "NEG": "#e74c3c", "NEU": "#f1c40f"}

        with col_a:
            st.subheader("Distribución Global")
            counts = df_data["sentimiento"].value_counts()
            fig1, ax1 = plt.subplots()
            counts.plot(
                kind="pie",
                autopct="%1.1f%%",
                ax=ax1,
                colors=[colores_map.get(x, "#3498db") for x in counts.index],
            )
            ax1.set_ylabel("")  # Quita etiqueta 'count'
            st.pyplot(fig1)
            plt.close(fig1)

        with col_b:
            st.subheader("Sentimiento por Producto")
            ct = pd.crosstab(df_data["producto"], df_data["sentimiento"])
            fig2, ax2 = plt.subplots()
            ct.plot(
                kind="bar",
                stacked=True,
                ax=ax2,
                color=[colores_map.get(col) for col in ct.columns],
            )
            ax2.set_xlabel("Productos")
            ax2.set_ylabel("Cantidad de Reseñas")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

        # --- 4. TENDENCIA TEMPORAL ---
        st.subheader("📈 Evolución Diaria")
        df_trend = df_data.copy()
        df_trend["fecha_solo"] = df_trend["fecha_dt"].dt.date
        if not df_trend["fecha_solo"].dropna().empty:
            trend_pivot = (
                df_trend.groupby(["fecha_solo", "sentimiento"])
                .size()
                .unstack(fill_value=0)
            )
            # Ordenamos para asegurar colores: Rojo, Amarillo, Verde
            cols = [c for c in ["NEG", "NEU", "POS"] if c in trend_pivot.columns]
            st.line_chart(
                trend_pivot[cols],
                color=[colores_map.get(c) for c in cols],
                y_label="Reseñas",
            )

        # --- 5. RESUMEN EJECUTIVO ---
        st.divider()
        st.subheader("📋 Resumen Ejecutivo")
        r1, r2 = st.columns(2)
        prod_pos = df_data[df_data["sentimiento"] == "POS"]["producto"].value_counts()
        prod_neg = df_data[df_data["sentimiento"] == "NEG"]["producto"].value_counts()

        with r1:
            if not prod_pos.empty:
                st.success(f"🌟 **Producto Estrella:** {prod_pos.idxmax()}")
        with r2:
            if not prod_neg.empty:
                st.error(f"⚠️ **Punto de Mejora:** {prod_neg.idxmax()}")
    else:
        st.info("No hay datos para el rango seleccionado.")

import streamlit as st
import matplotlib.pyplot as plt
from models.database import StarcuakDB
from models.ia_model import AnalizadorIA
from models.file_manager import FileManager

# Orquestación de la solución
db = StarcuakDB()
ia = AnalizadorIA()
fm = FileManager()

st.set_page_config(page_title="Starcuak Admin", page_icon="☕")
st.title("☕ Starcuak: Dashboard de Sentimiento")

st.sidebar.divider()
st.sidebar.subheader("Mantenimiento")
if st.sidebar.button("🗑️ Limpiar Base de Datos"):
    try:
        db.limpiar_datos()
        fm.registrar_log("Base de datos limpiada por el usuario.")
        st.sidebar.success("¡Datos eliminados correctamente!")
        # Forzar recarga para que el dashboard se actualice
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

menu = st.sidebar.selectbox("Módulo", ["Nueva Reseña", "Carga CSV", "Dashboard Pro"])

if menu == "Nueva Reseña":
    with st.form("starcuak_form"):
        prod = st.selectbox("Café/Acompañante", ["Espresso", "Americano", "Latte", "Capuccino"])
        txt = st.text_area("Opinión del cliente")
        if st.form_submit_button("Analizar"):
            label, score = ia.analizar(txt)
            db.insertar_resena(prod, txt, label, score)
            fm.registrar_log(f"Análisis manual: {prod} -> {label}")
            st.success(f"Sentimiento: {label} | Confianza: {score:.2f}")

elif menu == "Carga CSV":
    archivo = st.file_uploader("Subir CSV de reseñas", type=["csv"])
    if archivo:
        df = fm.leer_csv(archivo)
        # Normaliza columnas (quita espacios y pasa a minúsculas)
        df.columns = df.columns.str.strip().str.lower()
        
        if st.button("Procesar Todo"):
            for _, row in df.iterrows():
                l, s = ia.analizar(row['comentario'])
                db.insertar_resena(row.get('producto', 'Café'), row['comentario'], l, s)
            fm.guardar_binario(df.to_dict())
            st.success("¡Datos procesados y persistidos!")

elif menu == "Dashboard Pro":
    df_data = db.obtener_datos()
    if not df_data.empty:
        st.write("📊 Resumen de Impacto Starcuak")

        # Gráfico de pastel
        fig, ax = plt.subplots()
        df_data['sentimiento'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
        st.pyplot(fig)
        st.write("Registros en la Base de Datos:")
        st.dataframe(df_data, hide_index=True, use_container_width=True)
    else:
        st.info("Sin datos para mostrar.")
import pandas as pd
import random
from datetime import datetime, timedelta

# Carga de referencia para comentarios
original_df = pd.read_csv('Datos_1.csv', sep=';')
sample_comments = original_df['comentario'].unique().tolist()

# Configuración de restricciones
productos_validos = ["Espresso", "Capuccino", "Americano", "Latte"]
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 1, 14, 23, 59)

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    return start + timedelta(seconds=random.randrange(int_delta))

# Generación de los 100 registros
new_records = []
for _ in range(100):
    new_records.append({
        "producto": random.choice(productos_validos),
        "comentario": random.choice(sample_comments),
        "fecha": random_date(start_date, end_date).strftime("%d/%m/%Y %H:%M")
    })

# Guardado del archivo
df_new = pd.DataFrame(new_records)
df_new.to_csv('Nuevos_Datos_100.csv', sep=';', index=False)
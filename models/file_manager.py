import pandas as pd
import pickle
from datetime import datetime

class FileManager:
    @staticmethod
    def leer_csv(ruta):
        """Lectura de datos estructurados CSV con autodetección de separador."""
        try:
            # sep=None permite que pandas detecte si es coma (,) o punto y coma (;)
            return pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
        except Exception as e:
            raise Exception(f"Error al leer el archivo CSV: {e}")
    @staticmethod
    def guardar_binario(datos, ruta="data/outputs/backup_starcuak.dat"):
        """Persistencia en formato binario."""
        with open(ruta, "wb") as f:
            pickle.dump(datos, f)

    @staticmethod
    def registrar_log(mensaje, ruta="data/outputs/log.txt"):
        """Registro de operaciones en archivo de texto."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ruta, "a") as f:
            f.write(f"[{fecha}] {mensaje}\n")
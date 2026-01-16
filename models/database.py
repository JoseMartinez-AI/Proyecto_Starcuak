import sqlite3
import pandas as pd


class StarcuakDB:
    def __init__(self, db_path="data/starcuak.db"):
        self.db_path = db_path
        self._crear_tabla()

    def _crear_tabla(self):
        """Crea la estructura relacional inicial."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Resenas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        producto TEXT,
                        comentario TEXT,
                        sentimiento TEXT,
                        confianza REAL,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error de base de datos: {e}")

    def insertar_resena(self, producto, comentario, sentimiento, confianza, fecha=None):
        """Realiza operaciones DML de inserción."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "INSERT INTO Resenas (producto, comentario, sentimiento, confianza, fecha) VALUES (?, ?, ?, ?, ?)"
                cursor.execute(
                    query, (producto, comentario, sentimiento, confianza, fecha)
                )
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Fallo en la persistencia DML: {e}")

    def obtener_datos(self):
        """Recupera datos para el dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql("SELECT * FROM Resenas", conn)

    def limpiar_datos(self):
        """Elimina todos los registros y reinicia el contador de ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Eliminamos los datos de la tabla
                cursor.execute("DELETE FROM Resenas")
                # 2. Reiniciamos el contador de ID autoincremental de SQLite
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='Resenas'")
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Error al limpiar la base de datos: {e}")

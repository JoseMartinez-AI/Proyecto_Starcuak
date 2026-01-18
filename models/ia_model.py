from transformers import pipeline


class AnalizadorIA:
    def __init__(self):
        try:
            # Modelo preentrenado optimizado para sentimientos
            self.model = pipeline(
                "sentiment-analysis", model="finiteautomata/beto-sentiment-analysis"
            )
        except Exception:
            self.model = pipeline("sentiment-analysis")

    def analizar(self, texto):
        """Aplica el modelo y devuelve resultados interpretables."""
        if not texto.strip():
            return "NEUTRAL", 0.0
        resultado = self.model(texto)[0]
        return resultado["label"], resultado["score"]


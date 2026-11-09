from datetime import datetime, timedelta
from pathlib import Path
import random
import pandas as pd
from comum import cliente_s3, garantir_bucket, BUCKET

random.seed(42)
s3 = cliente_s3()
garantir_bucket(s3)

inicio = datetime(2026, 10, 1)
linhas = []
sensores = [
    ("S101", 1), ("S102", 1),
    ("S201", 2), ("S202", 2),
    ("S301", 3), ("S305", 3),
    ("S401", 4), ("S402", 4),
]

# Oito sensores, uma leitura a cada 30 minutos, durante sete dias.
for dia in range(7):
    data = inicio + timedelta(days=dia)
    for minuto in range(0, 24 * 60, 30):
        instante = data + timedelta(minutes=minuto)
        hora = instante.hour
        for sensor, andar in sensores:
            temperatura = round(22 + andar * 0.6 + random.uniform(-1.8, 1.8), 2)
            umidade = round(48 + random.uniform(-8, 8), 2)
            energia = round(0.35 + (0.25 if 8 <= hora < 18 else 0.05) + random.uniform(0, 0.12), 3)

            # Anomalia proposital para demonstrar a geração de alertas.
            if sensor == "S305" and instante.date().isoformat() == "2026-10-05" and 14 <= hora < 17:
                energia = round(energia * 3.5, 3)

            linhas.append({
                "timestamp": instante.isoformat(),
                "sensor_id": sensor,
                "andar": andar,
                "temperatura_c": temperatura,
                "umidade_pct": umidade,
                "energia_kwh": energia
            })

# Dados ruins intencionais para demonstrar a limpeza na camada Silver.
linhas.append({
    "timestamp": "2026-10-03T12:00:00",
    "sensor_id": "S101",
    "andar": 1,
    "temperatura_c": 999,
    "umidade_pct": 50,
    "energia_kwh": 0.5
})
linhas.append(linhas[0].copy())  # duplicata proposital

df = pd.DataFrame(linhas)
arquivo = Path("/tmp/leituras_sensores.csv")
df.to_csv(arquivo, index=False)

chave = "bronze/sensores/data=2026-10-01_a_2026-10-07/leituras.csv"
with arquivo.open("rb") as f:
    s3.put_object(
        Bucket=BUCKET,
        Key=chave,
        Body=f,
        ContentType="text/csv",
        Metadata={"origem": "sensores-automacao-predial", "schema-versao": "1"}
    )

print(f"Arquivo enviado para s3://{BUCKET}/{chave}")
print(f"Linhas geradas (incluindo dados de teste): {len(df):,}")

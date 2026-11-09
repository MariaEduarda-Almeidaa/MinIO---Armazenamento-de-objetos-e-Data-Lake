from io import BytesIO
import os
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from comum import cliente_s3, BUCKET

s3 = cliente_s3()
objetos = s3.list_objects_v2(Bucket=BUCKET, Prefix="bronze/sensores/").get("Contents", [])
csvs = [o["Key"] for o in objetos if o["Key"].endswith(".csv")]

if not csvs:
    raise SystemExit("Nenhum CSV encontrado. Execute primeiro 01_gerar_dados.py")

partes = []
for chave in csvs:
    resposta = s3.get_object(Bucket=BUCKET, Key=chave)
    partes.append(pd.read_csv(resposta["Body"]))

df = pd.concat(partes, ignore_index=True)
total_original = len(df)

# Limpeza: remove duplicatas, valores ausentes e medições fora dos limites didáticos.
df = df.drop_duplicates()
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
obrigatorias = ["timestamp", "sensor_id", "andar", "temperatura_c", "umidade_pct", "energia_kwh"]
df = df.dropna(subset=obrigatorias)
df = df[df["temperatura_c"].between(-10, 60)]
df = df[df["umidade_pct"].between(0, 100)]
df = df[df["energia_kwh"] >= 0]
df["data"] = df["timestamp"].dt.strftime("%Y-%m-%d")

# SILVER: dados limpos em Parquet.
silver_buffer = BytesIO()
pq.write_table(pa.Table.from_pandas(df, preserve_index=False), silver_buffer, compression="snappy")
s3.put_object(
    Bucket=BUCKET,
    Key="silver/sensores/leituras.parquet",
    Body=silver_buffer.getvalue(),
    ContentType="application/octet-stream",
    Metadata={"formato": "parquet", "camada": "silver"}
)

# GOLD: consumo diário total por andar.
gold_consumo = (
    df.groupby(["data", "andar"], as_index=False)["energia_kwh"]
      .sum()
      .rename(columns={"energia_kwh": "consumo_total_kwh"})
)
gold_consumo["consumo_total_kwh"] = gold_consumo["consumo_total_kwh"].round(3)
gold_consumo_buffer = BytesIO()
pq.write_table(pa.Table.from_pandas(gold_consumo, preserve_index=False), gold_consumo_buffer, compression="snappy")
s3.put_object(
    Bucket=BUCKET,
    Key="gold/indicadores/consumo_diario_por_andar.parquet",
    Body=gold_consumo_buffer.getvalue(),
    ContentType="application/octet-stream"
)

# GOLD: leituras acima do limite ilustrativo de 2,0 kWh por intervalo.
alertas = df[df["energia_kwh"] > 2.0][["timestamp", "sensor_id", "andar", "energia_kwh"]].copy()
alertas_buffer = BytesIO()
pq.write_table(pa.Table.from_pandas(alertas, preserve_index=False), alertas_buffer, compression="snappy")
s3.put_object(
    Bucket=BUCKET,
    Key="gold/alertas/alertas_consumo.parquet",
    Body=alertas_buffer.getvalue(),
    ContentType="application/octet-stream"
)

# COPIAS LOCAIS: grava CSVs na pasta "resultados" do projeto para abrir no Excel.
# O formato oficial do Data Lake continua sendo o Parquet no bucket.
pasta = Path(os.getenv("RESULTADOS_DIR", "/app/resultados"))
pasta.mkdir(parents=True, exist_ok=True)
opcoes_csv = dict(index=False, sep=";", decimal=",", encoding="utf-8-sig")
df.to_csv(pasta / "silver_leituras.csv", **opcoes_csv)
gold_consumo.to_csv(pasta / "gold_consumo_diario_por_andar.csv", **opcoes_csv)
alertas.to_csv(pasta / "gold_alertas_consumo.csv", **opcoes_csv)

print("Pipeline concluído!")
print(f"Registros originais: {total_original:,}")
print(f"Registros válidos na Silver: {len(df):,}")
print(f"Registros removidos na limpeza: {total_original - len(df):,}")
print("Objetos criados nas camadas Silver e Gold.")
print(f"Alertas de consumo encontrados: {len(alertas)}")
print(f"Copias CSV gravadas em: {pasta}  (pasta \"resultados\" do projeto)")
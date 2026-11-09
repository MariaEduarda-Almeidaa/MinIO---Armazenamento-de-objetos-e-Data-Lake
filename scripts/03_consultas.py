from io import BytesIO
import duckdb
import pyarrow.parquet as pq
from comum import cliente_s3, BUCKET

s3 = cliente_s3()

def baixar_parquet(chave):
    obj = s3.get_object(Bucket=BUCKET, Key=chave)
    return pq.read_table(BytesIO(obj["Body"].read())).to_pandas()

consumo = baixar_parquet("gold/indicadores/consumo_diario_por_andar.parquet")
alertas = baixar_parquet("gold/alertas/alertas_consumo.parquet")

con = duckdb.connect()
con.register("consumo_diario", consumo)
con.register("alertas", alertas)

print("\n=== CONSUMO TOTAL POR ANDAR ===")
resultado = con.execute("""
    SELECT andar, ROUND(SUM(consumo_total_kwh), 2) AS total_kwh
    FROM consumo_diario
    GROUP BY andar
    ORDER BY andar
""").df()
print(resultado.to_string(index=False))

print("\n=== ALERTAS DE CONSUMO ===")
if len(alertas):
    resultado_alertas = con.execute("""
        SELECT sensor_id, andar, COUNT(*) AS leituras_suspeitas,
               ROUND(MAX(energia_kwh), 2) AS pico_kwh
        FROM alertas
        GROUP BY sensor_id, andar
        ORDER BY pico_kwh DESC
    """).df()
    print(resultado_alertas.to_string(index=False))
else:
    print("Nenhum alerta encontrado.")

print("\nConsulta realizada com DuckDB sobre arquivos Parquet armazenados no Data Lake.")

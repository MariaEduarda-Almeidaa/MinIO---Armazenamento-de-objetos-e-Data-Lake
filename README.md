# Exemplo prático — MinIO e Data Lake de automação predial

Este projeto demonstra o uso do MinIO como armazenamento compatível com S3 em um pequeno Data Lake. O ambiente inclui:

- **MinIO**: armazena os objetos e disponibiliza a API S3 e o Console Web.
- **lab** (opcional): contêiner Python com scripts para gerar, transformar e consultar dados de sensores.

O arquivo `docker-compose.yml` constrói o MinIO a partir do código-fonte indicado em `minio-build/Dockerfile` e define os dois serviços. Os serviços podem ser iniciados juntos ou separadamente.

## Pré-requisitos

- Docker Desktop instalado e em execução.
- Acesso à internet no primeiro build, para baixar as imagens, dependências e o código-fonte do MinIO.
- Espaço livre em disco para as imagens e dependências.

Execute os comandos abaixo no terminal, dentro da pasta do projeto.

## Executar somente o MinIO

Para iniciar apenas o servidor MinIO, sem criar ou iniciar o contêiner `lab`:

```powershell
docker compose up -d --build minio
```

Nesse caso, **não é necessário usar as pastas `scripts/` e `resultados/`**: elas são montadas somente no serviço `lab` e servem para os exercícios de processamento. A pasta `minio-build/` é necessária porque contém o Dockerfile usado para construir a imagem do MinIO.

Confira o serviço:

```powershell
docker compose ps
```

Abra:

- Console Web: http://localhost:9001
- API S3: http://localhost:9000

Credenciais do laboratório:

- Usuário: `admin`
- Senha: `seminario123`

Essas credenciais são apenas para uso local e não devem ser usadas em produção.

Os dados do MinIO ficam no volume Docker `minio_data`, portanto continuam disponíveis após parar e iniciar o contêiner novamente.

## Executar o laboratório completo

Para iniciar o MinIO e também o contêiner Python usado nos exercícios:

```powershell
docker compose up -d --build
```

O primeiro build do MinIO compila o código-fonte e pode levar alguns minutos. O serviço `lab` permanece em execução aguardando os comandos dos exercícios.

Confira os contêineres:

```powershell
docker compose ps
```

As pastas locais `scripts/` e `resultados/` são montadas no contêiner `lab`:

- `scripts/`: scripts Python do laboratório.
- `resultados/`: cópias CSV geradas pelo pipeline, acessíveis diretamente no computador.

## Exercício: fluxo Bronze, Silver e Gold

Os comandos desta seção pressupõem que os dois serviços estejam em execução.

### 1. Gerar dados e gravar na Bronze

```powershell
docker exec minio-lab python scripts/01_gerar_dados.py
```

O script simula oito sensores em quatro andares, com leituras a cada 30 minutos durante sete dias. Também inclui uma duplicata e uma temperatura inválida para demonstrar a limpeza posterior. O bucket `datalake` é criado pelo script, se ainda não existir.

No Console Web, abra o bucket `datalake` e localize:

```text
bronze/
  sensores/
    data=2026-10-01_a_2026-10-07/
      leituras.csv
```

A camada Bronze contém os dados originais, antes do tratamento.

### 2. Transformar os dados para Silver e Gold

```powershell
docker exec minio-lab python scripts/02_pipeline.py
```

O pipeline lê os CSVs da Bronze, remove duplicatas e medições inválidas, e grava os dados tratados em Parquet. Também calcula o consumo diário por andar e identifica leituras acima do limite ilustrativo de 2,0 kWh por intervalo.

Os principais objetos gerados no bucket são:

```text
silver/
  sensores/
    leituras.parquet
gold/
  indicadores/
    consumo_diario_por_andar.parquet
  alertas/
    alertas_consumo.parquet
```

O pipeline também grava cópias CSV na pasta local `resultados/`, para abrir em uma planilha:

- `silver_leituras.csv`
- `gold_consumo_diario_por_andar.csv`
- `gold_alertas_consumo.csv`

Os arquivos Parquet no bucket são os dados do Data Lake; os CSVs locais são cópias para visualização.

### 3. Consultar os resultados com DuckDB

```powershell
docker exec minio-lab python scripts/03_consultas.py
```

O script lê os Parquet armazenados no MinIO e usa DuckDB para apresentar o consumo total por andar e resumir os alertas. O DuckDB executa no contêiner `lab`; ele não executa consultas dentro do servidor MinIO.

## Comandos úteis

Ver os logs do MinIO:

```powershell
docker compose logs minio
```

Parar e remover os contêineres, preservando os dados:

```powershell
docker compose down
```

Remover também o volume `minio_data` e apagar os dados armazenados no MinIO:

```powershell
docker compose down -v
```

**Atenção:** use `docker compose down -v` somente se quiser apagar os dados do laboratório e recomeçar do zero.

## Roteiro sugerido para apresentação

1. Abra o Console Web e mostre o bucket `datalake`.
2. Execute o script de geração e mostre o CSV na Bronze.
3. Execute o pipeline e mostre os Parquet nas camadas Silver e Gold.
4. Execute as consultas e mostre o consumo por andar e os alertas.
5. Explique que o MinIO armazena os objetos, enquanto o Python e o DuckDB fazem o processamento e as consultas.

## Limitações

Este é um laboratório local de nó único, com um único volume de armazenamento. Ele não demonstra alta disponibilidade ou tolerância a falhas de um cluster e não deve ser usado em produção.

"""Script de ingestão fiel para a Camada Bronze utilizando DuckDB.

Lê os arquivos CSV (incluindo compactados .csv.gz) do diretório `data/raw/`,
calcula o hash SHA-256 para rastreabilidade, adiciona o carimbo de auditoria
temporal (`_loaded_at`) e persiste os dados brutos sem alterações ou tipagem
no banco DuckDB `data/bronze/bronze.db`.
"""

import hashlib
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
BRONZE_DB_PATH = Path("data/bronze/bronze.db")
VALID_TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def calculate_sha256(file_path: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo para auditoria e rastreabilidade.

    Args:
        file_path: Caminho para o arquivo a ser lido.

    Returns:
        String hexadecimal representando o hash SHA-256 do arquivo.
    """
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_table_name(file_path: Path) -> str:
    """Extrai e valida o nome da tabela a partir do nome do arquivo CSV.

    Args:
        file_path: Caminho do arquivo CSV ou CSV.GZ.

    Returns:
        Nome da tabela sanitizado e validado.

    Raises:
        ValueError: Se o nome derivado não for um identificador SQL válido.
    """
    name = file_path.name
    if name.endswith(".csv.gz"):
        table_name = name[: -len(".csv.gz")]
    elif name.endswith(".csv"):
        table_name = name[: -len(".csv")]
    else:
        table_name = file_path.stem

    if not VALID_TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Nome de tabela inválido derivado do arquivo: {table_name}")
    return table_name


def list_raw_csv_files(raw_dir: Path) -> list[Path]:
    """Lista todos os arquivos CSV e CSV.GZ presentes no diretório raw.

    Args:
        raw_dir: Diretório contendo os arquivos brutos.

    Returns:
        Lista ordenada de caminhos para os arquivos CSV encontrados.
    """
    if not raw_dir.exists():
        logger.warning("Diretório raw não encontrado: %s", raw_dir)
        return []

    files = [
        p
        for p in raw_dir.iterdir()
        if p.is_file() and (p.name.endswith(".csv") or p.name.endswith(".csv.gz"))
    ]
    return sorted(files)


def ingest_csv_to_bronze(con: duckdb.DuckDBPyConnection, file_path: Path) -> str:
    """Ingere um único arquivo CSV no banco DuckDB da camada Bronze sem alterações.

    Args:
        con: Conexão ativa com o banco DuckDB.
        file_path: Caminho para o arquivo CSV bruto.

    Returns:
        Hash SHA-256 calculado para o arquivo ingerido.
    """
    table_name = extract_table_name(file_path)
    file_hash = calculate_sha256(file_path)
    loaded_at = datetime.now(UTC).isoformat()

    logger.info(
        "Ingerindo Bronze: %s -> %s (hash: %s)", file_path.name, table_name, file_hash
    )
    query = f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *, ? AS _loaded_at, ? AS _file_sha256
        FROM read_csv(?, all_varchar = true, header = true)
    """
    con.execute(query, [loaded_at, file_hash, str(file_path)])
    row_count = (con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone() or [0])[0]
    logger.info(
        "Concluído: %s | registros=%d | _loaded_at=%s", table_name, row_count, loaded_at
    )
    return file_hash


def run_bronze_ingestion(
    raw_dir: Path = RAW_DATA_DIR,
    db_path: Path = BRONZE_DB_PATH,
) -> dict[str, str]:
    """Executa o pipeline completo de ingestão da camada Raw para a camada Bronze.

    Args:
        raw_dir: Diretório de origem dos arquivos CSV brutos.
        db_path: Caminho do arquivo de banco de dados DuckDB de destino.

    Returns:
        Dicionário mapeando o nome de cada tabela ingerida ao seu hash SHA-256.
    """
    csv_files = list_raw_csv_files(raw_dir)
    if not csv_files:
        logger.warning("Nenhum arquivo CSV encontrado em %s", raw_dir)
        return {}

    db_path.parent.mkdir(parents=True, exist_ok=True)
    ingested_hashes: dict[str, str] = {}

    logger.info(
        "Conectando ao banco DuckDB Bronze em %s (%d arquivos encontrados)",
        db_path,
        len(csv_files),
    )
    with duckdb.connect(str(db_path)) as con:
        for file_path in csv_files:
            table_name = extract_table_name(file_path)
            ingested_hashes[table_name] = ingest_csv_to_bronze(con, file_path)

    logger.info(
        "Pipeline Bronze finalizado com sucesso. Total de tabelas: %d",
        len(ingested_hashes),
    )
    return ingested_hashes


if __name__ == "__main__":
    run_bronze_ingestion()

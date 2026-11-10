"""Testes unitários e de integração para a ingestão da Camada Bronze."""

import gzip
from pathlib import Path

import duckdb
import pytest

from src.ingestion.bronze_ingestion import (
    calculate_sha256,
    extract_table_name,
    list_raw_csv_files,
    run_bronze_ingestion,
)


def test_calculate_sha256_returns_expected_digest(tmp_path: Path) -> None:
    """Verifica se o cálculo de SHA-256 retorna o hash exato esperado."""
    sample_file = tmp_path / "sample.csv"
    sample_file.write_text("col1,col2\n1,a\n", encoding="utf-8")

    digest = calculate_sha256(sample_file)
    assert len(digest) == 64
    assert digest == calculate_sha256(sample_file)


def test_extract_table_name_handles_csv_and_csv_gz() -> None:
    """Verifica a extração do nome da tabela para arquivos .csv e .csv.gz."""
    assert (
        extract_table_name(Path("data/raw/olist_orders_dataset.csv"))
        == "olist_orders_dataset"
    )
    assert (
        extract_table_name(Path("data/raw/olist_orders_dataset.csv.gz"))
        == "olist_orders_dataset"
    )
    assert extract_table_name(Path("tabela_simples")) == "tabela_simples"


def test_extract_table_name_raises_on_invalid_identifier() -> None:
    """Garante que nomes de arquivo com caracteres inválidos geram ValueError."""
    with pytest.raises(ValueError, match="Nome de tabela inválido"):
        extract_table_name(Path("123-invalido!.csv"))


def test_list_raw_csv_files_filters_and_sorts(tmp_path: Path) -> None:
    """Verifica a listagem ordenada apenas de arquivos .csv e .csv.gz."""
    assert list_raw_csv_files(tmp_path / "inexistente") == []

    (tmp_path / "b_file.csv.gz").write_bytes(b"")
    (tmp_path / "a_file.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "ignorar.txt").write_text("texto", encoding="utf-8")

    files = list_raw_csv_files(tmp_path)
    assert [f.name for f in files] == ["a_file.csv", "b_file.csv.gz"]


def test_run_bronze_ingestion_empty_dir(tmp_path: Path) -> None:
    """Verifica o comportamento quando o diretório raw está vazio."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "bronze" / "bronze.db"

    result = run_bronze_ingestion(raw_dir=raw_dir, db_path=db_path)
    assert result == {}
    assert not db_path.exists()


def test_run_bronze_ingestion_preserves_raw_strings_and_adds_audit_columns(
    tmp_path: Path,
) -> None:
    """Testa se a ingestão preserva os dados brutos sem tipagem e inclui _loaded_at."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "bronze" / "bronze.db"

    csv_file = raw_dir / "olist_orders_dataset.csv"
    csv_file.write_text(
        "order_id,order_status,price\n001,delivered,0199.90\n",
        encoding="utf-8",
    )

    gz_file = raw_dir / "olist_customers_dataset.csv.gz"
    with gzip.open(gz_file, "wt", encoding="utf-8") as f:
        f.write("customer_id,zip_code\ncust_1,01310000\n")

    hashes = run_bronze_ingestion(raw_dir=raw_dir, db_path=db_path)
    assert set(hashes.keys()) == {"olist_orders_dataset", "olist_customers_dataset"}
    assert db_path.exists()

    with duckdb.connect(str(db_path)) as con:
        row = con.execute(
            "SELECT order_id, order_status, price, _loaded_at, _file_sha256 "
            "FROM olist_orders_dataset"
        ).fetchone()
        assert row is not None
        assert row[0] == "001"
        assert row[1] == "delivered"
        assert row[2] == "0199.90"
        assert row[3] is not None
        assert row[4] == hashes["olist_orders_dataset"]

        cust_row = con.execute(
            "SELECT customer_id, zip_code FROM olist_customers_dataset"
        ).fetchone()
        assert cust_row == ("cust_1", "01310000")

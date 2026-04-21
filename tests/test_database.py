"""
tests/test_database.py
----------------------
Testes unitários para o módulo de banco de dados GuarAssist.

Executar com: pytest tests/test_database.py -v
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from pathlib import Path

# Adiciona o diretório backend ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importa as funções do módulo database
from database.database import (
    conectar, init_db, save_analysis, get_all_analyses,
    cadastrar_produtor, listar_produtores,
    cadastrar_talhao, listar_talhoes,
    cadastrar_planta, listar_plantas,
    processar_resultado_ia, resumo_talhao
)


@pytest.fixture
def temp_db():
    """Cria um banco de dados temporário para testes."""
    # Cria arquivo temporário
    fd, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Substitui o DB_PATH global temporariamente
    import database.database as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = Path(temp_path)

    # Inicializa o banco
    init_db()

    yield temp_path

    # Limpeza - força fechamento de conexões
    db_module.DB_PATH = original_path
    
    # Tenta fechar conexões ativas antes de deletar
    try:
        # Fecha qualquer conexão que possa estar aberta
        import sqlite3
        conn = sqlite3.connect(temp_path)
        conn.close()
        
        # Pequena pausa para garantir que o arquivo seja liberado
        import time
        time.sleep(0.1)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except (OSError, PermissionError):
        # Se não conseguir deletar, pelo menos restaura o path original
        pass


class TestDatabaseInit:
    """Testes para inicialização do banco."""

    def test_init_db_cria_tabelas(self, temp_db):
        """Verifica se init_db cria todas as tabelas necessárias."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Lista de tabelas esperadas
        expected_tables = [
            'produtores', 'talhoes', 'plantas', 'patologias',
            'verificacoes', 'deteccoes', 'alertas'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in expected_tables:
            assert table in tables, f"Tabela {table} não foi criada"

        conn.close()

    def test_init_db_insere_patologias(self, temp_db):
        """Verifica se init_db insere o catálogo de patologias."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patologias")
        count = cursor.fetchone()[0]

        # Deve ter pelo menos as patologias do catálogo
        assert count >= 5, f"Esperado pelo menos 5 patologias, encontrado {count}"

        # Verifica se antracnose foi inserida
        cursor.execute("SELECT nome FROM patologias WHERE nome = 'Antracnose'")
        assert cursor.fetchone() is not None, "Antracnose não encontrada"

        conn.close()


class TestSaveAnalysis:
    """Testes para save_analysis()."""

    def test_save_analysis_basico(self, temp_db):
        """Testa salvar uma análise básica."""
        data = {
            "timestamp": 1640995200,  # 2022-01-01 00:00:00
            "filename": "foto.jpg",
            "status": "saudavel",
            "disease": None,
            "confidence": 0.95
        }

        save_analysis(data)

        # Verifica se foi salvo
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verificacoes WHERE foto_path = ? AND realizada_por = 'IA'", (data["filename"],))
        row = cursor.fetchone()

        assert row is not None, "Análise não foi salva"
        assert row[4] == data["status"]  # resultado (correção: row[3] era realizada_por)
        assert row[6] == data["filename"]  # foto_path

        conn.close()

    def test_save_analysis_com_doenca(self, temp_db):
        """Testa salvar análise com doença detectada."""
        data = {
            "timestamp": 1641081600,
            "filename": "doente.jpg",
            "status": "praga_detectada",
            "disease": "Antracnose",
            "confidence": 0.87
        }

        save_analysis(data)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT observacoes FROM verificacoes WHERE foto_path = ? AND realizada_por = 'IA'", (data["filename"],))
        row = cursor.fetchone()

        assert row is not None, "Análise não foi encontrada"
        observacoes = row[0]

        assert "Antracnose" in observacoes
        assert "87.0%" in observacoes

        conn.close()


class TestGetAllAnalyses:
    """Testes para get_all_analyses()."""

    def test_get_all_analyses_vazio(self, temp_db):
        """Testa get_all_analyses quando não há análises."""
        result = get_all_analyses()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_all_analyses_com_dados(self, temp_db):
        """Testa get_all_analyses com dados existentes."""
        # Insere algumas análises diretamente
        analyses = [
            {
                "id": "test-1",
                "timestamp": 1640995200,
                "filename": "foto1.jpg",
                "status": "saudavel",
                "disease": None,
                "confidence": 0.95
            },
            {
                "id": "test-2",
                "timestamp": 1641081600,
                "filename": "foto2.jpg",
                "status": "praga_detectada",
                "disease": "Antracnose",
                "confidence": 0.87
            }
        ]

        for analysis in analyses:
            save_analysis(analysis)

        result = get_all_analyses()

        assert len(result) == 2
        # IDs são numéricos agora, ordenados por data_hora DESC
        assert result[0]["timestamp"] == analyses[1]["timestamp"]  # Mais recente primeiro
        assert result[1]["timestamp"] == analyses[0]["timestamp"]

        # Verifica campos
        assert "timestamp" in result[0]
        assert "filename" in result[0]
        assert "status" in result[0]
        assert "disease" in result[0]
        assert "confidence" in result[0]


class TestCRUDProdutores:
    """Testes para operações CRUD de produtores."""

    def test_cadastrar_produtor(self, temp_db):
        """Testa cadastro de produtor."""
        produtor_id = cadastrar_produtor(
            nome="João Silva",
            municipio="Maués - AM",
            contato="joao@email.com"
        )

        assert produtor_id is not None

        # Verifica se foi salvo
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtores WHERE id = ?", (produtor_id,))
        row = cursor.fetchone()

        assert row[1] == "João Silva"  # nome
        assert row[2] == "Maués - AM"  # municipio
        assert row[3] == "joao@email.com"  # contato

        conn.close()

    def test_listar_produtores(self, temp_db):
        """Testa listagem de produtores."""
        # Cadastra alguns produtores
        id1 = cadastrar_produtor("Produtor 1", "Maués")
        id2 = cadastrar_produtor("Produtor 2", "Itacoatiara")

        produtores = listar_produtores()

        assert len(produtores) == 2
        nomes = [p["nome"] for p in produtores]
        assert "Produtor 1" in nomes
        assert "Produtor 2" in nomes


class TestCRUDTalhoes:
    """Testes para operações CRUD de talhões."""

    def test_cadastrar_talhao(self, temp_db):
        """Testa cadastro de talhão."""
        # Primeiro cadastra um produtor
        produtor_id = cadastrar_produtor("João Silva")

        talhao_id = cadastrar_talhao(
            produtor_id=produtor_id,
            nome="Talhão A",
            area_hectares=5.5,
            clone="BRS Maués",
            data_plantio="2022-03-15",
            lat=-3.37,
            lon=-57.72
        )

        assert talhao_id is not None

        # Verifica se foi salvo
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM talhoes WHERE id = ?", (talhao_id,))
        row = cursor.fetchone()

        assert row[1] == produtor_id  # produtor_id
        assert row[2] == "Talhão A"   # nome
        assert row[3] == 5.5         # area_hectares
        assert row[4] == "BRS Maués" # clone

        conn.close()

    def test_listar_talhoes(self, temp_db):
        """Testa listagem de talhões por produtor."""
        produtor_id = cadastrar_produtor("João Silva")

        # Cadastra talhões
        id1 = cadastrar_talhao(produtor_id, "Talhão 1", 3.0)
        id2 = cadastrar_talhao(produtor_id, "Talhão 2", 4.5)

        talhoes = listar_talhoes(produtor_id)

        assert len(talhoes) == 2
        nomes = [t["nome"] for t in talhoes]
        assert "Talhão 1" in nomes
        assert "Talhão 2" in nomes


class TestCRUDPlantas:
    """Testes para operações CRUD de plantas."""

    def test_cadastrar_planta(self, temp_db):
        """Testa cadastro de planta."""
        # Cadastra produtor e talhão
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A")

        planta_id = cadastrar_planta(
            talhao_id=talhao_id,
            codigo="TA-001",
            fase="adulta",
            data_plantio="2022-03-15"
        )

        assert planta_id is not None

        # Verifica se foi salva
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plantas WHERE id = ?", (planta_id,))
        row = cursor.fetchone()

        assert row[1] == talhao_id  # talhao_id
        assert row[2] == "TA-001"  # codigo
        assert row[3] == "adulta"  # fase

        conn.close()

    def test_listar_plantas(self, temp_db):
        """Testa listagem de plantas por talhão."""
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A")

        # Cadastra plantas
        id1 = cadastrar_planta(talhao_id, "TA-001")
        id2 = cadastrar_planta(talhao_id, "TA-002")

        plantas = listar_plantas(talhao_id)

        assert len(plantas) == 2
        codigos = [p["codigo"] for p in plantas]
        assert "TA-001" in codigos
        assert "TA-002" in codigos


class TestProcessarResultadoIA:
    """Testes para processar_resultado_ia()."""

    def test_processar_resultado_ia_saudavel(self, temp_db):
        """Testa processamento de resultado IA para planta saudável."""
        # Setup: produtor -> talhão -> planta
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A")
        planta_id = cadastrar_planta(talhao_id, "TA-001")

        resultado_ia = {
            "patologias": []
        }

        verif_id = processar_resultado_ia(
            planta_id=planta_id,
            foto_path="fotos/TA-001.jpg",
            resultado_modelo=resultado_ia,
            condicao_tempo="ensolarado",
            talhao_id=talhao_id
        )

        assert verif_id is not None

        # Verifica se verificação foi criada
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verificacoes WHERE id = ?", (verif_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == planta_id  # planta_id
        assert row[4] == "saudavel"  # resultado (correção: era row[3])
        assert row[5] == "ensolarado"  # condicao_tempo

        conn.close()

    def test_processar_resultado_ia_com_patologia(self, temp_db):
        """Testa processamento de resultado IA com patologia detectada."""
        # Setup
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A")
        planta_id = cadastrar_planta(talhao_id, "TA-001")

        resultado_ia = {
            "patologias": [
                {"nome": "Antracnose", "confianca": 0.92, "severidade": "moderada"}
            ]
        }

        verif_id = processar_resultado_ia(
            planta_id=planta_id,
            foto_path="fotos/TA-001.jpg",
            resultado_modelo=resultado_ia,
            condicao_tempo="chuvoso",
            talhao_id=talhao_id
        )

        assert verif_id is not None

        # Verifica se detecção foi registrada
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, p.nome as patologia_nome
            FROM deteccoes d
            JOIN patologias p ON d.patologia_id = p.id
            WHERE d.verificacao_id = ?
        """, (verif_id,))

        deteccoes = cursor.fetchall()
        assert len(deteccoes) == 1

        det = deteccoes[0]
        assert det[3] == 0.92  # confianca_ia (correção: era det[6])
        assert det[4] == "moderada"  # severidade (correção: era det[7])
        assert det[8] == "Antracnose"  # patologia_nome

        conn.close()


class TestResumoTalhao:
    """Testes para resumo_talhao()."""

    def test_resumo_talhao_basico(self, temp_db):
        """Testa geração de resumo básico de talhão."""
        # Setup
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A", 5.0)

        # Cadastra algumas plantas
        p1 = cadastrar_planta(talhao_id, "TA-001", "adulta")
        p2 = cadastrar_planta(talhao_id, "TA-002", "adulta")

        resumo = resumo_talhao(talhao_id)

        assert "plantas_por_status" in resumo
        assert "alertas_ativos" in resumo
        assert "top_patologias" in resumo

        # Deve ter 2 plantas saudáveis
        assert resumo["plantas_por_status"]["saudavel"] == 2

    def test_resumo_talhao_com_doente(self, temp_db):
        """Testa resumo com planta doente."""
        # Setup
        produtor_id = cadastrar_produtor("João Silva")
        talhao_id = cadastrar_talhao(produtor_id, "Talhão A")
        planta_id = cadastrar_planta(talhao_id, "TA-001")

        # Simula detecção de doença
        resultado_ia = {
            "patologias": [
                {"nome": "Antracnose", "confianca": 0.95, "severidade": "severa"}
            ]
        }

        processar_resultado_ia(
            planta_id=planta_id,
            foto_path="fotos/TA-001.jpg",
            resultado_modelo=resultado_ia,
            condicao_tempo="chuvoso",
            talhao_id=talhao_id
        )

        resumo = resumo_talhao(talhao_id)

        # Deve aparecer na top_patologias
        assert len(resumo["top_patologias"]) > 0
        assert resumo["top_patologias"][0]["nome"] == "Antracnose"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
GuarAssist - Módulo de Banco de Dados SQLite
Cultura: Guaranazeiro (Paullinia cupana var. sorbilis)
Região: Amazônia Ocidental
=====================================================
Fontes de referência de pragas e doenças:
  - Embrapa Amazônia Ocidental (Pereira, 2005)
  - Embrapa: Poda fitossanitária no controle da antracnose (Araújo, 2007)
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "guarassist.db"


# ──────────────────────────────────────────────
# CONEXÃO
# ──────────────────────────────────────────────

def conectar():
    """Abre conexão com o banco e retorna (conn, cursor)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return conn, cursor



# CRIAÇÃO DAS TABELAS


SCHEMA = """
-- Produtores/usuários do sistema
CREATE TABLE IF NOT EXISTS produtores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    municipio       TEXT,
    contato         TEXT,
    data_cadastro   TEXT    DEFAULT (DATE('now'))
);

-- Talhões/áreas de guaraná de cada produtor
CREATE TABLE IF NOT EXISTS talhoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    produtor_id     INTEGER NOT NULL,
    nome            TEXT    NOT NULL,
    area_hectares   REAL,
    clone           TEXT,           -- ex: BRS Maués, BRS Amazonas, CMU 376
    data_plantio    TEXT,
    coordenadas     TEXT,           -- JSON: {"lat": -3.37, "lon": -60.01}
    FOREIGN KEY (produtor_id) REFERENCES produtores(id)
);

-- Plantas individuais monitoradas dentro de um talhão
CREATE TABLE IF NOT EXISTS plantas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id       INTEGER NOT NULL,
    codigo          TEXT,           -- identificação de campo (ex: T1-P003)
    fase            TEXT    DEFAULT 'adulta',
                                    -- muda | jovem | adulta | producao
    status          TEXT    DEFAULT 'saudavel',
                                    -- saudavel | suspeita | doente | tratamento | recuperada
    data_plantio    TEXT,
    observacoes     TEXT,
    FOREIGN KEY (talhao_id) REFERENCES talhoes(id)
);

-- Catálogo de pragas e doenças do guaranazeiro
CREATE TABLE IF NOT EXISTS patologias (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT    NOT NULL UNIQUE,
    nome_cientifico     TEXT,
    categoria           TEXT,   -- fungo | inseto | bacteria | fitoplasma | abiotico | erva_daninha
    nivel_risco         TEXT    DEFAULT 'medio',
                                -- baixo | medio | alto | critico
    sintomas            TEXT,   -- descrição dos sintomas visíveis
    parte_afetada       TEXT,   -- folhas | frutos | ramos | raizes | flores | caule
    epoca_critica       TEXT,   -- época do ano de maior incidência
    tratamento          TEXT,   -- tratamento recomendado
    produtos_indicados  TEXT,   -- fungicidas/inseticidas indicados
    fonte               TEXT    -- referência bibliográfica
);

-- Cada inspeção/verificação feita em uma planta
CREATE TABLE IF NOT EXISTS verificacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    planta_id       INTEGER NOT NULL,
    data_hora       TEXT    DEFAULT (DATETIME('now')),
    realizada_por   TEXT,           -- nome do técnico ou 'IA'
    resultado       TEXT    DEFAULT 'saudavel',
                                    -- saudavel | suspeita | patologia_detectada
    condicao_tempo  TEXT,           -- seco | chuvoso | nublado
    foto_path       TEXT,
    observacoes     TEXT,
    FOREIGN KEY (planta_id) REFERENCES plantas(id)
);

-- Patologias detectadas em cada verificação (pode ter mais de uma por verificação)
CREATE TABLE IF NOT EXISTS deteccoes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    verificacao_id      INTEGER NOT NULL,
    patologia_id        INTEGER NOT NULL,
    confianca_ia        REAL,       -- score do modelo: 0.0 a 1.0
    severidade          TEXT,       -- leve | moderada | severa | critica
    tratamento_aplicado TEXT,
    data_tratamento     TEXT,
    resolvido           INTEGER DEFAULT 0,  -- 0 = não | 1 = sim
    FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    FOREIGN KEY (patologia_id)   REFERENCES patologias(id)
);

-- Alertas gerados automaticamente pelo sistema
CREATE TABLE IF NOT EXISTS alertas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id       INTEGER NOT NULL,
    patologia_id    INTEGER,
    nivel           TEXT,       -- info | aviso | urgente | critico
    mensagem        TEXT,
    data_hora       TEXT DEFAULT (DATETIME('now')),
    resolvido       INTEGER DEFAULT 0,
    FOREIGN KEY (talhao_id)   REFERENCES talhoes(id),
    FOREIGN KEY (patologia_id) REFERENCES patologias(id)
);
"""

# Catálogo pré-populado com pragas e doenças reais do guaranazeiro
# Fontes: Embrapa Amazônia Ocidental, Pereira (2005), Araújo (2007)
PATOLOGIAS_GUARANA = [
    {
        "nome": "Antracnose",
        "nome_cientifico": "Colletotrichum guaranicola",
        "categoria": "fungo",
        "nivel_risco": "critico",
        "sintomas": "Lesões necróticas em folhas e hastes novas. Manchas escuras nos lançamentos. Principal causa de baixa produtividade no Amazonas.",
        "parte_afetada": "folhas, ramos, frutos",
        "epoca_critica": "Março a Junho (época chuvosa)",
        "tratamento": "Poda fitossanitária dos ramos afetados. Aplicação de fungicidas preventivos antes da época chuvosa. Uso de clones resistentes (BRS Maués).",
        "produtos_indicados": "Cercobin 700, Cercobin 500, Folicur 200",
        "fonte": "Araújo et al., Embrapa Pecuária Sudeste, 2007",
    },
    {
        "nome": "Superbrotamento",
        "nome_cientifico": "Fitoplasma (Mollicutes)",
        "categoria": "fitoplasma",
        "nivel_risco": "critico",
        "sintomas": "Multiplicação exagerada de células em brotos e inflorescências, formando massa densa. Flores com aspecto de cálice compacto. Pode reduzir 100% da produção.",
        "parte_afetada": "ramos, flores",
        "epoca_critica": "Fevereiro a Setembro (ano todo)",
        "tratamento": "Inspeções fitossanitárias a cada 30 dias. Poda dos ramos afetados 10 cm abaixo do superbrotamento. Sem controle químico viável.",
        "produtos_indicados": "Sem produto químico eficaz. Controle apenas por poda.",
        "fonte": "Batista & Bolkan, 1982; Pereira, Embrapa, 2005",
    },
    {
        "nome": "Tripes",
        "nome_cientifico": "Liothrips adisi",
        "categoria": "inseto",
        "nivel_risco": "alto",
        "sintomas": "Deformação e queda de folhas jovens. Secamento prematuro de flores. Danos nos frutos. Insetos negros (adultos) ou alaranjados (jovens) na face inferior das folhas.",
        "parte_afetada": "folhas, flores, frutos",
        "epoca_critica": "Início do período seco (floração e frutificação)",
        "tratamento": "Monitoramento constante. Inseticidas sistêmicos quando a população ultrapassar o nível de dano econômico.",
        "produtos_indicados": "Inseticidas sistêmicos registrados para a cultura",
        "fonte": "Garcia, 1998; Pereira, Embrapa Amazônia Ocidental, 2005",
    },
    {
        "nome": "Mancha angular",
        "nome_cientifico": "Xanthomonas campestris pv. paullinae",
        "categoria": "bacteria",
        "nivel_risco": "alto",
        "sintomas": "Lesões oleosas (anasarca) nos folíolos dos ramos baixeiros. Manchas irregulares com halo amarelo que evoluem para marrom-avermelhado. Pode causar morte em plantas jovens.",
        "parte_afetada": "folhas",
        "epoca_critica": "Todo o ano, maior severidade em plantas jovens",
        "tratamento": "Remoção e destruição das partes afetadas. Aplicação preventiva de fungicidas cúpricos.",
        "produtos_indicados": "Oxicloreto de cobre",
        "fonte": "Embrapa Amazônia Ocidental",
    },
    {
        "nome": "Oídio",
        "nome_cientifico": "Oidium anacardii",
        "categoria": "fungo",
        "nivel_risco": "medio",
        "sintomas": "Pó branco acinzentado sobre folhas e brotos novos. Redução do crescimento.",
        "parte_afetada": "folhas, ramos",
        "epoca_critica": "Período seco",
        "tratamento": "Aplicação de enxofre em pó ou fungicidas específicos para oídio.",
        "produtos_indicados": "Enxofre molhável, fungicidas IBE",
        "fonte": "Embrapa Amazônia Ocidental",
    },
    {
        "nome": "Crestamento abiótico",
        "nome_cientifico": None,
        "categoria": "abiotico",
        "nivel_risco": "medio",
        "sintomas": "Manchas marrom-claras simétricas nos folíolos evoluindo para cinza-palha. Causado por toxidez de ferro em solos encharcados.",
        "parte_afetada": "folhas",
        "epoca_critica": "Período chuvoso (solo encharcado)",
        "tratamento": "Melhorar drenagem do solo. Corrigir pH com calagem.",
        "produtos_indicados": "Calcário dolomítico para correção do pH",
        "fonte": "Pereira et al., Embrapa Soja, 2013",
    },
    {
        "nome": "Formiga cortadeira",
        "nome_cientifico": "Atta sexdens / Acromyrmex coronatus",
        "categoria": "inseto",
        "nivel_risco": "medio",
        "sintomas": "Desfolhamento rápido com corte limpo de folíolos e ramos novos. Trilhas e formigueiros próximos às plantas.",
        "parte_afetada": "folhas, ramos",
        "epoca_critica": "Todo o ano",
        "tratamento": "Isca granulada formicida no formigueiro. Monitoramento periódico.",
        "produtos_indicados": "Iscas formicidas à base de Sulfluramida ou Fipronil",
        "fonte": "De Nazaré & Figueiredo, Embrapa Amazônia Oriental, 1982",
    },
    {
        "nome": "Broca do caule",
        "nome_cientifico": "Aegerina vignea",
        "categoria": "inseto",
        "nivel_risco": "alto",
        "sintomas": "Galerias no interior do caule. Ramos murchos sem causa aparente. Serragem fina ao redor da base da planta.",
        "parte_afetada": "caule, ramos",
        "epoca_critica": "Todo o ano",
        "tratamento": "Remoção e queima dos ramos infestados. Inseticida sistêmico.",
        "produtos_indicados": "Inseticidas sistêmicos (imidacloprido)",
        "fonte": "De Nazaré & Figueiredo, Embrapa Amazônia Oriental, 1982",
    },
]


def criar_banco():
    """
    Cria o banco de dados e popula o catálogo de patologias.
    Chame esta função UMA VEZ ao iniciar o sistema.
    """
    conn, cursor = conectar()
    cursor.executescript(SCHEMA)

    for p in PATOLOGIAS_GUARANA:
        cursor.execute(
            """INSERT OR IGNORE INTO patologias
               (nome, nome_cientifico, categoria, nivel_risco, sintomas,
                parte_afetada, epoca_critica, tratamento, produtos_indicados, fonte)
               VALUES (:nome, :nome_cientifico, :categoria, :nivel_risco, :sintomas,
                       :parte_afetada, :epoca_critica, :tratamento, :produtos_indicados, :fonte)""",
            {**p, "fonte": p.get("fonte", ""), "nome_cientifico": p.get("nome_cientifico", "")},
        )

    conn.commit()
    conn.close()
    print(f"✅ Banco GuarAssist criado em: {DB_PATH}")
    print(f"   {len(PATOLOGIAS_GUARANA)} patologias do guaranazeiro carregadas.")


# ──────────────────────────────────────────────
# PRODUTORES
# ──────────────────────────────────────────────

def cadastrar_produtor(nome, municipio=None, contato=None):
    conn, cursor = conectar()
    cursor.execute(
        "INSERT INTO produtores (nome, municipio, contato) VALUES (?, ?, ?)",
        (nome, municipio, contato),
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def listar_produtores():
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM produtores ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# TALHÕES
# ──────────────────────────────────────────────

def cadastrar_talhao(produtor_id, nome, area_hectares=None, clone=None,
                     data_plantio=None, lat=None, lon=None):
    coordenadas = json.dumps({"lat": lat, "lon": lon}) if lat and lon else None
    conn, cursor = conectar()
    cursor.execute(
        """INSERT INTO talhoes (produtor_id, nome, area_hectares, clone, data_plantio, coordenadas)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (produtor_id, nome, area_hectares, clone, data_plantio, coordenadas),
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def listar_talhoes(produtor_id):
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM talhoes WHERE produtor_id = ?", (produtor_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# PLANTAS
# ──────────────────────────────────────────────

def cadastrar_planta(talhao_id, codigo=None, fase="adulta", data_plantio=None):
    conn, cursor = conectar()
    cursor.execute(
        "INSERT INTO plantas (talhao_id, codigo, fase, data_plantio) VALUES (?, ?, ?, ?)",
        (talhao_id, codigo, fase, data_plantio),
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_status_planta(planta_id, novo_status):
    """Status: saudavel | suspeita | doente | tratamento | recuperada"""
    conn, cursor = conectar()
    cursor.execute("UPDATE plantas SET status = ? WHERE id = ?", (novo_status, planta_id))
    conn.commit()
    conn.close()


def listar_plantas(talhao_id):
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM plantas WHERE talhao_id = ? ORDER BY codigo", (talhao_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_plantas_doentes(talhao_id):
    conn, cursor = conectar()
    cursor.execute(
        "SELECT * FROM plantas WHERE talhao_id = ? AND status != 'saudavel'",
        (talhao_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# PATOLOGIAS (catálogo)
# ──────────────────────────────────────────────

def listar_patologias(categoria=None, nivel_risco=None):
    conn, cursor = conectar()
    query = "SELECT * FROM patologias WHERE 1=1"
    params = []
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if nivel_risco:
        query += " AND nivel_risco = ?"
        params.append(nivel_risco)
    query += " ORDER BY nivel_risco DESC, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_patologia(nome_ou_id):
    conn, cursor = conectar()
    if isinstance(nome_ou_id, int):
        cursor.execute("SELECT * FROM patologias WHERE id = ?", (nome_ou_id,))
    else:
        cursor.execute("SELECT * FROM patologias WHERE nome LIKE ?", (f"%{nome_ou_id}%",))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ──────────────────────────────────────────────
# VERIFICAÇÕES
# ──────────────────────────────────────────────

def registrar_verificacao(planta_id, resultado, realizada_por="IA",
                           condicao_tempo=None, foto_path=None, observacoes=None):
    """
    Registra uma inspeção numa planta.
    resultado: 'saudavel' | 'suspeita' | 'patologia_detectada'
    Retorna o ID da verificação criada.
    """
    conn, cursor = conectar()
    cursor.execute(
        """INSERT INTO verificacoes
               (planta_id, resultado, realizada_por, condicao_tempo, foto_path, observacoes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (planta_id, resultado, realizada_por, condicao_tempo, foto_path, observacoes),
    )
    verif_id = cursor.lastrowid

    if resultado == "patologia_detectada":
        cursor.execute("UPDATE plantas SET status = 'doente' WHERE id = ?", (planta_id,))
    elif resultado == "saudavel":
        cursor.execute(
            "UPDATE plantas SET status = 'saudavel' WHERE id = ? AND status != 'tratamento'",
            (planta_id,),
        )

    conn.commit()
    conn.close()
    return verif_id


def registrar_deteccao(verificacao_id, patologia_id, confianca_ia=None,
                        severidade="moderada", tratamento_aplicado=None):
    conn, cursor = conectar()
    cursor.execute(
        """INSERT INTO deteccoes
               (verificacao_id, patologia_id, confianca_ia, severidade, tratamento_aplicado)
           VALUES (?, ?, ?, ?, ?)""",
        (verificacao_id, patologia_id, confianca_ia, severidade, tratamento_aplicado),
    )
    conn.commit()
    conn.close()


def marcar_tratado(deteccao_id, data_tratamento=None):
    """Marca uma detecção como resolvida após o tratamento."""
    from datetime import date
    data = data_tratamento or date.today().isoformat()
    conn, cursor = conectar()
    cursor.execute(
        "UPDATE deteccoes SET resolvido = 1, data_tratamento = ? WHERE id = ?",
        (data, deteccao_id),
    )
    conn.commit()
    conn.close()


def historico_planta(planta_id, limite=30):
    conn, cursor = conectar()
    cursor.execute(
        """
        SELECT
            v.id            AS verificacao_id,
            v.data_hora,
            v.resultado,
            v.realizada_por,
            v.condicao_tempo,
            v.foto_path,
            v.observacoes,
            p.nome          AS patologia,
            p.nivel_risco,
            p.categoria,
            d.confianca_ia,
            d.severidade,
            d.tratamento_aplicado,
            d.resolvido
        FROM verificacoes v
        LEFT JOIN deteccoes  d ON d.verificacao_id = v.id
        LEFT JOIN patologias p ON p.id = d.patologia_id
        WHERE v.planta_id = ?
        ORDER BY v.data_hora DESC
        LIMIT ?
        """,
        (planta_id, limite),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# ALERTAS
# ──────────────────────────────────────────────

def criar_alerta(talhao_id, mensagem, nivel="aviso", patologia_id=None):
    conn, cursor = conectar()
    cursor.execute(
        "INSERT INTO alertas (talhao_id, patologia_id, nivel, mensagem) VALUES (?, ?, ?, ?)",
        (talhao_id, patologia_id, nivel, mensagem),
    )
    conn.commit()
    conn.close()


def listar_alertas_ativos(talhao_id=None):
    conn, cursor = conectar()
    if talhao_id:
        cursor.execute(
            """SELECT a.*, p.nome AS patologia_nome
               FROM alertas a LEFT JOIN patologias p ON p.id = a.patologia_id
               WHERE a.talhao_id = ? AND a.resolvido = 0
               ORDER BY a.data_hora DESC""",
            (talhao_id,),
        )
    else:
        cursor.execute(
            """SELECT a.*, p.nome AS patologia_nome
               FROM alertas a LEFT JOIN patologias p ON p.id = a.patologia_id
               WHERE a.resolvido = 0
               ORDER BY a.data_hora DESC"""
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolver_alerta(alerta_id):
    conn, cursor = conectar()
    cursor.execute("UPDATE alertas SET resolvido = 1 WHERE id = ?", (alerta_id,))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# RELATÓRIOS / DASHBOARD (retornam dicts prontos para JSON → React)
# ──────────────────────────────────────────────

def resumo_talhao(talhao_id):
    """
    Resumo geral do talhão — alimenta o dashboard React.
    """
    conn, cursor = conectar()

    cursor.execute(
        "SELECT status, COUNT(*) AS total FROM plantas WHERE talhao_id = ? GROUP BY status",
        (talhao_id,),
    )
    por_status = {r["status"]: r["total"] for r in cursor.fetchall()}

    cursor.execute(
        """SELECT p.nome, p.nivel_risco, COUNT(*) AS ocorrencias
           FROM deteccoes d
           JOIN patologias  p  ON p.id  = d.patologia_id
           JOIN verificacoes v ON v.id  = d.verificacao_id
           JOIN plantas      pl ON pl.id = v.planta_id
           WHERE pl.talhao_id = ?
           GROUP BY p.id
           ORDER BY ocorrencias DESC
           LIMIT 5""",
        (talhao_id,),
    )
    top_patologias = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM alertas WHERE talhao_id = ? AND resolvido = 0",
        (talhao_id,),
    )
    alertas_ativos = cursor.fetchone()["total"]

    conn.close()
    return {
        "plantas_por_status": por_status,
        "top_patologias": top_patologias,
        "alertas_ativos": alertas_ativos,
    }


def relatorio_deteccoes_ia(talhao_id, apenas_nao_resolvidas=False):
    """Lista todas as detecções de IA num talhão para a tabela do dashboard."""
    conn, cursor = conectar()
    query = """
        SELECT
            v.data_hora,
            pl.codigo          AS planta,
            p.nome             AS patologia,
            p.nivel_risco,
            p.categoria,
            d.confianca_ia,
            d.severidade,
            d.tratamento_aplicado,
            d.resolvido,
            v.foto_path
        FROM deteccoes d
        JOIN verificacoes v  ON v.id  = d.verificacao_id
        JOIN plantas      pl ON pl.id = v.planta_id
        JOIN patologias   p  ON p.id  = d.patologia_id
        WHERE pl.talhao_id = ?
    """
    params = [talhao_id]
    if apenas_nao_resolvidas:
        query += " AND d.resolvido = 0"
    query += " ORDER BY v.data_hora DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# INTEGRAÇÃO COM IA
# ──────────────────────────────────────────────

def processar_resultado_ia(planta_id, foto_path, resultado_modelo,
                            condicao_tempo=None, talhao_id=None):
    """
    Função principal de integração com o modelo de visão computacional.

    Parâmetros:
        planta_id       : ID da planta monitorada
        foto_path       : caminho ou URL da imagem analisada
        resultado_modelo: dict retornado pelo modelo de IA
                          Formato esperado:
                          {
                            "patologias": [
                              {"nome": "Antracnose", "confianca": 0.94, "severidade": "severa"},
                              {"nome": "Tripes",     "confianca": 0.71, "severidade": "leve"}
                            ]
                          }
        condicao_tempo  : 'seco' | 'chuvoso' | 'nublado'
        talhao_id       : necessário para gerar alertas automáticos

    Retorna o ID da verificação criada.
    """
    patologias_detectadas = resultado_modelo.get("patologias", [])
    resultado = "patologia_detectada" if patologias_detectadas else "saudavel"

    verif_id = registrar_verificacao(
        planta_id=planta_id,
        resultado=resultado,
        realizada_por="IA",
        condicao_tempo=condicao_tempo,
        foto_path=foto_path,
    )

    for det in patologias_detectadas:
        patologia = buscar_patologia(det["nome"])
        if not patologia:
            continue  # patologia não catalogada — adicione ao catálogo se necessário

        registrar_deteccao(
            verificacao_id=verif_id,
            patologia_id=patologia["id"],
            confianca_ia=det.get("confianca"),
            severidade=det.get("severidade", "moderada"),
            tratamento_aplicado=patologia.get("tratamento"),
        )

        # Alerta automático para riscos altos ou críticos
        if talhao_id and patologia["nivel_risco"] in ("alto", "critico"):
            nivel_alerta = "critico" if patologia["nivel_risco"] == "critico" else "urgente"
            criar_alerta(
                talhao_id=talhao_id,
                patologia_id=patologia["id"],
                nivel=nivel_alerta,
                mensagem=(
                    f"{patologia['nome']} detectada com "
                    f"{det.get('confianca', 0)*100:.0f}% de confiança. "
                    f"Tratamento: {patologia['tratamento']}"
                ),
            )

    return verif_id


# ──────────────────────────────────────────────
# FUNÇÕES DE COMPATIBILIDADE (Legacy - para API)
# ──────────────────────────────────────────────

def init_db():
    """Inicializa o banco de dados com o schema completo."""
    try:
        conn, cursor = conectar()
        cursor.executescript(SCHEMA)
        
        # Insere catálogo de patologias se tabela estiver vazia
        cursor.execute("SELECT COUNT(*) FROM patologias")
        if cursor.fetchone()[0] == 0:
            for patologia in PATOLOGIAS_GUARANA:
                cursor.execute("""
                    INSERT INTO patologias 
                    (nome, nome_cientifico, categoria, nivel_risco, sintomas, 
                     parte_afetada, epoca_critica, tratamento, produtos_indicados, fonte)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patologia["nome"],
                    patologia.get("nome_cientifico"),
                    patologia["categoria"],
                    patologia.get("nivel_risco", "medio"),
                    patologia.get("sintomas"),
                    patologia.get("parte_afetada"),
                    patologia.get("epoca_critica"),
                    patologia.get("tratamento"),
                    patologia.get("produtos_indicados"),
                    patologia.get("fonte"),
                ))
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        raise

def save_analysis(data: dict, planta_id=None):
    """
    Salva uma análise realizada pela IA.
    Compatível com a estrutura esperada pela API.
    
    Args:
        data: dicionário com { id, timestamp, filename, status, disease, confidence }
        planta_id: ID da planta analisada (opcional, para compatibilidade)
    """
    try:
        conn, cursor = conectar()
        
        # Se não foi fornecido planta_id, tenta encontrar ou criar uma planta genérica
        if planta_id is None:
            # Busca uma planta existente
            cursor.execute("SELECT id FROM plantas LIMIT 1")
            row = cursor.fetchone()
            if row:
                planta_id = row[0]
            else:
                # Cria um produtor e talhão genérico se necessário
                cursor.execute("SELECT id FROM produtores LIMIT 1")
                prod_row = cursor.fetchone()
                if not prod_row:
                    cursor.execute("""
                        INSERT INTO produtores (nome, municipio)
                        VALUES ('Sistema GuarAssist', 'Genérico')
                    """)
                    prod_id = cursor.lastrowid
                else:
                    prod_id = prod_row[0]
                
                # Cria talhão genérico
                cursor.execute("""
                    INSERT INTO talhoes (produtor_id, nome, area_hectares)
                    VALUES (?, 'Talhão Genérico', 1.0)
                """, (prod_id,))
                talhao_id = cursor.lastrowid
                
                # Cria planta genérica
                cursor.execute("""
                    INSERT INTO plantas (talhao_id, codigo, fase, status)
                    VALUES (?, 'GENERICA', 'adulta', 'saudavel')
                """, (talhao_id,))
                planta_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO verificacoes 
            (planta_id, data_hora, realizada_por, resultado, condicao_tempo, foto_path, observacoes)
            VALUES (?, datetime(?, 'unixepoch'), 'IA', ?, 'nublado', ?, ?)
        """, (
            planta_id,
            data.get("timestamp"),
            data.get("status", "saudavel"),
            data.get("filename"),
            f"Doença detectada: {data.get('disease')} (confiança: {data.get('confidence', 0)*100:.1f}%)"
            if data.get("disease") else f"Análise IA: {data.get('status', 'saudavel')}"
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao salvar análise: {e}")
        raise

def get_all_analyses():
    """
    Retorna todas as análises realizadas, ordenadas por timestamp decrescente.
    Compatível com o esperado pela rota de histórico.
    """
    try:
        conn, cursor = conectar()
        cursor.execute("""
            SELECT 
                v.id,
                CAST((julianday(v.data_hora) - julianday('1970-01-01')) * 86400 AS INTEGER) as timestamp,
                v.foto_path as filename,
                v.resultado as status,
                v.observacoes,
                CASE 
                    WHEN v.observacoes LIKE 'Doença detectada: %' 
                    THEN TRIM(SUBSTR(v.observacoes, 18, INSTR(v.observacoes, ' (confiança:') - 18))
                    ELSE NULL 
                END as disease,
                CASE 
                    WHEN v.observacoes LIKE '%(confiança: %)%' 
                    THEN CAST(TRIM(SUBSTR(v.observacoes, INSTR(v.observacoes, '(confiança: ') + 11, 
                        INSTR(v.observacoes, '%)') - INSTR(v.observacoes, '(confiança: ') - 11)) AS REAL) / 100
                    ELSE 0.0 
                END as confidence
            FROM verificacoes v
            WHERE v.realizada_por = 'IA'
            ORDER BY v.data_hora DESC 
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "timestamp": row[1],
                "filename": row[2],
                "status": row[3],
                "disease": row[5],
                "confidence": row[6] or 0.0,
            })
        return result
    except Exception as e:
        print(f"❌ Erro ao recuperar análises: {e}")
        return []


# ──────────────────────────────────────────────
# EXEMPLO DE USO
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Cria o banco e carrega o catálogo de patologias do guaraná
    criar_banco()

    # 2. Cadastra um produtor
    produtor_id = cadastrar_produtor(
        nome="Cooperativa GuarAssist",
        municipio="Maués - AM",
        contato="guarassist@email.com",
    )

    # 3. Cadastra um talhão de guaraná
    talhao_id = cadastrar_talhao(
        produtor_id=produtor_id,
        nome="Talhão A - Clone BRS Maués",
        area_hectares=2.5,
        clone="BRS Maués",
        data_plantio="2022-03-15",
        lat=-3.37,
        lon=-57.72,
    )

    # 4. Cadastra plantas no talhão
    p1 = cadastrar_planta(talhao_id, codigo="TA-001", fase="adulta")
    p2 = cadastrar_planta(talhao_id, codigo="TA-002", fase="adulta")

    # 5. Simula resultado retornado pelo modelo de IA após analisar uma foto
    resultado_ia = {
        "patologias": [
            {"nome": "Antracnose", "confianca": 0.97, "severidade": "severa"},
        ]
    }

    verif_id = processar_resultado_ia(
        planta_id=p1,
        foto_path="fotos/TA-001_20260421.jpg",
        resultado_modelo=resultado_ia,
        condicao_tempo="chuvoso",
        talhao_id=talhao_id,
    )
    print(f"\n📸 Verificação registrada: ID {verif_id}")

    # 6. Dados para o dashboard React
    resumo = resumo_talhao(talhao_id)
    print(f"\n📊 Resumo do talhão:")
    print(f"   Plantas por status : {resumo['plantas_por_status']}")
    print(f"   Alertas ativos     : {resumo['alertas_ativos']}")
    print(f"   Top patologias     : {[p['nome'] for p in resumo['top_patologias']]}")

    # 7. Histórico da planta TA-001
    print(f"\n📋 Histórico da planta TA-001:")
    for r in historico_planta(p1):
        conf = f"{r['confianca_ia']*100:.0f}%" if r["confianca_ia"] else "n/a"
        print(f"   [{r['data_hora']}] {r['resultado']} | {r['patologia']} ({conf})")

    # 8. Alertas gerados automaticamente
    print(f"\n🚨 Alertas ativos:")
    for a in listar_alertas_ativos(talhao_id):
        print(f"   [{a['nivel'].upper()}] {a['mensagem'][:80]}...")

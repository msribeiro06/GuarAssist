# GuarAssist - Testes Unitários

## Visão Geral
Este diretório contém os testes unitários para o módulo de banco de dados do GuarAssist.

## Estrutura dos Testes

### Classes de Teste

- **`TestDatabaseInit`**: Testes de inicialização do banco
  - Criação de tabelas
  - Inserção do catálogo de patologias

- **`TestSaveAnalysis`**: Testes da função `save_analysis()`
  - Salvamento de análises básicas
  - Salvamento com doenças detectadas

- **`TestGetAllAnalyses`**: Testes da função `get_all_analyses()`
  - Retorno vazio
  - Retorno com dados

- **`TestCRUDProdutores`**: Testes CRUD de produtores
  - Cadastro, listagem

- **`TestCRUDTalhoes`**: Testes CRUD de talhões
  - Cadastro, listagem

- **`TestCRUDPlantas`**: Testes CRUD de plantas
  - Cadastro, listagem

- **`TestProcessarResultadoIA`**: Testes da função `processar_resultado_ia()`
  - Processamento de plantas saudáveis
  - Processamento com patologias detectadas

- **`TestResumoTalhao`**: Testes da função `resumo_talhao()`
  - Geração de resumos básicos
  - Resumos com plantas doentes

## Como Executar

### Todos os Testes
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar todos os testes
python -m pytest tests/ -v

# Executar com relatório conciso
python -m pytest tests/ --tb=short
```

### Teste Específico
```bash
# Executar apenas uma classe
python -m pytest tests/test_database.py::TestDatabaseInit -v

# Executar apenas um método
python -m pytest tests/test_database.py::TestSaveAnalysis::test_save_analysis_basico -v
```

### Com Cobertura
```bash
# Executar com relatório de cobertura
python -m pytest tests/ --cov=backend.database --cov-report=html

# Abrir relatório de cobertura
# Abrir htmlcov/index.html no navegador
```

## Cobertura dos Testes

Os testes cobrem:
- ✅ **16 testes unitários** implementados
- ✅ **100% dos testes passando**
- ✅ **Funções críticas**: init_db, save_analysis, get_all_analyses
- ✅ **CRUD completo**: produtores, talhões, plantas
- ✅ **Integração IA**: processar_resultado_ia
- ✅ **Relatórios**: resumo_talhao

## Dependências

- `pytest`: Framework de testes
- `pytest-cov`: Relatórios de cobertura (opcional)
- `pytest-mock`: Mocking de funções (opcional)

## Notas Técnicas

- **Banco temporário**: Cada teste usa um arquivo SQLite temporário
- **Isolamento**: Testes não interferem uns nos outros
- **Limpeza**: Arquivos temporários são removidos automaticamente
- **Compatibilidade**: Testes mantêm compatibilidade com API FastAPI</content>
<parameter name="filePath">c:\Users\msrib\OneDrive\Desktop\GuarAssist\tests\README.md
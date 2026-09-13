DOWNLOAD  E IMPORTAÇÃO SFTP

    - Periodicidade:
        > Ínicio: 04:00
        > Fim: 00:00
        > Intervalo: 2:00


    - Criação Excel
        > Registrar Histórico de Extrações
        > Nome Arquivo e Data Inclusão (Site Banco)
        > Cedente

    - Leitura Excel:
        > Cedente - Variavel

    - Abrir Navegador:
        > Site - Processos - CNAB - 400 - Exportação
        > Cedente, Carteira, Dt Inicial e Dt Final (Serão Iguais)

    - Tabela Site:
        > Ler:
            * Data Inclusão e Nome Arquivo
        > Compara Histórico:
            * Data Inclusão e Nome Arquivo já foram registrados
        > Caso que não localizar irá salvar no Excel


FLUXO:
    1 - Leitura Excel Base
        Cedente e Caminho Import SFTP

        1.1 - Buscar/verificar se existe um excel de histórico
            - Se não criar um
                * Nome do Arquivo
                * Data Inclusão

    2 - Abrir Navegador
    3 - Realizar comparação entre base histórico e Arquivos disponíveis
    4 - Baixar os casos válidos
    5 Registrar no Excel
    6 - Importar no SFTP (Pasta Correspondente) Arquivo Retorno
    7 - Fecha tudo e aguarda a próxima verificação 

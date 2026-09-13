OBJETIVO:
    Este robo tem como objetivo realizar o caminho inverso do primeiro robo, onde agora o foco aqui é o site do Banco.
    Neste fluxo o script vai acessar o site, na parte de extração e irá verificar se há novos arquivos para serem extraídos e importados dentro do SFTP da parceiro de acordo com o cedente e irá registrar todos eles num arquvo excel de histórico para cada um dos cedentes.

    Após o download, o robô extrai os arquivos compactados (Zip), faz o upload (importação) deles para as pastas específicas no SFTP (AWS S3) e atualiza uma base em Excel para manter o histórico e o rastreamento das operações de cada cedente.


FLUXO:
    Main:
        Temos praticamente a mesma lógica de comando e por horário do robo de extração, entretanto aqui o período é maior, pois o site gera novos arquivos além dos já importados.

    Funções:
        lerArquivo(nome): 
            Busca as credenciais de acesso (email, senha) e os caminhos onde a base está e caminho de Download em um arquivo .txt parametrizado (procurando no OneDrive ou Desktop local)

        carregar_base():
            Carrega o excel base, usado para ter as informações básicas de cada cedente, bem como os próprios caminhos para buscar os arquivos no SFTP e para onde irá manda-los

        tarefa_diaria:
            A maior diferença está aqui, onde o script já partirá para o se conectar ao site do Banco, seguindo a mesma lógica de 3 tentativas.
            Processa a base excel que usará como base para ter as informações necessárias e criar ou apenas ler, a base de cedente que serviá como histórico de registros.
            Chama a função de importação e, ao finalizar todos os cedentes, encerra o navegador.



    roboImportSFTP:
        Este módulo é resposnável por logar no site e ir até a pagína de Extração do site, para verificar se há novos arquivos a serem baixados, quando os arquivos são baixados ele vem no formato de zip então ocorre a extração antes da importação dentro do SFTP

    Funções:
        login_Banco:
            Efetua o lgin e segue a mesma premissa de 3 tentativas para se logar na página, caso haja falha ele reinicia o navegador.

        importaCNAB_Banco:
            Altera dinamicamente a pasta de download do navegador Chrome (`Page.setDownloadBehavior`) para a pasta específica do cedente atual.
            Acessa a tela de exportação CNAB 400, preenche os filtros (Cedente, Carteira e Data de Hoje).
            Lê a tabela dos arquivos e compara os arquivos disponíveis com os arquivos já registrados na planilha Excel do cedente. Apenas os arquivos não processados anteriormente são selecionados e baixados.
            Após o download, aciona a extração do Zip e o upload para o SFTP. Se houver sucesso no SFTP, atualiza a planilha com as datas de envio e exclui os arquivos `.RET` locais para manter a pasta limpa.


    Functions:
        aguarda_Download:
            Aguarda os arquivos serem baixados por completo antes de prosseguir com o restante do processo.

        extract_zip:
            Função responsável por fazer a extração dos arquivos retornos baixados do site, antes de subirem para o SFTP

        import_arquivos_SFTP:
            Aqui é onde o script vai conectar com o SFTP para pegar todos os arquivos que foram extraídos e importar dentro da pasta especificada no excel base.
            Monta uma lista de comandos para o WinSCP via terminal (subprocess.run), divide a URL de destino entre *Bucket* e *Subpasta*, faz o upload dos arquivos extraídos (put) e retorna os status de sucesso ou erro.

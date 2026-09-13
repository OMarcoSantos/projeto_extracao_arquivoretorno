import os
import time
import shutil
import zipfile
import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

import roboArqRetorno
import functions

# URL do sistema
link = "https://banco.banco.valor.com.br/"

# Define o Fuso Horário de Brasilia
fuso_br = ZoneInfo('America/Sao_Paulo')



# Função para ler configurações
def lerArquivo(nome):
    try:
        caminho_area_trabalho_OneDrive = os.path.join(os.path.expanduser("~"), "OneDrive", "Área de Trabalho", f"{nome}.txt")
        caminho_area_trabalho = os.path.join(os.path.expanduser("~"), "Desktop", f"{nome}.txt")

        if os.path.exists(caminho_area_trabalho_OneDrive):
            with open(caminho_area_trabalho_OneDrive, 'r', encoding='utf-8') as file:
                linhas = file.readlines()
        elif os.path.exists(caminho_area_trabalho):
            with open(caminho_area_trabalho, 'r', encoding='utf-8') as file:
                linhas = file.readlines()
        else:
            raise FileNotFoundError("Arquivo de configuração não encontrado.")

        email = linhas[1].strip()
        senhaBanco = linhas[2].strip()
        caminho_Download = linhas[3].strip()
        baseExcel = linhas[4].strip()

        return email, senhaBanco, caminho_Download, baseExcel

    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo de configuração: {e}")
        return None, None, None, None

# Carregamento inicial
def carregar_base():
    global dfBase, tempBaseExcel, email, senhaBanco, caminho_Download, baseExcel

    email, senhaBanco, caminho_Download, baseExcel = lerArquivo('Marco')
    dfBase = pd.read_excel(baseExcel, sheet_name='Planilha1')

    dfBase.columns = dfBase.columns.str.strip()
    print('[DEBUG] Colunas da base:', dfBase.columns.tolist())


    for col in ['Carteira', 'Cedente', 'Caminho Rede', 'Caminho Extracao SFTP', 'Caminho Importacao SFTP', 'Caminho Arq Retorno SFTP']:
        dfBase[col] = dfBase[col].astype(str).str.strip()


# Função principal da tarefa
def tarefa_diaria():
    try:
        carregar_base()
        print('[INFO] Iniciando processamento por Cedente...')

        for i, row in dfBase.iterrows():

            zip_paths = []

            cedente = row['Cedente']
            carteira = row['Carteira']
            caminho_destino = row['Caminho Rede']
            caminho_SFTP = row['Caminho Extracao SFTP']
            caminhoImport_SFTP = row['Caminho Importacao SFTP']
            caminho_Aqr_Retorno_SFTP = row['Caminho Arq Retorno SFTP']

        
            print(f'\n[INFO] Processando Cedente: {cedente} | Carteira: {carteira}')

            # Cria a pasta da carteira: 
            pasta_carteira = os.path.join(caminho_Download, f'{cedente}_{carteira}')
            os.makedirs(pasta_carteira, exist_ok=True)

            # Listar Arquivos no SFTP
            arquivos_disponiveis = roboArqRetorno.lista_Arquivos(caminho_SFTP)
            if not arquivos_disponiveis:
                print(f'[INFO] Nenhum arquivo encontrado para o cedente: {cedente}')
                continue

            # Cria ou Carrega o Excel do Cedente: 
            excel_cedente = os.path.join(pasta_carteira, f'{cedente}_{carteira}.xlsx')
            if os.path.exists(excel_cedente):
                dfCedente = pd.read_excel(excel_cedente)
            else:
                dfCedente = pd.DataFrame(columns=['Nome_Arq', 'Dt_Hora', 'Nome_Sequencial' , 'Dt_Sequencial', 'Status_Importacao'])
            
            if 'Status_Importacao' not in dfCedente.columns:
                dfCedente['Status_Importacao'] = ''

            arquivos_existentes = dfCedente['Nome_Arq'].dropna().astype(str).tolist()
            novos_arquivos = [a for a in arquivos_disponiveis if a ['Arquivo'] not in arquivos_existentes]

            if not novos_arquivos:
                print(f'[INFO] Nenhum novo arquivo para o cedente: {cedente}')
                continue

            # Baixar e processar arquivos
            arquivos_tratados = roboArqRetorno.extracao_CNAB_SFTP(novos_arquivos, pasta_carteira, caminho_SFTP, caminhoImport_SFTP)

            novas_linhas = []

            for nome in arquivos_tratados:
                caminho_CNAB = os.path.join(pasta_carteira, nome)
                novo_nome, prox_sequencial = functions.sequencial(caminho_destino)
                novo_caminho = functions.rename_txt(caminho_CNAB, prox_sequencial)

                zip_name = os.path.splitext(os.path.basename(novo_caminho))[0] + '.zip'
                zip_path = os.path.join(pasta_carteira, zip_name)

                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    zipf.write(novo_caminho, arcname=os.path.basename(novo_caminho))

                shutil.copy(zip_path, os.path.join(caminho_destino, os.path.basename(zip_path)))
                zip_paths.append(zip_path)

                novas_linhas.append({
                    'Nome_Arq': nome,
                    'Dt_Hora': next((a['data_modificacao'] for a in novos_arquivos if a['Arquivo'] == nome), ''),
                    'Nome_Sequencial': os.path.basename(novo_caminho),
                    'Dt_Sequencial': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Status_Importacao': 'Pendente'
                })

            dfCedente = pd.concat([dfCedente, pd.DataFrame(novas_linhas)], ignore_index=True)
            dfCedente.to_excel(excel_cedente, index=False)
            print(f'[INFO] Cedente {cedente} finalizado com sucesso.')

            driver = None

            if zip_paths:
                #driver = functions.browser(zip_paths[0])
                driver = functions.browser(zip_paths)
                roboArqRetorno.ImportaCNAB(driver, email, senhaBanco, link, dfCedente, zip_paths, excel_cedente, cedente)
                
                #Atualiza a coluna Status Importação
                dfCedente.loc[dfCedente['Status_Importacao'] == 'Pendente', 'Status_Importacao'] = 'Arquivo Importado'
                dfCedente.to_excel(excel_cedente, index=False) # Salva Novamente a Base do Excel com status atualizado

                roboArqRetorno.mover_arquivos_SFTP(arquivos_tratados, caminho_SFTP, caminhoImport_SFTP)

            if driver:
                driver.quit()

    except Exception as e:
        print(f'[ERRO] Falha na tarefa agendada: {e}')



# Execução - Teste e Produção:

# MODO_TESTE - True - Deixa o Script configurado para o Modo Teste
# MODO_TESTE - False - Retira o Script do Modo Teste - Produção
MODO_TESTE = False

if __name__ == "__main__":
    if MODO_TESTE:
        print('[MODO TESTE] - Iniciando Testes')
        tarefa_diaria()
        print('[MODO TESTE] - Teste Encerrado.')

    else:
        # Agendamento Contínuo (Modo Produção)
        print('[INFO] Inicinado Checagem....')
        #calendario = BlockingScheduler()
        # Inicializa o agendador com o fuso horário correto
        calendario = BlockingScheduler(timezone=fuso_br)

        # Agendamento Cron: Executa das 04 às 12 no intervalo de 2h
        calendario.add_job(
            tarefa_diaria, 
            'cron',
            hour='4-12/2', # Horas: 4, 6, 8, 10, 12
            minute=0, # Minuto: 0 (Extamente na hora cheia)
            #next_run_time=datetime.now(), # Quando colocar pra rodar o script, irá rodar por completo e depois entrará no modo de espera 
            misfire_grace_time=3600, # Tolerância para atrasos da VM
        )

    
        print(f'[INFO] Iniciado em: {datetime.now(fuso_br)}')

        try:
            tarefa_diaria()
            calendario.start()
        except (KeyboardInterrupt, SystemExit):
            print('[INFO] Agendamento Encerrado')



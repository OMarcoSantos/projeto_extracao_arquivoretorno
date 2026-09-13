import os
import time
import shutil
import zipfile
import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

import roboImportSFTP
import functions

# URL
link = "https://funcao.Banco.Valor.com.br/"

# Define o Fuso Horário de Brasilia usando o módulo nativo
fuso_br = ZoneInfo('America/Sao_Paulo')

driver = None
# numCedente = "" # Variável de teste


# Função para ler configurações
def lerArquivo(nome):
    try:
        caminho_area_trabalho_OneDrive = os.path.join(os.path.expanduser("~"), "OneDrive - Marco", "Área de Trabalho", f"{nome}.txt")
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
        pasta_Download = linhas[3].strip()
        baseExcel = linhas[4].strip()

        return email, senhaBanco, pasta_Download, baseExcel

    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo de configuração: {e}")
        return None, None, None, None


# Carregamento inicial
def carregar_base():
    global dfBase, tempBaseExcel, email, senhaBanco, pasta_Download, baseExcel


    email, senhaBanco, pasta_Download, baseExcel = lerArquivo('Marco')

    # Inicializa a planilha Base com as Info de Cedente, Cedente, Caminhos SFTP's etc
    dfBase = pd.read_excel(baseExcel, sheet_name='Planilha1')

    dfBase.columns = dfBase.columns.str.strip()
    #print('[DEBUG] Colunas da base:', dfBase.columns.tolist())

    for col in ['Carteira', 'Cedente', 'Caminho Rede', 'Caminho Extracao SFTP', 'Caminho Importacao SFTP', 'Caminho Arq Retorno SFTP']:
        dfBase[col] = dfBase[col].astype(str).str.strip()


# Função principal da tarefa
def tarefa_diaria():

    driver = None

    try:
        carregar_base()
        print('[INFO] Iniciando processamento por Cedente...')

        driver = roboImportSFTP.login_Banco(email, senhaBanco, link, pasta_Download)

        if not driver:
            print("[ERRO] Não foi possível logar no Banco.")
            return


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
            pasta_carteira = os.path.join(pasta_Download, f'{cedente}_{carteira}')
            os.makedirs(pasta_carteira, exist_ok=True)
            

            # Cria ou Carrega o Excel do Cedente: 
            excel_cedente = os.path.join(pasta_carteira, f'Base_Importacao_{cedente}_{carteira}.xlsx')
            #print(f"[VALOR] Excel Cedente - {excel_cedente}")

            if os.path.exists(excel_cedente):
                dfCedente = pd.read_excel(excel_cedente)
                print(f"Cedente Já Existe - {dfCedente}")
            else:
                dfCedente = pd.DataFrame(columns=['Nome_CNAB_Banco', 'Dt_Hora_Banco', 'Dt_Hora_SFTP', 'Status_Importacao'])
                print(f"Cedente Não Existe... Criando")
            
            if 'Status_Importacao' not in dfCedente.columns:
                dfCedente['Status_Importacao'] = ''

            # Baixar e Processar Arquivos
            roboImportSFTP.importaCNAB_Banco(driver, email, senhaBanco, link, dfCedente, excel_cedente, cedente, pasta_carteira, caminho_Aqr_Retorno_SFTP)

    except Exception as e:
        print(f'[ERRO] Falha na tarefa agendada: {e}')
    finally:
        # Fecha o navegador apenas quando o loop de todos os cedente terminar
        if driver:
            driver.quit()
            print("[INFO] Todos os Cedentes foram processados!!!")


# Execução - Teste e Produção:

# MODO_TESTE - True - Deixa o Script configurado para o Modo Teste (Rodar na hora)
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
        calendario = BlockingScheduler(timezone=fuso_br)
        

        # Agendamento Cron: Executa das 03 às 21 no intervalo de 2h
        calendario.add_job(
            tarefa_diaria, 
            'cron',
            hour='3-21/2', # Horas: 3, 5, 7, 9, 11
            minute=0, # Minuto: 0 (Extamente na hora cheia)
            #next_run_time=datetime.now(fuso_br), # Quando colocar pra rodar o script, irá rodar por completo e depois entrará no modo de espera 
            misfire_grace_time=3600, # Tolerância para atrasos da VM
        )


        print(f'[INFO] Iniciado em: {datetime.now(fuso_br)}')

        try:
            # Tenta iniciar o agendador
            tarefa_diaria()
            calendario.start()
        except (KeyboardInterrupt, SystemExit):
            print('[INFO] Agendamento interrompido manualmente ou pelo sistema.')
        except Exception as e:
            # Isso vai nos mostrar se o erro é de permissão, timezone ou outro
            print(f'[ERRO CRÍTICO] O agendador falhou ao iniciar: {e}')



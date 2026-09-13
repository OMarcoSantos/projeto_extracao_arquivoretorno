from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, time as dt_time
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import subprocess
import functions
import glob
import xpath
import time
import Class
import os

hoje = datetime.now().strftime("%d/%m/%Y")


def login_Banco(email, senhaBanco, link, pasta_Download):
    # Abre Navegador e realiza o login com 3 tentativas:
    driver = None
    maxTentativas = 3
    tentativas = 0
    sucesso = False 


    while tentativas < maxTentativas and not sucesso:
        try:
            tentativas += 1
            print(f'Tentava {tentativas} para acessar Banco...')
            if driver:
                driver.quit()

            driver = functions.browser(pasta_Download)
            variaveisRerun = Class.Rerun(driver, email, senhaBanco, link)

            driver.execute_script("window.open('about:blank','_blank');")
            driver.switch_to.window(driver.window_handles[0])

            # Acessa Tela Inicial do Banco
            functions.tryLoading(variaveisRerun)
            functions.tryGetLink(link, variaveisRerun)

            # Tentar Localizar a Página Inicial
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, xpath.lblEmailBanco)))
            
            # Loga no Banco
            functions.tryLogin(email, senhaBanco, xpath.lblEmailBanco, xpath.lblSenhaBanco, xpath.btnEntrar, variaveisRerun)
            functions.tryLoading(variaveisRerun)

            # Marca como sucesso se conseguiu acessar o Banco
            sucesso = True
            return driver

        except Exception as e:
            print(f"[ERRO] Falha na Tentativa {tentativas}: {e}")
            if driver:
                driver.quit()
                time.sleep(2)

    return None


def importaCNAB_Banco(driver, email, senhaBanco, link, dfCedente, excel_cedente, cedente, pasta_carteira, caminho_Aqr_Retorno_SFTP):
    
    variaveisRerun = Class.Rerun(driver, email, senhaBanco, link, dfCedente)

    # Altera o caminho do Download para a pasta da carteira respectiva
    driver.execute_cdp_cmd("Page.setDownloadBehavior",{
    "behavior": "allow",
    "downloadPath": pasta_carteira
    })

    try:
        # Alterar de Página:
        link = "https://funcao.Banco.Valor.com.br//processos/cnab/400/exportacao"
        functions.tryGetLink(link, variaveisRerun)
        functions.tryLoading(variaveisRerun)


        # Tela Exportação
        # Seleção - Cedente
        functions.tryClick(xpath.campo_cedente, variaveisRerun)
        functions.trySendInfo(xpath.cedente, cedente, variaveisRerun)
        functions.tryLoading(variaveisRerun)
        functions.tryClick(xpath.select_cedente, variaveisRerun)
        functions.tryLoading(variaveisRerun)

        # Seleção - Carteira
        functions.tryClick(xpath.campo_carteira, variaveisRerun)
        functions.tryClick(xpath.select_Carteira, variaveisRerun)
        functions.tryLoading(variaveisRerun)

        # Inserindo a Data:
        functions.tryClick(xpath.dataInicial, variaveisRerun)
        functions.trySendInfoData(xpath.dataInicial, hoje, variaveisRerun)

        # Tabela Banco:
        tabela = driver.find_element(By.ID, "grid")
        #Aguardar as linhas carregarem
        functions.tryLoading(variaveisRerun)
        linhas = tabela.find_elements(By.TAG_NAME, "tr")
    
        #print(f"Total de Linhas Com Cabeçalho: {len(linhas)}")

        arquivo_registrados = set(dfCedente['Nome_CNAB_Banco'].astype(str))
        arquivos_selecionados = 0

        for i, linha in enumerate(linhas[1:], start=2):
            colunas = linha.find_elements(By.TAG_NAME, "td")
            nome_arq_Banco = colunas[3].text
            data_arq_Banco = colunas[2].text

            if nome_arq_Banco not in arquivo_registrados:
                print('Novo Arquivo Identificado... Baixando!!!')


                checkBox = linha.find_element(By.CSS_SELECTOR, 'td:nth-child(1) input[type="checkbox"]')
                driver.execute_script("arguments[0].click();", checkBox)

                arquivos_selecionados += 1

                # Registra Temporariamente no DataFrame
                banco_dict = {
                    "Nome_CNAB_Banco": [nome_arq_Banco],
                    "Dt_Hora_Banco": [data_arq_Banco],
                    "Status_Importacao": ["Selecionado"],
                }

                df_nova_linha = pd.DataFrame(banco_dict)
                dfCedente = pd.concat([dfCedente, df_nova_linha], ignore_index=True)
                dfCedente.to_excel(excel_cedente, index=False)

        if arquivos_selecionados > 0:
            functions.tryClick(xpath.btnDownload, variaveisRerun)
            functions.aguarda_Download(pasta_carteira)
            time.sleep(3)
            # EXTRAI E EXCLUI OS ARQUIVOS
            functions.extract_zip(pasta_carteira)
        else:
            print(f"[INFO] Nenhum Arquivo Novo para o Cedente: {cedente}... Indo para o próximo.")
            return

        status_import_SFTP = functions.import_arquivos_SFTP(pasta_carteira, caminho_Aqr_Retorno_SFTP)

        if status_import_SFTP:
            print("[INFO] Importação SFTP Concluída. Iniciando Registro e Limpeza")

            arquivos_ret = glob.glob(os.path.join(pasta_carteira, "*.RET"))

            for ret_path in arquivos_ret:
                nome_arq = os.path.basename(ret_path)

                # Pega a data de modificação do arquivo SFTP para o histórico
                timestamp = os.path.getatime(ret_path)
                dt_sftp = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')

                # Procura a a linha que já existe e atualiza apenas as colunas de SFTP e Status
                if nome_arq in dfCedente['Nome_CNAB_Banco'].values:
                    # Atualiza a linha onde o nome do arquivo coincide
                    dfCedente.loc[dfCedente['Nome_CNAB_Banco'] == nome_arq, 'Dt_Hora_SFTP'] = dt_sftp
                    dfCedente.loc[dfCedente['Nome_CNAB_Banco'] == nome_arq, 'Status_Importacao'] = 'Arquivo Importado SFTP'

                else:
                    # Caso não encontre o arquivo, cria uma linha para ele (segurança)
                    nova_linha = {
                        'Nome_CNAB_Banco': nome_arq,
                        'Dt_Hora_SFTP': dt_sftp,
                        'Status_Importacao': 'Arquivo Importado SFTP',
                    }
                
                    dfCedente = pd.concat([dfCedente, pd.DataFrame([nova_linha])], ignore_index=True)

                # Exclui o arquivo .RET da pasta local
                try:
                    os.remove(ret_path)
                    print(f"[LIMPEZA] Arquivo {nome_arq} removido da pasta")
                except Exception as e:
                    print(f"[AVISO] Erro ao remover {nome_arq}: {e}")
            
            # Atualiza o Dataframe e Salva o Excel final do cedente
            dfCedente.to_excel(excel_cedente, index=False)
            print(f"[SUCESSO] Histórico Atualizado para o Cedente - {cedente}")

        else:
            print("[ERRO] Falha na importação SFTP. Os arquivos foram mantidos para conferência")

    except Exception as e:
        print(f"[ERRO] Falha ao processar cedente {cedente}: {e}")

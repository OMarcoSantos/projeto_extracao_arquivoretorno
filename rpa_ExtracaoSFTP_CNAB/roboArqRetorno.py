from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pandas as pd
import subprocess
import functions
import xpath
import time
import Class
import os

def cria_pasta(caminho_Download):
    download_Temp = 'Temporária'
    caminho_pasta = os.path.expanduser(fr'{caminho_Download}')
    pasta_Temp = os.path.join(caminho_pasta, download_Temp)
    os.makedirs(pasta_Temp, exist_ok=True)

    return download_Temp, caminho_pasta, pasta_Temp


def lista_Arquivos(caminho_SFTP):
    try:
        comandoListar = [
            'C:\\Program Files (x86)\\WinSCP\\WinSCP.com', '/ini=nul', '/command',
            f'open s3://XXXXXXXXXXXXXXXXXXXXXXX/{caminho_SFTP}', # Acesso AWS
            f'cd /{caminho_SFTP}',
            'ls',
            'exit'
        ]

        process = subprocess.Popen(comandoListar, stdout= subprocess.PIPE, stderr= subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f'[ERRO] Código de Saída: {process.returncode}')
            return []

        # Mostra a saída completa do comando ls
        stdout_decodificado = stdout.decode()
        # print("[DEBUG] Saída bruta do WinSCP:") # Descomentar se precisar testar - Mostra info do SFTP
        # print(stdout_decodificado)

        arquivos = []

        for linha in stdout_decodificado.splitlines():
            print(f"[DEBUG] Linha analisada: {linha}")

            partes = list(filter(None, linha.strip().split(' ')))
            #print(f"[DEBUG] Partes extraídas: {partes}") # Utilizar em modo de teste, se necessário

            if len(partes) >= 8 and partes[-1].endswith('.REM'):

                mes_str = partes[-5]
                dia = partes[-4]
                hora = partes[-3]
                ano = partes[-2]
                nome_arquivo = partes[-1]

                # print(f"[DEBUG] Partes extraídas: {partes}") # Utilizar em modo de teste, se necessário

                meses = {
                    'Jan': '01', 'Fev': '02', 'Mar': '03', 'Abr': '04', 'Mai': '05', 'Jun': '06', 'Jul': '07',
                    'Ago': '08', 'Set':'09', 'Out': '10', 'Nov': '11', 'Dez': '12'
                }
                mes = meses.get(mes_str, '01')
                data_mod = f"{dia.zfill(2)}/{mes}/{ano} {hora}"
                arquivos.append({'Arquivo': nome_arquivo.strip(), 'data_modificacao': data_mod})
            else: 
                continue

        #print(f"[DEBUG] Arquivos listados no SFTP: {arquivos}")

        return arquivos

    except Exception as e:
        print(f'[Erro] Falha ao listar arquivos SFTP: {e}')
        return []



def extracao_CNAB_SFTP(arquivos, pasta_carteira, caminho_SFTP, caminhoImport_SFTP, deletar_rem=True):
    try:
        if not arquivos:
            print(f'[INFO] Nenhum arquivo para baixar.')
            return []

        print('[INFO] Iniciando download dos arquivos do SFTP....')

        pasta_carteira = os.path.abspath(pasta_carteira).replace("\\", "/")

        comandoDownload = (
            '"C:\\Program Files (x86)\\WinSCP\\WinSCP.com" /ini=nul /command '
            f'"open s3:/XXXXXXXXXXXXXXXXXXXXXXX/{caminho_SFTP}" '
            f'"cd /{caminho_SFTP}" '
            f'"lcd ""{pasta_carteira}""" '
            '"get *.REM" '
            '"exit"'
            )

        download_process = subprocess.run(comandoDownload, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Descomentar para Testes
        # print("STDOUT (Download): ") 
        # print(download_process.stdout.decode('latin1'))
        # print("STDERR (Download): ")
        # print(download_process.stderr.decode('latin1'))

        arquivos_processados = []

        for arquivo in arquivos:
            nome_antigo = arquivo['Arquivo']
            caminho_antigo = os.path.join(pasta_carteira, nome_antigo)

            if os.path.exists(caminho_antigo):
                arquivos_processados.append(nome_antigo)
            else:
                print(f'[AVISO] Arquivo não encontrado após o Download: {caminho_antigo}')


        # Mover Arquivos para a Pasta de Processados:
        for arquivo in arquivos_processados:
            caminho_local = os.path.join(pasta_carteira, arquivo).replace("\\", "/")
            #print(f"Teste Arquivos --> {arquivo}")
            #print(f"Teste Caminho Local --> {caminho_local}")

            pasta_local = os.path.dirname(caminho_local)
            #print(f"Teste Pasta Local --> {pasta_local}")

            arquivo_nome = os.path.basename(caminho_local)
            #print(f"Teste Arquivo Nome --> {arquivo_nome}")
            #print(f"O arquivo será importado em: {caminhoImport_SFTP}")

            comandoUpload = (
                '"C:\\Program Files (x86)\\WinSCP\\WinSCP.com" /ini=nul /command '
                f'"open s3://XXXXXXXXXXXXXXXXXXXXXXX/{caminho_SFTP}" '
                f'"lcd \"{pasta_local}\"" '
                f'"cd /{caminhoImport_SFTP}" '
                f'"put \"{arquivo_nome}\"" '
                '"exit"'
            )

            resultado = subprocess.run(comandoUpload, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Descomentar para Testes
            #print("[DEBUG] Comando de upload:", comandoUpload)
            #print("[STDOUT Upload]:", resultado.stdout.decode('latin1', errors='ignore'))
            #print("[STDERR Upload]:", resultado.stderr.decode('latin1', errors='ignore'))


        return arquivos_processados

    except Exception as err:
        print(f"[ERRO] Ocorreu um erro durante o processamento: {err}")
        return []



def ImportaCNAB(driver, email, senhaBanco, link, dfCedente, zip_paths, excel_cedente, numCedente):

    variaveisRerun = Class.Rerun(driver, email, senhaBanco, link, dfCedente)

    try:

        maxTentativas = 3
        tentativa = 0
        sucesso = False

        while tentativa < maxTentativas and not sucesso:
            try:
                tentativa += 1
                print(f'[INFO] Tentativa {tentativa} de acesso ao Banco...')

                if driver:
                    driver.quit()

                # driver = functions.browser(zip_paths[0]) # Inicializa o driver a cada tentativa
                driver = functions.browser(zip_paths) # Inicializa o driver a cada tentativa
                variaveisRerun.driver = driver

                driver.execute_script("window.open('about:blank','_blank');")
                driver.switch_to.window(driver.window_handles[0])


                #Acessa Tela Inicial do 
                functions.tryLoading(variaveisRerun)
                functions.tryGetLink(link, variaveisRerun)
                #print(f'Tela Inicial')

                # Tentar Localizar a Página Inicial
                WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, xpath.lblEmailBanco)))
                
                # Loga no Banco
                functions.tryLogin(email, senhaBanco, xpath.lblEmailBanco, xpath.lblSenhaBanco, xpath.btnEntrar, variaveisRerun)
                functions.tryLoading(variaveisRerun)

                # Marca como sucesso se conseguiu acessar
                sucesso = True
            
            except TimeoutException:
                print('[ERRO] Elemento da tela inicial não encontrado... Reiniciando o Navegador')
                driver.quit()
                # driver = functions.browser(zip_paths[0])
                driver = functions.browser(zip_paths)
                time.sleep(5)
            
            except Exception as e:
                print(f'[Erro] Falha Inesperada na tentaiva {tentativa}.... {e}')
                driver.quit()
                # driver = functions.browser(zip_paths[0])
                driver = functions.browser(zip_paths)
                time.sleep(5)

        if not sucesso:
            print(f'[ERRO] Não foi possível acessar a página do Banco após {maxTentativas} tentativas')
            return

        # Tela de Importação CNAB
        link = "https://https://banco.banco.valor.com.br/processos/cnab/400/importacao"
        functions.tryGetLink(link, variaveisRerun)
        functions.tryLoading(variaveisRerun)



        # Preenchomento - AGÊNCIA:
        functions.tryClick(xpath.campoAgencia, variaveisRerun)
        functions.tryLoading(variaveisRerun)
        functions.tryClick(xpath.selecaoAgencia, variaveisRerun)
        functions.tryLoading(variaveisRerun)

        # Inserindo - Número Cedente
        cedente = str(numCedente)
        functions.trySendInfo(xpath.campoCedente, cedente, variaveisRerun)
        functions.tryLoading(variaveisRerun)
        functions.tryClick(xpath.clickCedente, variaveisRerun)
        functions.tryLoading(variaveisRerun)


        # Selecionando - Carteira:
        carteira = ''
        functions.TrySendMultipleInfosData(xpath.campoCarteira, carteira,"","",variaveisRerun)
        #functions.tryLoading(variaveisRerun)

        # Upload dos Arquivos
        for zip_file in zip_paths:
            nome_zip = os.path.basename(zip_file)
            nome_txt = nome_zip.replace('.zip', '.REM')

            try:
                # Espera o input aparecer no DOM
                upload_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.file-input")))
                upload_input.send_keys(zip_file)

                # Importar Arquivo ZIP
                functions.tryClick(xpath.btnUpArquivo, variaveisRerun)
                functions.tryLoading(variaveisRerun)
                time.sleep(5)

                # Limpa a tela para inserir novos arquivo
                functions.tryClick(xpath.btnCleanArquivos, variaveisRerun)
                functions.tryLoading(variaveisRerun)

                print(f"[INFO] Upload iniciado para o arquivo: {zip_file}")
                dfCedente.loc[dfCedente['Nome_Arq'] == nome_txt, 'Status_Importacao'] = 'Importado com Sucesso'

            except Exception as upload_err:
                print(f'[ERRO] Falaha ao importar {zip_file}: {upload_err}')
                nome_zip = os.path.basename(zip_file)
                nome_txt = nome_zip.replace('.zip', '.REM')
                dfCedente.loc[dfCedente['Nome_Arq'] == nome_txt, 'Status_Importacao'] = 'Erro na Importação'

        #Salva o Excel do cendente com status atualizado
        dfCedente.to_excel(excel_cedente, index=False)
        print(f'[INFO] Status de Importação atualizado no Excel: {excel_cedente}')
        time.sleep(0.5)

        # Fechar Navegador após Importação
        driver.quit()

    except Exception as err:
        print(f'[ERRO] Falha Geral na Importação: {err}')

        print('Acessou o Banco Homolog')
        print(f'[CAMINHO DO UPLOAD]: {zip_paths}')
        time.sleep(5)


    except Exception as err:
        print(f'Erro ao acessar Banco: {err}')


# MOVER OS ARQUIVOS PARA OUTRA PASTA DO SFTP
# Ver para integrar as duas
def mover_arquivos_SFTP(arquivos_processados, caminho_SFTP, caminhoImport_SFTP):

    try:
        if not arquivos_processados:
            print('[INFO] Nenhum arquivo para mover.')
            return

        print(f'[INFO] Iniciando movimentação de arquivos para a pasta: {caminho_SFTP}')


        # Caminho para iniciar o executavél do WinSCP
        winscp_exe = r'"C:\Program Files (x86)\WinSCP\WinSCP.exe"'
        
        # Criando conexão com o SFTP
        comando_base = f'{winscp_exe} /ini=nul /command "open s3://XXXXXXXXXXXXXXXXXXXXXXX{caminho_SFTP}"' 

        # Configurando a move (mv) para mover os arquivos de uma pasta para outra
        comandos_mv = []
        for nome in arquivos_processados:
            origem = f"/{caminho_SFTP}/{nome}".replace("//", "/")
            destino = f"/{caminhoImport_SFTP}/{nome}".replace("//", "/")

            comandos_mv.append(f'"mv ""{origem}"" ""{destino}"""')
        
        # Junta todas as configuraçõe feita acima em uma única string de comando
        comando_final = f"{comando_base} {' '.join(comandos_mv)} \"exit\""

        # Executando o comando por meio do shell=True (Resolvendo conflitos com o Windows)
        processo = subprocess.run(comando_final, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if processo.returncode == 0:
            print(f"[SUCESSO] Arquivos Movidos no SFTP")
        else:
            erro_msg = processo.stderr.decode('latin1')
            print(f"[ERRO] O WinSCP retornou um erro: {erro_msg}")

    except Exception as e:
        print(f"[ERRO] Falha ao executar o WinSCP: {e}")






from selenium import webdriver
import zipfile
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import subprocess
import time
import re
import glob
import os
import roboImportSFTP


def browser(pasta_Download): 

    #Configurações do Chorme
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": pasta_Download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    options.add_argument("--disable-features=PasswordAlert,ChromePasswordProtection")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--force-device-scale-factor=1")
    #options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-ipv6") # Possível correção da tela Branca
    options.add_argument("--disable-gpu") # Tentar corrigir os carregamentos muito longos

    options.page_load_strategy = 'eager' # Impedir que o site carregue informações que eu não preciso.

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """
    })
    #driver.maximize_window()
    driver.implicitly_wait(5)
    return driver



def rerun(variaveisRerun):
    variaveisRerun.driver.quit()
    roboImportSFTP.importaCNAB_Banco(variaveisRerun.email, variaveisRerun.senhaBanco, variaveisRerun.checkpoint, variaveisRerun.link)


def tryGetLink(link, variaveisRerun):
    try:
        variaveisRerun.driver.get(link)
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def tryLogin(email, senhaBanco, lblEmailBanco, lblSenhaBanco, btnEntrar, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, lblEmailBanco))
        ).send_keys(email)

        WebDriverWait(variaveisRerun.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, lblSenhaBanco))
        ).send_keys(senhaBanco)

        WebDriverWait(variaveisRerun.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, btnEntrar))
        ).click()
        
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def tryFilterInfo(xpath, info, variaveisRerun):
    try:
        tryClick(xpath, variaveisRerun)
        time.sleep(1)
        TrySendMultipleInfos(xpath, Keys.CONTROL, 'a', Keys.BACKSPACE, variaveisRerun)
        time.sleep(1)
        trySendInfo(xpath, info, variaveisRerun)
        tryLoading(variaveisRerun)  
        trySendInfo(xpath, Keys.ENTER, variaveisRerun)
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def tryCatchText(xpath, variaveisRerun):
    try:
        texto = WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).text 
        return texto
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def tryClick(xpath, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def trySendInfo(xpath, info, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(info)
        time.sleep(1)
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def trySendInfoData (xpath, info, variaveisRerun):
    try:
        elemento = WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath)))
        elemento = variaveisRerun.driver.find_element(By.XPATH, xpath)
        elemento.clear()
        # Adicional:
        elemento.send_keys(info)
        elemento.send_keys(Keys.RETURN)
    except Exception as err:
        print(err)
        rerun(variaveisRerun)
          

def TrySendMultipleInfos(xpath, info1, info2, info3, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(info1, info2, info3)
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def TrySendMultipleInfosData_(xpath, info1, info2, info3, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(info1, info2, info3)
    except Exception as err:
        print(f"Erro ao digitar no elemento: {xpath} \n {err}")
        rerun(variaveisRerun)



def TrySendMultipleInfosData(xpath, info1, info2, info3, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(info1, info2, info3, Keys.ENTER)
    except Exception as err:
        print(f"Erro ao digitar no elemento: {xpath} \n {err}")
        rerun(variaveisRerun)



def tryLoading(variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, 'loading-backdrop')))
        WebDriverWait(variaveisRerun.driver, 1000).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loading-backdrop')))
    except:
        pass


def tryLogout (xpath1, xpath2, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath1))).click()
        WebDriverWait(variaveisRerun.driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath2))).click()
    except Exception as err:
        print(err)
        rerun(variaveisRerun)


def waitingElemento (seletor, variaveisRerun):
    try:
        WebDriverWait(variaveisRerun.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, seletor)))
        WebDriverWait(variaveisRerun.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
    except Exception as err:
        print(f"Erro ao esperar pelo elemento clicavel, '{seletor}': {err}")
        rerun(variaveisRerun)


def tryCalcDate():
    try:
        hoje = datetime.today() 
        #hoje = datetime(2025,4, 1) # Quando precisar pegar o mês anterior, colocar a ultima data do mês + 1
        print(f'Retorno data de hoje: {hoje}')
        data = hoje
        
        if data.weekday() == 0:
            data -= timedelta(days=3)
        else:
            data -= timedelta(days=1)
            
        data = data.strftime("%d")
        data = int(data)
    except Exception as err:
        print(f"Erro ao calcular data.\n {err}")
    return data


def aguarda_Download(pasta_destino, timeout=60):
    
    timer = 0
    print("Iniciando Downaload")

    while timer < timeout:
        arquivos = os.listdir(pasta_destino)

        check_download = any(f.endswith('.zip') for f in arquivos)
        time.sleep(3)

        if not check_download:
            print("Download Concluído com Sucesso!!")
            print(f"Está na pasta {pasta_destino}")
            return True

        time.sleep(1)
        timer +=1
    
    print("Erro: O Download demorou demais ou não iniciou.")
    print(f"Está na pasta {pasta_destino}")

    return False



def extract_zip(pasta_carteira):
    arquivos_zip = glob.glob(os.path.join(pasta_carteira, "*.zip")) # Busca todos os arquivos com extensão ZIP

    if not arquivos_zip:
        print(f"[AVISO] Nenhum Arquivo ZIP encontrado para extrair em: {pasta_carteira}")
        return False
    
    print(f"[INFO] Encontrados {len(arquivos_zip)} arquivos ZIP para extração")

    for zip_path in arquivos_zip:
        nome_arquivo = os.path.basename(zip_path)
        try:
            print(f"[INFO] Extraindo: {nome_arquivo}....")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(pasta_carteira)
            
            os.remove(zip_path)
            print(f"[SUCESSO] {nome_arquivo} extraído e removido")

        except Exception as e:
            print(f"[ERRO] Falha ao processar {nome_arquivo}: {e}")
            continue

    return True



def import_arquivos_SFTP(pasta_carteira, caminho_Aqr_Retorno_SFTP):
    arquivo_retorno = glob.glob(os.path.join(pasta_carteira, "*.RET"))

    if not arquivo_retorno:
        print(f"[AVISO] Nenhum Retorno Localizado na Pasta: {pasta_carteira}")
        return False
    
    print(f"[INFO] Iniciando upload de {len(arquivo_retorno)} arquivo(s) para o SFTP...")

    try:
        # Usando WinSCP.com:
        winscp_path = r'"C:\Program Files (x86)\WinSCP\WinSCP.com"'

        # 2 Credenciais
        user = ""
        passw = ""
        host = ""

        # TRATAMENTO DO CAMINHO:
        # Remove barras extras e separa o Bucket do restante do caminho
        caminho_limpo = caminho_Aqr_Retorno_SFTP.strip("/")
        partes = caminho_limpo.split("/", 1)
        bucket = partes[0]
        subpasta = partes[1] if len(partes) > 1 else ""


        # O SEGREDO: Usar aspas duplas literais para envolver os caminhos internos
        # Usamos f'""comando""' para que o Windows entenda que as aspas fazem parte do argumento
        comandos = [
            f'open s3://{user}:{passw}@{host}/{bucket}/',
            f'lcd ""{pasta_carteira}""' # Aspas duplas duplas para proteger o espaço
        ]


        # 2. ENTRA NA SUBPASTA (se houver)
        if subpasta:
            comandos.append(f'cd ""{subpasta}""')

        # 3. UPLOAD DOS ARQUIVOS
        for ret_path in arquivo_retorno:
            nome_arquivo = os.path.basename(ret_path)
            comandos.append(f'put ""{nome_arquivo}""')

        comandos.append('"exit"')

        # 4. Monta a string de comandos separada por espaços, 
        # envolvendo cada comando em aspas duplas para o parâmetro /command
        string_comandos = " ".join([f'"{c}"' for c in comandos])

        # 5. Monta o comando final
        comando_final = f'{winscp_path} /ini=nul /command {string_comandos}'
        #print(f"[DEBUG] Comando Final Corrigido: {comando_final}")

        # Executa
        processo = subprocess.run(comando_final, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if processo.returncode == 0:
            print(f"[SUCESSO] {len(arquivo_retorno)} arquivo(s) importado(s) com sucesso.")
            return True
        else:
            # Com WinSCP.com, o erro costuma vir no stdout também
            erro_msg = processo.stderr.decode('latin1', errors='ignore')
            if not erro_msg:
                erro_msg = processo.stdout.decode('latin1', errors='ignore')
                print(f"[ERRO] WinSCP: {erro_msg}")
                return False

    except Exception as e:
        print(f"[ERRO] Falha: {e}")
        return False
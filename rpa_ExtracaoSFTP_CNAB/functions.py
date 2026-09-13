from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re
import os
from datetime import datetime, timedelta
import roboArqRetorno


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
    roboArqRetorno.download_Arq_Retorno(variaveisRerun.email, variaveisRerun.senhaBanco, variaveisRerun.checkpoint, variaveisRerun.link)


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



def sequencial(caminho):
    try:
        print(f'\n[INFO] Iniciando verificação de sequencial na pasta: {caminho}')
        lista_arquivos = os.listdir(caminho)
        nome_padrao = re.compile(r'^CB\d{4}(\d+)\.zip$', re.IGNORECASE)
        maior_num = 0

        for arquivo in lista_arquivos:
            correspondencia = nome_padrao.match(arquivo)
            if correspondencia:
                sequencial = int(correspondencia.group(1))
                if sequencial > maior_num:
                    maior_num = sequencial

        proximo_sequencial = maior_num + 1
        print(f'[INFO] Maior sequencial encontrado: {maior_num}')
        print(f'[INFO] Próximo sequencial: {proximo_sequencial}')

        return f'{proximo_sequencial}', proximo_sequencial

    except Exception as err:
        print(f'[ERRO] Falha ao identificar sequencial: {err}')
        return None, None


def rename_txt(caminho_CNAB, prox_sequencial):
    try:
        print(f'\n[INFO] Iniciando renomeação do arquivo CNAB: {caminho_CNAB}')

        nome_original = os.path.basename(caminho_CNAB)
        nome_sem_extensao, extensao = os.path.splitext(nome_original)

        # Regex para capturar: CB + DDMM + sequencial
        match = re.match(r'^(CB\d{4})(\d+)$', nome_sem_extensao, re.IGNORECASE)

        if not match:
            raise ValueError(f'Nome do arquivo não está no padrão esperado: {nome_original}')

        prefixo_data = match.group(1)      # Ex: CB2206
        sequencial_antigo = match.group(2) # Ex: 0000385

        # Garante que o novo nome tenha 13 caracteres antes do .REM
        total_digitos = 13 - len(prefixo_data)
        novo_sequencial = f'{prox_sequencial:0{total_digitos}}'

        novo_nome = f'{prefixo_data}{novo_sequencial}{extensao}'
        novo_caminho = os.path.join(os.path.dirname(caminho_CNAB), novo_nome)

        # Atualiza o header: MX0000000
        ajuste_seq = f'MX{prox_sequencial:07}'
        print(f'[DEBUG] Substituindo header por: {ajuste_seq}')

        with open(caminho_CNAB, 'r', encoding='ascii') as f:
            linhas = f.readlines()

        if linhas:
            linhas[0] = re.sub(r'MX\d{7}', ajuste_seq, linhas[0], count=1)
            print(f'[DEBUG] Header modificado: {linhas[0].strip()}')

        with open(caminho_CNAB, 'w', encoding='ascii') as f:
            f.writelines(linhas)

        time.sleep(1)
        os.rename(caminho_CNAB, novo_caminho)
        print(f'[INFO] Arquivo renomeado para: {novo_caminho}')

        return novo_caminho

    except Exception as err:
        print(f'[ERRO] Falha ao tratar arquivo REM: {err}')
        return None


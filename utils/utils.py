##################################
# 0. Librerías
##################################
import os
import time
import json
import wget
import zipfile
import requests
import platform

import datetime
import pandas as pd
from browsermobproxy import Server

import psycopg2
from sqlalchemy import create_engine

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

from utils.paths import PROJECT_PATH

# 0. Variables iniciales
OS_PATH = PROJECT_PATH
TIME_SLEEP = 5
ITERATIONS = 4

##################################
# 0. Funciones de procesamiento
##################################

def process_date(date):
    try:
        return date.replace('T',' ').split('.')[0]
    except:
        return None

##################################
# 1. Funciones de PostgreSQL
##################################

def create_update_table(df, tabla, db_user, db_password, db_host, db_port, db_name):   
    # 1. Crear conexión a la base de datos
    connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    engine = create_engine(connection_string)

    # 2. Guarda el DataFrame en la tabla de PostgreSQL
    df.to_sql(tabla, engine, if_exists='replace', index=False)
    print("El DataFrame `{}` se ha guardado correctamente en la tabla de PostgreSQL.".format(tabla))

    # 3. Cerar conexión de base de datos
    engine.dispose()

def insert_dataframe_to_table(dataframe, table_name, db_user, db_password, db_host, db_port, db_name):
    # 1. Conexión a la base de datos PostgreSQL
    connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    engine = create_engine(connection_string)
    
    # 2. Insertar DataFrame en la tabla
    dataframe.to_sql(table_name, engine, if_exists='append', index=False)

    # 3. Cerar conexión de base de datos
    engine.dispose()

def select_from_table(query, db_user, db_password, db_host, db_port, db_name):
    # 1. Conexión a la base de datos PostgreSQL
    connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    conn = create_engine(connection_string)

    # 2. Ejecutar la consulta y obtener los resultados
    results = pd.read_sql(query, conn)

    # 3. Cerrar la conexión a la base de datos
    conn.dispose()

    return results

######################################
# 2. Funciones del driver y proxy
######################################
def download_driver(path):

    # 1. Obtener la última versión del driver
    url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    response = requests.get(url)
    version_number = response.text

    # 2. Costruir la url de descarga
    os_platform = platform.system().lower()
    print("Sistema operativo: ", os_platform)

    system_version = ''
    if os_platform == "windows":
        system_version = version_number + "/chromedriver_win32.zip"
        print("Estás utilizando Windows.")

    elif os_platform == "linux":
        system_version = version_number +"/chromedriver_linux64.zip"
        print("Estás utilizando Linux.")
        
    elif os_platform == "darwin":
        system_version = version_number +"/	chromedriver_mac_arm64.zip"
        print("Estás utilizando macOS.")

    else:
        print("No se pudo determinar el sistema operativo.")

    # 3. Descargar el driver y extraer el driver
    print("Descargando la versión: ", system_version)
    download_url = "https://chromedriver.storage.googleapis.com/" + system_version
    latest_driver_zip = wget.download(download_url,'chromedriver.zip')

    with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
        zip_ref.extractall(path) # you can specify the destination folder path here

    # 4. Eliminar el zip
    os.remove(latest_driver_zip)



def get_chrome_driver(chromedriver_path=None, print_view=False, headless=False):
    
    # Iniciar el servidor proxy
    if os.name == 'nt':  # Para Windows
        browsermob_path = os.path.join(OS_PATH, 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy.bat')
        print("Se inicia el servidor en Windows")
    else:  # Para Mac o Linux
        browsermob_path = os.path.join(OS_PATH, 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy')
        print("Se inicia el servidor en Mac o Linux")
    
    server = Server(browsermob_path) 
    server.start()
    proxy = server.create_proxy(params={'trustAllServers': 'true'})
        
    # Configurar las opciones de Selenium
    options = webdriver.ChromeOptions()

    options.add_argument("--no-sandbox")
    # options.add_argument("--start-maximized")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--proxy-server={0}".format(proxy.proxy))

    if print_view:
        options.add_argument('--disable-print-preview')
    
    if headless:
        options.add_argument("--headless=new")

    if chromedriver_path is not None:
        print("Usando el chromedriver_path: {}".format(chromedriver_path))
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        print("Usando el chromedriver_path por defecto")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver, server, proxy

def get_firefox_driver(geckodriver_path=None, print_view=False, headless=False):
    # Iniciar el servidor proxy
    if os.name == 'nt':  # Para Windows
        browsermob_path = os.path.join(OS_PATH, 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy.bat')
        print("Se inicia el servidor en Windows")
    else:  # Para Mac o Linux
        browsermob_path = os.path.join(OS_PATH, 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy')
        print("Se inicia el servidor en Mac o Linux")

    server = Server(browsermob_path)
    server.start()
    proxy = server.create_proxy(params={'trustAllServers': 'true'})

    # Configurar las opciones de Selenium
    options = webdriver.FirefoxOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--proxy-server={0}".format(proxy.proxy))

    if print_view:
        options.add_argument('--disable-print-preview')

    if headless:
        options.add_argument("--headless")

    print("Usando el geckodriver_path por defecto")
    service = Service(executable_path='geckodriver.exe')
    driver = webdriver.Firefox(service=service, options=options)

    return driver, server, proxy




def stop_chrome_driver(driver, server, proxy):
    driver.quit()
    server.stop()
    proxy.close()


def try_close_modal(driver):
    # Modal de encuesta
    try:
        time.sleep(1)
        driver.find_element('class name','_hj-x7hBM__styles__closeModalBtn').click()
        time.sleep(1)
    except:
        time.sleep(1)

    # Modal de actualización de caja
    try:
        time.sleep(1)
        driver.find_element("css selector", "button[data-v-00baa7d9]").click()
        time.sleep(1)
    except:
        time.sleep(1)



##################################
# 3. Funciones de Selenium
##################################

def find_elements_decorator(func):
    def wrapper(driver, by, value, text):
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((by, value)))
            func(driver, by, value, text)
            time.sleep(1)

        except:
            print(f"Ocurrió un error by: ({by}), value: ({value})")
    return wrapper

def find_element_decorator(func):
    def wrapper(driver, by, value):
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((by, value)))
            func(driver, by, value)
            time.sleep(1)

        except:
            print(f"Ocurrió un error by: ({by}), value: ({value})")
    return wrapper

def login_decorator(func):
    def wrapper(driver, by, value, username, password):
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((by, value)))
            func(driver, by, value, username, password)
            time.sleep(1)

        except:
            print(f"Ocurrió un error by: ({by}), value: ({value})")

    return wrapper

@find_elements_decorator
def find_elements_and_click(driver, by, value, text):
    elements = driver.find_elements(by, value)
    for element in elements:
        if text in element.text:
            element.click()
            break

@find_element_decorator
def find_element_and_click(driver, by, value):
    driver.find_element(by, value).click()

@login_decorator
def login(driver, by, value , username, password):
    elementos = driver.find_elements("css selector", ".v-field__input")
    time.sleep(1)
    elementos[0].send_keys(username)
    elementos[1].send_keys(password)
    time.sleep(1)
    driver.find_element(by,value).click()


#########################
# 4. Procesar Boletas
#########################
def process_ballots(har, LOCAL):
    i = 0
    for  entrie in har.get('log').get('entries'):
        string_content = entrie.get('response').get('content').get('text')

        if string_content is not None:
            if '_id' in string_content and 'serialNumber' in string_content:
                data_list = json.loads(string_content)
                with open(os.path.join(OS_PATH,'jsons','BOLETAS',LOCAL, str(i)+'_'+ LOCAL.lower() +'_data.json'), 'w') as json_file:
                    json.dump(data_list, json_file, indent=4)
                i += 1

    try:
        print('Hay {} boletas en la vista de 30 dias'.format(str(len(data_list))))
    except:
        print('No hay boletas en la vista de 30 dias')


def process_update_ballots(paths, LOCAL, db_user, db_password, db_host, db_port, db_name):

    # 1. Leer todos los archivos .json
    df_boletas = pd.concat([pd.read_json(path) for path in paths], axis=0)
    df_boletas['serialNumber'] = df_boletas['document'].apply(lambda x: x['serialNumber'])
    df_boletas['type'] = df_boletas['document'].apply(lambda x: x['type'])

    # 2. Eliminar document, eliminar duplicados y agragar LOCAL
    df_boletas.drop('document', axis=1, inplace=True)
    df_boletas.drop_duplicates(inplace=True)
    df_boletas['local'] = LOCAL

    # 3. Seleccionar columnas
    columnas = ['local','id','serialNumber','type','saleStatus','createdAt','updatedAt','paidAt'
                ,'clientName','currency','tableTag','totalReferencePrice','totalBaseAmount'
                ,'totalVat','totalPayableAmount','name','note','cashierName','orderTakerName'
                ,'paymentType','paymentWay','_id','business','store','registerTerminal'
                ,'cashoutTerminal','client','shift','cashier','consumptionSurcharge'
                ,'totalIcbperAmount','totalConsumptionSurcharge','seller','orderTaker','sellerName']
    df_boletas = df_boletas[columnas]

    # 4. Convertir a datetime createdAt, updatedAt y paidAt
    df_boletas['paidAt'] = df_boletas.apply(lambda row: process_date(row['paidAt']), axis=1)
    df_boletas['createdAt'] = df_boletas.apply(lambda row: process_date(row['createdAt']), axis=1)
    df_boletas['updatedAt'] = df_boletas.apply(lambda row: process_date(row['updatedAt']), axis=1)

    df_boletas['paidAt'] = pd.to_datetime(df_boletas['paidAt'])
    df_boletas['createdAt'] = pd.to_datetime(df_boletas['createdAt'])
    df_boletas['updatedAt'] = pd.to_datetime(df_boletas['updatedAt'])


    ##### 4. Leer la base de datos y cargar solo datos nuevos

    # 1. Leer la tabla de boletas
    query = f""" SELECT distinct "serialNumber" FROM public."BOLETAS" WHERE "local" = '{LOCAL}' """

    df_boletas_pg = select_from_table(query, db_user, db_password, db_host, db_port, db_name)
    df_boletas_pg['inPostgre'] = 1

    # 2. Unir las tablas y quedarse con las que no están en postgre
    df_boletas = df_boletas.merge(df_boletas_pg, how='left', on='serialNumber')
    df_boletas['inPostgre'] = df_boletas['inPostgre'].fillna(0)
    df_boletas = df_boletas[df_boletas['inPostgre'] == 0]
    df_boletas.drop('inPostgre', axis=1, inplace=True)

    # 3. Guardar en postgre
    if df_boletas.shape[0] > 0:
        insert_dataframe_to_table(df_boletas, 'BOLETAS', db_user, db_password, db_host, db_port, db_name)
        print('Hay ({}) boletas nuevas que se guardaran en postgreSQL'.format(df_boletas.shape[0]))
        
    else:
        print('no hay datos nuevos para guardar en postgreSQL')



#########################
# 5. Procesar Consumos
#########################

def get_bool_details(LOCAL,db_user, db_password, db_host, db_port, db_name):
    query = f"""
    SELECT
        A.*
    FROM (
        SELECT 
            "id"
            , "local"
            , "serialNumber"
            , "updatedAt"
            , concat('https://pos.miwally.com/SaleHistory/',"id") as url
        FROM public."BOLETAS"
        WHERE LOCAL = '{LOCAL}'
        AND "saleStatus" = 'ISSUED'
    ) A 
    LEFT JOIN (
        SELECT
            distinct "serialNumber"
        FROM public."CONSUMO"
    ) B
    ON A."serialNumber" = B."serialNumber"
    WHERE B."serialNumber" IS NULL
    """

    aux_query = f""" SELECT * FROM public."BOLETAS" WHERE LOCAL = '{LOCAL}' AND "saleStatus" = 'ISSUED' """
    print('--> Todas las boletas del local ',str(select_from_table(aux_query, db_user, db_password, db_host, db_port, db_name).shape))

    df_boletas = select_from_table(query, db_user, db_password, db_host, db_port, db_name)
    print('--> Boletas que no están en consumo ',str(df_boletas.shape))

    return df_boletas


def iter_urls(driver, proxy, df_boletas, LOCAL):
# 2. Iterar las URLs
    i = 0
    list_ids = []
    # for index, row in df_boletas.head(100).iterrows(): # Pruebas
    for index, row in df_boletas.iterrows(): # Correr todo
        try:
            # Obtener el id y la url
            id = '"id":"' + row['id'] + '"'
            url = row['url']

            # Cargar la url
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "text-3xl-600")))

            # Guardar los id para buscar en json
            list_ids.append(id)
            print(f'{str(i).zfill(2)} -> url: {url}')
            i += 1
        except:
            break

    # 3. Obtener el .har y guardar los json
    time.sleep(TIME_SLEEP*4)
    har = proxy.har
    i = 0
    for  entrie in har.get('log').get('entries'):
        string_content =  entrie.get('response').get('content').get('text')

        if string_content is not None:
            # Buscar los ids en el json
            for id in list_ids:
                if id in string_content:
                    # Si se encuentra el id, guardar el json
                    print(f'{str(i)}: id {id} encontrado')
                    data_list = json.loads(string_content)
                    with open(os.path.join(OS_PATH,'jsons','CONSUMO',LOCAL, str(i) + '_' + LOCAL.lower() +'_data.json'), 'w') as json_file:
                        json.dump(data_list, json_file, indent=4)
                    i += 1
                
                    # Eliminar el valor que se encontró en la lista
                    list_ids.remove(id)


def process_update_ballot_details(paths, db_user, db_password, db_host, db_port, db_name):
    # 1. Leer todos los archivos .json
    # paths = get_files(os.path.join(OS_PATH,'jsons','CONSUMO',LOCAL), '.json')

    df_consumo = pd.concat([pd.read_json(path) for path in paths], axis=0).reset_index(drop=True)
    df_consumo = df_consumo[['createdAt','updatedAt','paidAt','saleItems','document','payments']]

    # 2. Convertir a datetime createdAt, updatedAt y paidAt
    df_consumo['paidAt'] = df_consumo.apply(lambda row: process_date(row['paidAt']), axis=1)
    df_consumo['createdAt'] = df_consumo.apply(lambda row: process_date(row['createdAt']), axis=1)
    df_consumo['updatedAt'] = df_consumo.apply(lambda row: process_date(row['updatedAt']), axis=1)

    df_consumo['paidAt'] = pd.to_datetime(df_consumo['paidAt'])
    df_consumo['createdAt'] = pd.to_datetime(df_consumo['createdAt'])
    df_consumo['updatedAt'] = pd.to_datetime(df_consumo['updatedAt'])

    # 3. Extraer serialNumber y los productos vendidos
    df_consumo['serialNumber'] = df_consumo['document'].apply(lambda x: x['serialNumber'])

    df_consumo = df_consumo.explode('saleItems')
    df_consumo['paymentName'] = df_consumo['payments'].apply(lambda x: x[0]['name'] if x[0]['name'] == 'Tarjeta' else 'Efectivo')
    # df_consumo['paymentType'] = df_consumo['payments'].apply(lambda x: x[0]['cardInformation']['type'] if x[0]['name'] == 'Tarjeta' else 'CASH')
    df_consumo['paymentType'] = df_consumo['payments'].apply(lambda x: 'CARD' if x[0]['name'] == 'Tarjeta' else 'CASH')

    # 4. Obtener el detalle de saleItems
    def extract_values(sale_item):
        return pd.Series({
            'productId': sale_item.get('id'),
            'product': sale_item.get('name'),
            'note': sale_item.get('note'),
            'quantity': sale_item.get('quantity'),
            'referenceUnitPrice': sale_item.get('referenceUnitPrice'),
            'taxGroup': sale_item.get('taxGroup'),
            'totalBaseAmount': sale_item.get('totalBaseAmount'),
            'totalVat': sale_item.get('totalVat'),
            'totalReferencePrice': sale_item.get('totalReferencePrice'),
            'totalPayableAmount': sale_item.get('totalPayableAmount')
        })

    df_sale_items = df_consumo['saleItems'].apply(extract_values)
    df_consumo = pd.concat([df_consumo, df_sale_items], axis=1)
    df_consumo.reset_index(drop=True, inplace=True)

    # 7. Ordenar columnas y guardar
    df_consumo = df_consumo[['serialNumber','paymentType', 'productId','taxGroup'
                            , 'product', 'note','quantity', 'referenceUnitPrice'
                            , 'totalBaseAmount', 'totalVat', 'totalPayableAmount']]

    if df_consumo.shape[0] > 0:
        insert_dataframe_to_table(df_consumo, 'CONSUMO', db_user, db_password, db_host, db_port, db_name)
        print('Se insertaron ({}) detalles de consumo en postgreSQL'.format(df_consumo.shape[0]))
    else:
        print('No hay datos para insertar')

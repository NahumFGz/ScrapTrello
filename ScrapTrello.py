####################################
## A. Librerias
####################################
import os
import time
import json

import datetime
import pandas as pd

from utils.utils import *
from utils.paths import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

####################################
## B. Funciones
####################################

def get_files(path, extension):
    dir_name  = os.path.join(os.getcwd(), path)
    files     = os.listdir(dir_name)
    
    paths    = []
    for file in files:
        if extension in file:
            paths.append(os.path.join(path,file))

    return paths

def columns_to_string(df):
    columns = list(df.columns)    
    for column in columns:
        df[column] = df[column].astype(str)
    return df

####################################
## C. Configuración de parametros
####################################

## 1. Seleccionar modo
HEADLESS = False
PRINT_VIEW = False
CHROMEDRIVER_PATH = None

## 2. Leer credenciales de postgres
POSTGRE_CREDS_PATH = os.path.join(os.getcwd(),'creds','postgre_creds.json')

## 3. Leer credenciales de postgres
pd_postgre_crefs = pd.read_json(POSTGRE_CREDS_PATH)

db_host = pd_postgre_crefs['db_host'][0]
db_port = pd_postgre_crefs['db_port'][0]
db_name = pd_postgre_crefs['db_name'][0]
db_user = pd_postgre_crefs['db_user'][0]
db_password = pd_postgre_crefs['db_password'][0]


## 4. Todos los DNI
query = """
SELECT 
	  "documentNumber"
FROM public."DNI"
WHERE LENGTH ("documentNumber") = 8
"""
df_all_dni = select_from_table(query, db_user, db_password, db_host, db_port, db_name)
print('--> Todas los DNIs:', len(df_all_dni))

## 5. Todos los DNIs que no tienen fechaNacimiento
query = """
SELECT
	A."documentNumber"
FROM (
	SELECT 
		  "documentNumber"
	FROM public."DNI"
	WHERE LENGTH ("documentNumber") = 8
) A 
LEFT JOIN public."DNI_DETALLES" B
ON A."documentNumber" = B."numeroDocumento"
WHERE B."numeroDocumento" IS NULL
"""
df_find_dni = select_from_table(query, db_user, db_password, db_host, db_port, db_name)
print('--> DNIs sin fechaNacimiento:', len(df_find_dni))


########################
## D. Ejecución
########################

# 1. Iniciar el driver, el servidor proxy y el proxy
driver, server, proxy = get_chrome_driver(chromedriver_path=CHROMEDRIVER_PATH, print_view=PRINT_VIEW, headless=HEADLESS)
print('1. Se inició el driver, el servidor proxy y el proxy')

# 2. Eliminar todos los archivos de la carpeta
try:
    os.mkdir('jsons')
    print('Se creó la carpeta ./jsons')
except:
    print('Ya existe  ./jsons')

try:
    os.mkdir('jsons/DNI_DETALLES')
    print('Se creó la carpeta ./jsons/DNI_DETALLES')
except:
    print('Ya existe ./jsons/DNI_DETALLES')

try:
    os.mkdir(f'jsons/DNI_DETALLES')
    print(f'Se creó la carpeta ./jsons/DNI_DETALLES')
except:
    print(f'Ya existe ./jsons/DNI_DETALLES')

try:
    files = get_files(os.path.join(os.getcwd(),'jsons','DNI_DETALLES'), '.')
    for file in files:
        os.remove(file)
    print('Se eliminaron los archivos de la carpeta')
except:
    pass

# 3. Iniciar .har
options = {
    'captureHeaders': True, # Capturar los headers --> Default: False
    'captureContent': True, # Capturar el contenido --> Default: False
    'captureBinaryContent': False, # Capturar el contenido binario --> Default: False
    'captureCookies': True, # Capturar las cookies --> Default: False
    'captureHeadersSize': -1, 
    'captureMaxSize': -1, 
    'captureBinaryContentMaxLength': -1 # Tamaño máximo del contenido binario
}
proxy.new_har("rimac", options=options)

# 4. Iterar hasta encontrar todos los DNIs
i = 0
for dni in df_find_dni.head(1).values:
    
    # A. Ingresa a la página
    url = 'https://www.rimac.com/comprar/seguro-salud'
    driver.get(url)

    # B. Esperar a que cargue la página
    wait = WebDriverWait(driver, 20)
    
    # C. Ingresar DNI y celular
    dni_element = driver.find_element("id", "numDocumento2")
    cel_element = driver.find_element("id", "phone")
    dni_element.send_keys(dni[0])
    cel_element.send_keys('987322452')

    # D. Si aparece el aviso de eres miembro clic en "de acuerdo"
    try:
        time.sleep(7)
        for element in driver.find_elements("class name", "rbr-btn"):
            if 'De acuerdo' in element.text:
                element.click()
                break
        time.sleep(1)
    except:
        time.sleep(1)

    # E. Si aparece el campo day/month/year, entonces el DNI no existe en la BD de rimac
    try:
        driver.find_element("id", "year")
        EXISTE_DNI = False
    except:
        EXISTE_DNI = True

    # F. Si el DNI existe, aceptar TyC y click en cotizar
    if EXISTE_DNI:
        find_element_and_click(driver, 'css selector', "label[for='termscc']")
        time.sleep(5)
        find_element_and_click(driver,'class name', 'btn-zero')
    
    print(f'{i}. DNI: {dni[0]} - Existe: {EXISTE_DNI}')
    i = i + 1

# 5. Obtener el .har y guardar los json --> 42743152
time.sleep(15)
har = proxy.har
# har

# 6. Guardar solo el interes en un json  
i = 0
for  entrie in har.get('log').get('entries'):
    request  =  entrie.get('request')

    try:
        if request:
            postData = request.get('postData')
            if postData:
                mimeType = postData.get('mimeType')
                text = postData.get('text')
                if '"correo":' in text:
                    # Haz algo con mimeType y text, por ejemplo, imprimirlos
                    print(f"Text: {text}")
                    data_list = json.loads(text)
                    with open(os.path.join(os.getcwd(),'jsons','DNI_DETALLES', str(i) + '_data.json'), 'w') as json_file:
                        json.dump(data_list, json_file, indent=4)
    except:
        pass

# 7. Leer dataframe y guardar en la BD
ruta_archivo = "./jsons/DNI_DETALLES/0_data.json"

with open(ruta_archivo, "r") as archivo:
    data = json.load(archivo)

terceros = data["payload"]["request"]["payload"]["terceros"]
df_terceros = pd.DataFrame(terceros)
df_terceros.drop(columns=['ideRol'], inplace=True)
df_terceros.drop_duplicates(inplace=True)

# 8. Dar formato antes de cargar a la BD
columns_to_add = ['tipoDocumento', 'numeroDocumento', 'nombre', 'apePaterno','apeMaterno', 'correo', 'telefono', 'estCivil', 'fecNacimiento', 'sexo', 'pais']
for column in columns_to_add:
    if column not in df_terceros.columns:
        df_terceros[column] = ''

df_terceros = columns_to_string(df_terceros)
insert_dataframe_to_table(df_terceros, 'DNI_DETALLES', db_user, db_password, db_host, db_port, db_name)
print('Se cargó la tabla DNI_DETALLES')
print(df_terceros)
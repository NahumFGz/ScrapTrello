#########################
# 0. Librerías
#########################
import os
import platform

#########################
# 1. Definir variables
#########################

# A. Definir sistema operativo
os_platform = platform.system().lower()

# B. Ruta donde se encuentra el proyecto
if os_platform == 'darwin':
    PROJECT_PATH = '/Users/nahumfg/Desktop/GitHubProjects/ScrapTrello'

elif os_platform == 'windows':
    PROJECT_PATH = 'C:\GitHubProjets\ScrapTrello'

elif os_platform == 'linux':
    PROJECT_PATH = '/home/brew_test_gcp_01/Desktop/ScrapTrello'

# C. Definir rutas del chrome driver
if os_platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(PROJECT_PATH,'chromedriver','darwin','chromedriver')

elif os_platform == 'windows':
    CHROMEDRIVER_PATH = os.path.join(PROJECT_PATH,'chromedriver','windows','chromedriver.exe')

elif os_platform == 'linux':
    CHROMEDRIVER_PATH = os.path.join(PROJECT_PATH,'chromedriver','linux','chromedriver')

# D. Definir rutas generales
WALLY_CREDS_PATH = os.path.join(PROJECT_PATH,'creds','my_wally_creds.json')
POSTGRE_CREDS_PATH = os.path.join(PROJECT_PATH,'creds','postgre_creds.json')

# E. Imprimir variables
print('ESTAMOS EN ---> ', os_platform)
print('PROJECT_PATH: ', PROJECT_PATH)
print('CHROME_DRIVER_PATH: ', CHROMEDRIVER_PATH)
print('WALLY_CREDS_PATH: ', WALLY_CREDS_PATH)
print('POSTGRE_CREDS_PATH: ', POSTGRE_CREDS_PATH)
print('')
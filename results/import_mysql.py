import tkinter as tk
from tkinter import filedialog
import pandas as pd
import mysql.connector
from datetime import datetime

# Función para importar datos desde un archivo CSV a la base de datos MySQL
def importar_a_mysql(ruta_csv):
    try:
        # Conexión a la base de datos MySQL (reemplaza los valores con tus propias credenciales)
        conexion = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="cazarezf97",
            database="accounts"
        )
        
        # Crear un cursor
        cursor = conexion.cursor()

        # Leer el archivo CSV con pandas
        df = pd.read_csv(ruta_csv)

        # Obtener una lista de registros desde el DataFrame
        registros = df.to_records(index=False)

        # Iterar sobre los registros e imprimir información antes de la inserción
        for registro in registros:
            print(f"Registro a insertar: {registro}")

            # Asumiendo que tu tabla en MySQL tiene las mismas columnas que el CSV
            query = "INSERT INTO hbomax (idAccount, username, password, dateAdded) VALUES (NULL, %s, %s, %s)"
            valores = (registro[0], registro[1], datetime.now())

            # Intentar realizar la inserción
            try:
                cursor.execute(query, valores)
                conexion.commit()
                print("Inserción exitosa.")

            # Manejar posibles errores
            except mysql.connector.Error as err:
                print(f"Error durante la inserción: {err}")
                conexion.rollback()

        # Cerrar el cursor y la conexión
        cursor.close()
        conexion.close()

        print("Datos importados exitosamente a MySQL.")

    except Exception as e:
        print(f"Error general: {e}")

# Función para seleccionar un archivo CSV mediante una interfaz gráfica
def seleccionar_csv():
    ruta_csv = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
    if ruta_csv:
        importar_a_mysql(ruta_csv)

# Crear la interfaz gráfica
ventana = tk.Tk()
ventana.title("Importar datos a MySQL desde CSV")

# Botón para seleccionar archivo CSV
boton_seleccionar = tk.Button(ventana, text="Seleccionar CSV", command=seleccionar_csv)
boton_seleccionar.pack(pady=20)

# Iniciar el bucle principal de la interfaz gráfica
ventana.mainloop()

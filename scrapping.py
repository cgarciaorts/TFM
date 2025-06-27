import pandas as pd
import time
import os
from io import StringIO
from bs4 import BeautifulSoup
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
URLS_PARTIDOS = [
    "https://fbref.com/es/partidos/33e26065/Chelsea-Tottenham-Hotspur-Abril-3-2025-Premier-League",
    "https://fbref.com/es/partidos/5984e216/Brentford-Chelsea-Abril-6-2025-Premier-League",
    "https://fbref.com/es/partidos/a45626b5/Chelsea-Ipswich-Town-Abril-13-2025-Premier-League",
    "https://fbref.com/es/partidos/c559794a/Legia-Warsaw-Chelsea-Abril-10-2025-Conference-League",
    "https://fbref.com/es/partidos/c83977dc/Chelsea-Legia-Warsaw-Abril-17-2025-Conference-League",
    "https://fbref.com/es/partidos/aaac9748/Fulham-Chelsea-Abril-20-2025-Premier-League",
    "https://fbref.com/es/partidos/06c5f0ab/Chelsea-Everton-Abril-26-2025-Premier-League"
]

CARPETA_RAIZ = "partidos_a_analizar"

# --- FUNCIÓN DE DESCARGA Y LIMPIEZA ---
def descargar_y_limpiar(url, carpeta_principal, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        titulo_completo = soup.find('h1').text
        info_partido = titulo_completo.split(' Informe del partido')[0]
        equipos = info_partido.split(' vs. ')
        
        if len(equipos) == 2:
            equipo_local_limpio = equipos[0].strip().replace(' ', '_')
            equipo_visitante_limpio = equipos[1].strip().replace(' ', '_')
            nombre_carpeta_partido = f"{equipo_local_limpio}_vs_{equipo_visitante_limpio}"
        else:
            nombre_carpeta_partido = f"partido_desconocido_{int(time.time())}"

        ruta_partido = os.path.join(carpeta_principal, nombre_carpeta_partido)
        os.makedirs(ruta_partido, exist_ok=True)
        print(f"\n--- Descargando datos en: {ruta_partido} ---")
        
        tablas_relevantes = soup.find_all("table", class_=lambda x: x and 'stats_table' in x)
        
        for i, tabla_html in enumerate(tablas_relevantes):
            try:
                df = pd.read_html(StringIO(str(tabla_html)))[0]
                
                # --- INICIO DE LA LIMPIEZA DE DATOS ---
                
                # Eliminar filas completamente vacías (las que son solo comas en el CSV)
                df.dropna(how='all', inplace=True)
                
                columnas_originales = df.columns
                
                if 'País' in columnas_originales or any('País' in col for col in columnas_originales):
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(0)
                    if 'Jugador' in df.columns:
                        df = df[~df['Jugador'].str.contains(' jugadores', na=False)]
                    if 'Edad' in df.columns:
                        df['Edad'] = df['Edad'].astype(str).str.split('-').str[0]
                    if 'País' in df.columns:
                        df['País'] = df['País'].astype(str).str.extract(r'([A-Z]{3})')
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(0)
                
                # Reiniciar el índice después de cualquier posible eliminación de filas
                df = df.reset_index(drop=True)
                
                # --- FIN DE LA LIMPIEZA DE DATOS ---
                nombre_archivo = f"tabla_{i+1}.csv"
                archivo_path = os.path.join(ruta_partido, nombre_archivo)
                df.to_csv(archivo_path, index=False, encoding="utf-8-sig")
                print(f"   - ✅ Descargada y Limpia: {nombre_archivo}")

            except Exception as e:
                print(f"   - ⚠️ Error procesando la tabla individual nro {i+1}: {e}")

    except Exception as e:
        print(f"❌ Error grave en la URL {url}: {e}")

# --- FUNCIÓN DE RENOMBRADO ---
def renombrar_archivos_partido(ruta_carpeta_partido):
    print(f"\n--- Renombrando ficheros en: {ruta_carpeta_partido} ---")
    nombre_carpeta = os.path.basename(ruta_carpeta_partido)
    try:
        equipo_local, equipo_visitante = nombre_carpeta.split('_vs_')
    except ValueError:
        print(f"   - ❌ ERROR: El nombre de la carpeta '{nombre_carpeta}' no tiene el formato 'EquipoA_vs_EquipoB'.")
        return

    for nombre_fichero_antiguo in os.listdir(ruta_carpeta_partido):
        nombre_final = ""
        # Lógica de renombrado directo
        if nombre_fichero_antiguo == "tabla_1.csv": nombre_final = f"{equipo_local}_Resumen.csv"
        elif nombre_fichero_antiguo == "tabla_2.csv": nombre_final = f"{equipo_local}_Pases.csv"
        elif nombre_fichero_antiguo == "tabla_3.csv": nombre_final = f"{equipo_local}_TiposPases.csv"
        elif nombre_fichero_antiguo == "tabla_4.csv": nombre_final = f"{equipo_local}_AccionesDefensivas.csv"
        elif nombre_fichero_antiguo == "tabla_5.csv": nombre_final = f"{equipo_local}_Posesion.csv"
        elif nombre_fichero_antiguo == "tabla_6.csv": nombre_final = f"{equipo_local}_EstadisticasDiversas.csv"
        elif nombre_fichero_antiguo == "tabla_7.csv": nombre_final = f"{equipo_local}_Portero.csv"
        elif nombre_fichero_antiguo == "tabla_8.csv": nombre_final = f"{equipo_visitante}_Resumen.csv"
        elif nombre_fichero_antiguo == "tabla_9.csv": nombre_final = f"{equipo_visitante}_Pases.csv"
        elif nombre_fichero_antiguo == "tabla_10.csv": nombre_final = f"{equipo_visitante}_TiposPases.csv"
        elif nombre_fichero_antiguo == "tabla_11.csv": nombre_final = f"{equipo_visitante}_AccionesDefensivas.csv"
        elif nombre_fichero_antiguo == "tabla_12.csv": nombre_final = f"{equipo_visitante}_Posesion.csv"
        elif nombre_fichero_antiguo == "tabla_13.csv": nombre_final = f"{equipo_visitante}_EstadisticasDiversas.csv"
        elif nombre_fichero_antiguo == "tabla_14.csv": nombre_final = f"{equipo_visitante}_Portero.csv"
        elif nombre_fichero_antiguo == "tabla_15.csv": nombre_final = "Tiros_ambos_equipos.csv"
        elif nombre_fichero_antiguo == "tabla_16.csv": nombre_final = f"{equipo_local}_tiros.csv"
        elif nombre_fichero_antiguo == "tabla_17.csv": nombre_final = f"{equipo_visitante}_tiros.csv"

        if nombre_final:
            os.rename(os.path.join(ruta_carpeta_partido, nombre_fichero_antiguo), os.path.join(ruta_carpeta_partido, nombre_final))
            print(f"   - ✅ Renombrado: '{nombre_fichero_antiguo}' -> '{nombre_final}'")

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    if os.path.exists(CARPETA_RAIZ):
        shutil.rmtree(CARPETA_RAIZ)
    os.makedirs(CARPETA_RAIZ)

    print("===========================================")
    print(" Fase 1: Iniciando descarga de partidos...")
    print("===========================================")
    for url in URLS_PARTIDOS:
        descargar_y_limpiar(url, CARPETA_RAIZ, driver)
    driver.quit()
    print("\n🎉 Proceso de descarga y limpieza completado.")

    print("\n============================================")
    print(" Fase 2: Iniciando renombrado de ficheros...")
    print("============================================")
    carpetas_de_partidos = [os.path.join(CARPETA_RAIZ, d) for d in os.listdir(CARPETA_RAIZ) if os.path.isdir(os.path.join(CARPETA_RAIZ, d))]
    for carpeta in carpetas_de_partidos:
        renombrar_archivos_partido(carpeta)
    print("\n🎉 Proceso de renombrado completado.")
    
    print("\n\n✅✅✅ ¡TODO EL PROCESO HA FINALIZADO CON ÉXITO! ✅✅✅")
from playwright.sync_api import sync_playwright
import pandas as pd
import os
import io

def extraer_datos_por_bloques_limpios():
    print("Iniciando Bot - Extracción Limpia por Años (2021-2026)...")
    
    carpeta_raw = os.path.join("data", "raw")
    os.makedirs(carpeta_raw, exist_ok=True)
    
    tablas_por_año = []
    
    # Recorremos año por año, pero abriendo un navegador limpio para cada uno
    for anio in range(2021, 2027):
        with sync_playwright() as p:
            # Lanzamos un navegador totalmente nuevo por cada año para evitar basura en la caché
            navegador = p.chromium.launch(headless=False)
            pagina = navegador.new_page()
            pagina.on("dialog", lambda dialog: dialog.accept())
            
            try:
                print(f"\nBot: === Extrayendo año {anio} de forma independiente ===")
                
                fecha_inicio = f"01/01/{anio}"
                fecha_fin = f"31/12/{anio}" if anio != 2026 else "30/09/2026"
                
                # 1. Entrar a la página
                pagina.goto("http://sistemas.midagri.gob.pe/sisap/portal2/mayorista/", timeout=60000)
                
                # 2. Clic en Intervalo de Tiempo
                pagina.click("a#intervalo")
                
                # 3. Llenar fechas usando la lógica original que funcionaba
                pagina.fill("input#desde", fecha_inicio)
                pagina.fill("input#hasta", fecha_fin)
                
                # 4. Variables y Procedencia
                pagina.select_option("select#variables", ["precio_min", "volumen"])
                pagina.select_option("select#mercado", "15011501")
                pagina.select_option("select#procedencias", "120000") # Junín
                
                # 5. Marcar los productos exactamente igual que en el script original exitoso
                pagina.click("input#CHK_0104_CHK") # Papa
                pagina.click("input#CHK_0404_CHK") # Maíz seco
                pagina.click("input#CHK_0405_CHK") # Quinua
                
                print(f"Bot: Consultando rango {fecha_inicio} - {fecha_fin}...")
                pagina.click("button#consultar")
                
                # Esperamos 8 segundos a que cargue la tabla de fondo
                pagina.wait_for_timeout(8000)
                
                html_generado = pagina.content()
                tablas_html = pd.read_html(io.StringIO(html_generado))
                
                if len(tablas_html) > 0:
                    df_anio = max(tablas_html, key=len)
                    tablas_por_año.append(df_anio)
                    print(f"✅ ¡Año {anio} extraído correctamente ({len(df_anio)} filas)!")
                else:
                    print(f"⚠️ Advertencia: No se detectó tabla para el año {anio}")
                    
            except Exception as e:
                print(f"❌ Error en el año {anio}: {e}")
            finally:
                navegador.close()

    # --- CONSOLIDACIÓN FINAL ---
    if len(tablas_por_año) > 0:
        print("\nBot: Consolidando todos los años en el archivo maestro crudo...")
        df_completo = pd.concat(tablas_por_año, ignore_index=True)
        
        ruta_raw = os.path.join(carpeta_raw, "datos_precios_junin.csv")
        df_completo.to_csv(ruta_raw, index=False)
        
        print(f"🎉 ¡Éxito total! Archivo crudo guardado en:\n--> {ruta_raw}")
        print(f"Total de registros históricos unidos: {len(df_completo)}")
    else:
        print("\n❌ No se pudo recuperar ningún año.")

if __name__ == "__main__":
    extraer_datos_por_bloques_limpios()
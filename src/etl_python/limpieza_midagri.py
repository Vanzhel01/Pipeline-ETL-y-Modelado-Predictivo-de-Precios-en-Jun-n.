import pandas as pd
import numpy as np
import os
import csv

print("Iniciando transformación de datos hacia /data/processed/ ...")

try:
    # 1. Definir y crear rutas estructuradas
    carpeta_raw = os.path.join("data", "raw")
    carpeta_processed = os.path.join("data", "processed")
    os.makedirs(carpeta_processed, exist_ok=True)
    
    ruta_entrada = os.path.join(carpeta_raw, "datos_precios_junin.csv")
    ruta_salida = os.path.join(carpeta_processed, "precios_agrupados_mensual.csv")

    # 2. Leer desde la carpeta raw
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        lector_csv = csv.reader(f)
        datos_crudos = list(lector_csv)
        
    df_raw = pd.DataFrame(datos_crudos)

    # 3. Detectar encabezados (ignorar basura)
    fila_vars = 0
    for i, row in df_raw.head(15).iterrows():
        texto_fila = " ".join(row.fillna("").astype(str))
        if "Precio" in texto_fila or "Volumen" in texto_fila:
            fila_vars = i
            break
            
    l0_producto = df_raw.iloc[fila_vars - 1].copy() if fila_vars > 0 else df_raw.iloc[0].copy()
    l1_variable = df_raw.iloc[fila_vars].copy()
    l2_detalle = df_raw.iloc[fila_vars + 1].copy()
    df_data = df_raw.iloc[fila_vars + 2:].copy().reset_index(drop=True)

    # 4. Mapeo y Aplanamiento (Tidy Data)
    col_map = []
    current_prod = "Fecha"
    for i in range(len(l0_producto)):
        prod = str(l0_producto[i]).strip()
        var = str(l1_variable[i]).strip()
        det = str(l2_detalle[i]).strip()
        
        if prod and prod not in ["None", "", "nan", "0", "Fecha"] and not prod.isdigit():
            current_prod = prod
            
        if "Fecha" in var or "Fecha" in prod:
            col_map.append({'col_idx': i, 'Producto': 'Fecha', 'Tipo': 'Fecha'})
        elif "Precio" in var or "Precio" in det:
            col_map.append({'col_idx': i, 'Producto': current_prod, 'Tipo': 'Precio_Minimo'})
        elif "Volumen" in var and ("Total" in det or "Total" in var):
            col_map.append({'col_idx': i, 'Producto': current_prod, 'Tipo': 'Volumen_Total'})

    filas_limpias = []
    for idx, row in df_data.iterrows():
        fecha = row[0]
        if pd.isna(fecha) or fecha == "None" or "Fecha" in str(fecha):
            continue
            
        productos_en_fila = {}
        for mapping in col_map:
            if mapping['Producto'] == 'Fecha': continue
            prod = mapping['Producto']
            tipo = mapping['Tipo']
            val = str(row[mapping['col_idx']]).replace("...", "NaN").replace(",", "").strip()
            
            if prod not in productos_en_fila:
                productos_en_fila[prod] = {'Fecha': fecha, 'Producto': prod, 'Precio_Minimo': np.nan, 'Volumen_Total': np.nan}
                
            try:
                productos_en_fila[prod][tipo] = float(val)
            except:
                productos_en_fila[prod][tipo] = np.nan
                
        for prod, data in productos_en_fila.items():
            if not (pd.isna(data['Precio_Minimo']) and pd.isna(data['Volumen_Total'])):
                filas_limpias.append(data)

    df_clean = pd.DataFrame(filas_limpias)

    # 5. Agrupación Temporal
    df_clean['Fecha'] = pd.to_datetime(df_clean['Fecha'], format="%d/%m/%Y", errors='coerce')
    df_clean = df_clean.dropna(subset=['Fecha'])
    df_clean['Periodo'] = df_clean['Fecha'].dt.to_period('M').astype(str)

    df_mensual = df_clean.groupby(['Periodo', 'Producto']).agg({
        'Precio_Minimo': 'mean',
        'Volumen_Total': 'sum'
    }).reset_index()
    df_mensual['Precio_Minimo'] = df_mensual['Precio_Minimo'].round(2)

    # 6. Exportar a la carpeta processed
    df_mensual.to_csv(ruta_salida, index=False)
    print(f"\n¡Dataset final consolidado exitosamente en:\n--> {ruta_salida}")

except Exception as e:
    print(f"\nError en el procesamiento: {e}")
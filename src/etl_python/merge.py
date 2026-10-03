import pandas as pd
import os

print("Iniciando la Fusión Final (ETL) del Dataset Maestro...")

try:
    # 1. Definimos las rutas usando tus carpetas exactas
    ruta_economia = os.path.join("data", "processed", "precios_agrupados_mensual.csv")
    ruta_clima = os.path.join("data", "raw", "datos_clima.csv")
    ruta_maestra = os.path.join("data", "processed", "dataset_merged_junin.csv")

    # 2. Cargar los datos económicos
    print(f"Cargando economía desde: {ruta_economia}")
    df_economia = pd.read_csv(ruta_economia)
    df_economia['Periodo'] = df_economia['Periodo'].astype(str)

    # 3. Cargar los datos climáticos
    print(f"Cargando clima desde: {ruta_clima}")
    df_clima = pd.read_csv(ruta_clima)
    
    # 💡 LA SOLUCIÓN: Renombramos la columna 'fecha' a 'Periodo' para que coincidan las llaves
    df_clima = df_clima.rename(columns={'fecha': 'Periodo'})
    df_clima['Periodo'] = df_clima['Periodo'].astype(str)

    # 4. La Fusión (Inner Merge)
    print("Uniendo las tablas relacionales mediante la llave 'Periodo'...")
    df_maestro = pd.merge(df_economia, df_clima, on='Periodo', how='inner')

    # 5. Ordenar el dataset para el modelo
    df_maestro = df_maestro.sort_values(by=['Producto', 'Periodo']).reset_index(drop=True)
    df_maestro = df_maestro.ffill() # Imputación de datos vacíos

    print("\n¡Fusión Exitosa! Muestra del Dataset :")
    print(df_maestro.head(10))

    # 6. Exportar el entregable final
    df_maestro.to_csv(ruta_maestra, index=False)
    print(f"Dataset guardado en:\n--> {ruta_maestra}")

except FileNotFoundError as e:
    print(f"\nError de archivo: {e}")
except Exception as e:
    print(f"\nOcurrió un error técnico durante la fusión: {e}")
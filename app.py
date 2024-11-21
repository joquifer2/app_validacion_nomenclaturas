import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import re 
import io 


# Título principal
st.title("Validación de Nomenclaturas")

# Barra lateral para la navegación
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Selecciona una sección", ["Configuración de Reglas", "Validación de Datos", "Corrección Manual", "Exportar Resultados"])

# Configuración de Reglas
if opcion == "Configuración de Reglas":
    st.header("Configuración de Reglas")
    st.write("Aquí podrás definir las reglas de validación.")
    
# Validación de Datos
elif opcion == "Validación de Datos":
    st.header("Validación de Datos")
    st.write("Aquí podrás cargar y validar tus datos.")
    
# Corrección Manual
elif opcion == "Corrección Manual":
    st.header("Corrección Manual")
    st.write("Aquí podrás corregir los errores detectados.")
    
# Exportar Resultados
elif opcion == "Exportar Resultados":
    st.header("Exportar Resultados")
    st.write("Aquí podrás descargar los datos corregidos.")

if opcion == "Configuración de Reglas":
    st.header("Configuración de Reglas")

    # Input para definir el formato de las reglas
    regla = st.text_input("Define el formato de las nomenclaturas (Ejemplo: Cliente-Mes-Campaña)")

    # Selección de campos obligatorios
    obligatorio = st.checkbox("¿Hacer este formato obligatorio?")
    
    # Vista previa dinámica
    if regla:
        st.write("Vista previa del formato definido:")
        st.code(f"{regla}", language="text")
    
    # Botón para guardar la regla (lógica aún no implementada)
    if st.button("Guardar Regla"):
        st.success("Regla guardada correctamente.")




#### Validación de datos

elif opcion == "Validación de Datos":
    st.header("Validación de Datos")

    # Subir archivo
    uploaded_file = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])

    if uploaded_file:
        # Leer archivo dependiendo del tipo
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)

        # Normalizar nombres de columnas
        data.columns = data.columns.str.strip().str.lower()

        # Reglas de validación
        def validar_nomenclatura(nomenclatura):
            pattern = r"^\[JQF\]-\[(0[1-9]|[1-9][0-9])\]-\[(Display|Search|Pmax|Discovery|Youtube)\]$"
            return bool(re.match(pattern, nomenclatura))

        # Aplicar validación
        data['error'] = data.apply(
            lambda row: "Error en la nomenclatura" if not validar_nomenclatura(f"{row['cliente']}-{row['mes']}-{row['campaña']}") else None,
            axis=1
        )

        # Filtrar errores y guardarlos en session_state
        errores = data[data['error'].notnull()]
        st.session_state['errores'] = errores  # Guardar datos con errores
        st.session_state['data'] = data  # Guardar todos los datos

        # Mostrar resumen de validación
        st.subheader("Resumen de Validación")
        st.metric("Total de filas validadas", len(data))
        st.metric("Errores detectados", len(errores))

        # Mostrar errores detectados
        if not errores.empty:
            st.warning("Se encontraron errores en las siguientes filas:")
            st.dataframe(errores)
        else:
            st.success("No se encontraron errores. Todos los datos son válidos.")


    if errores.empty:
        st.warning("No se encontraron errores en los datos. Todos los datos son válidos.")
    else:
        st.session_state['errores'] = errores


### Corrección manual

elif opcion == "Corrección Manual":
    st.header("Corrección Manual")

    # Verificar si hay datos de errores en session_state
    if 'errores' in st.session_state and not st.session_state['errores'].empty:
        errores = st.session_state['errores']
        data_original = st.session_state['data']

        st.write("Datos con errores detectados (Editables):")

        # Configurar AgGrid para la tabla interactiva
        gb = GridOptionsBuilder.from_dataframe(errores)
        gb.configure_default_column(editable=True)  # Permitir edición de todas las columnas
        grid_options = gb.build()

        # Mostrar la tabla interactiva
        grid_response = AgGrid(
            errores,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True
        )

        # Obtener los datos corregidos
        df_corregido = pd.DataFrame(grid_response['data'])

        # Normalizar tipos de datos en df_corregido
        for col in df_corregido.columns:
            if errores[col].dtype == 'object':
                df_corregido[col] = df_corregido[col].fillna("").astype(str)
            elif errores[col].dtype in ['int64', 'float64']:
                df_corregido[col] = pd.to_numeric(df_corregido[col], errors='coerce').fillna(0)

        # Eliminar filas originales con errores del DataFrame original
        data_original = data_original.drop(errores.index)

        # Añadir las filas corregidas al DataFrame original
        data_actualizado = pd.concat([data_original, df_corregido])

        # Restablecer el índice para evitar problemas de tipo
        data_actualizado.reset_index(drop=True, inplace=True)

        # Guardar el conjunto actualizado en session_state
        st.session_state['data'] = data_actualizado

        # Mostrar los datos completos con las correcciones aplicadas
        st.write("Datos completos después de las correcciones:")
        st.dataframe(data_actualizado)

        # Botón para guardar los datos corregidos
        if st.button("Guardar Datos Corregidos"):
            st.session_state['data'] = data_actualizado  # Guardar la versión actualizada
            st.success("Datos corregidos guardados correctamente.")
    else:
        st.warning("No hay datos con errores para corregir. Realiza primero la validación.")





### Exportación del resultado

elif opcion == "Exportar Resultados":
    st.header("Exportar Resultados")

    # Verificar si hay datos disponibles en session_state
    if 'data' in st.session_state:
        # Obtener los datos completos actualizados
        data_final = st.session_state['data'].copy()

        # Normalizar los datos para evitar problemas de serialización
        for col in data_final.columns:
            if data_final[col].dtype == 'object':
                data_final[col] = data_final[col].fillna("").astype(str)  # Convertir objetos a strings
            elif data_final[col].dtype in ['int64', 'float64']:
                data_final[col] = pd.to_numeric(data_final[col], errors='coerce').fillna(0)

        # Mostrar una vista previa de los datos exportables
        st.subheader("Vista previa de los datos completos:")
        st.dataframe(data_final)

        # Botón para descargar los datos completos como CSV
        st.subheader("Exportar como CSV")
        csv = data_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Datos Completos (CSV)",
            data=csv,
            file_name='datos_completos.csv',
            mime='text/csv',
            key="download_csv"  # Asignar un identificador único
        )

        # Botón para descargar los datos completos como Excel
        st.subheader("Exportar como Excel")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data_final.to_excel(writer, index=False, sheet_name='Datos Completos')
        excel_data = output.getvalue()
        st.download_button(
            label="Descargar Datos Completos (Excel)",
            data=excel_data,
            file_name='datos_completos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key="download_excel"  # Asignar un identificador único
        )
    else:
        st.warning("No hay datos disponibles para exportar. Realiza primero la validación y corrección manual.")


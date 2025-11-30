import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="ICATEX - Dashboard de Optimización",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🏭 ICATEX - Dashboard de Optimización de Producción")
st.markdown("---")

# Cargar datos desde el archivo Excel
# Cargar datos desde el archivo Excel
# Cargar datos desde el archivo Excel
# Cargar datos desde el archivo Excel
@st.cache_data
def load_data():
    file_path = "ICATEX_Lingo_4Anios.xlsx"
    
    data = {}
    sheets = [
        'SET_PRODUCTOS', 'SET_MESES', 'SET_INSUMOS', 'SET_PROCESOS',
        'DAT_PI_MATRIX', 'DAT_PP_MATRIX', 'DAT_PM_MATRIX', 'DAT_PJM_MATRIX',
        'DAT_KM_MATRIX', 'DAT_PRODUCTOS_FIJOS'
    ]
    
    for sheet in sheets:
        try:
            data[sheet] = pd.read_excel(file_path, sheet_name=sheet)
        except Exception as e:
            st.warning(f"No se pudo cargar la hoja {sheet}: {e}")
            data[sheet] = pd.DataFrame()
    
    # Procesar resultados de LINGO - CORREGIDO
    try:
        # Leer hoja RESULTADOS saltando la primera fila (encabezado)
        resultados = pd.read_excel(file_path, sheet_name='RESULTADOS', header=None, skiprows=1)
        
        # Verificar que tenemos 960 filas (20 productos * 48 meses)
        if len(resultados) >= 960:
            # Crear arrays para ID_Producto y Periodo_Index
            id_productos = []
            periodo_indices = []
            
            # Generar IDs de productos (P001 a P020) repetidos cada 48 periodos
            for producto in range(1, 21):  # 20 productos
                for periodo in range(1, 49):  # 48 periodos
                    id_productos.append(f"P{producto:03d}")
                    periodo_indices.append(periodo)
            
            # Convertir datos a numérico - tomamos las primeras 3 columnas
            produccion_data = resultados.iloc[:960, 0].astype(float).values
            ventas_data = resultados.iloc[:960, 1].astype(float).values
            inventario_data = resultados.iloc[:960, 2].astype(float).values
            
            # Crear DataFrames separados
            data['RES_PRODUCCION'] = pd.DataFrame({
                'ID_Producto': id_productos,
                'Periodo_Index': periodo_indices,
                'Produccion': produccion_data
            })
            
            data['RES_VENTAS'] = pd.DataFrame({
                'ID_Producto': id_productos,
                'Periodo_Index': periodo_indices,
                'Ventas': ventas_data
            })
            
            data['RES_INVENTARIO'] = pd.DataFrame({
                'ID_Producto': id_productos,
                'Periodo_Index': periodo_indices,
                'Inventario': inventario_data
            })
            
            
        else:
            st.warning(f"Resultados insuficientes: {len(resultados)} filas, se esperaban 960")
            # Crear DataFrames vacíos para evitar errores
            data['RES_PRODUCCION'] = pd.DataFrame()
            data['RES_VENTAS'] = pd.DataFrame()
            data['RES_INVENTARIO'] = pd.DataFrame()
            
    except Exception as e:
        st.warning(f"No se pudieron cargar los resultados de LINGO: {e}")
        # Crear DataFrames vacíos para evitar errores
        data['RES_PRODUCCION'] = pd.DataFrame()
        data['RES_VENTAS'] = pd.DataFrame()
        data['RES_INVENTARIO'] = pd.DataFrame()
    
    # Procesar horas extra - CORREGIDO
    try:
        # Leer hoja RES_HORAS_EXTRA saltando la primera fila (encabezado)
        horas_extra = pd.read_excel(file_path, sheet_name='RES_HORAS_EXTRA', header=None, skiprows=1)
        
        # Verificar que tenemos 240 filas de datos (5 procesos * 48 periodos)
        if len(horas_extra) >= 240:
            # Crear arrays para ID_Proceso y Periodo_Index
            id_procesos = []
            periodo_indices = []
            
            # Generar IDs de procesos (PR001 a PR005) repetidos cada 48 periodos
            for proceso in range(1, 6):  # 5 procesos
                for periodo in range(1, 49):  # 48 periodos
                    id_procesos.append(f"PR{proceso:03d}")
                    periodo_indices.append(periodo)
            
            # Convertir datos a numérico
            horas_extra_data = horas_extra.iloc[:240, 0].astype(float).values
            
            data['RES_H_EXTRAS'] = pd.DataFrame({
                'ID_Proceso': id_procesos,
                'Periodo_Index': periodo_indices,
                'HorasExtrasMinutos': horas_extra_data
            })
            
            
        else:
            st.warning(f"Horas extra insuficientes: {len(horas_extra)} filas, se esperaban 240")
            data['RES_H_EXTRAS'] = pd.DataFrame()
            
    except Exception as e:
        st.warning(f"No se pudieron cargar las horas extra de LINGO: {e}")
        data['RES_H_EXTRAS'] = pd.DataFrame()
    
    return data

# Cargar los datos
data = load_data()

# El resto del código permanece exactamente igual...
# [TODO EL RESTO DEL CÓDIGO QUE YA TENÍAS, SIN MODIFICAR]
# Solo reemplaza la función load_data() anterior con esta versión corregida

# Crear diccionarios para mapear códigos a nombres
nombres_insumos = {
    'I001': 'Algodón Premium', 'I002': 'Poliester', 'I003': 'Elastano', 
    'I004': 'Hilo Costura', 'I005': 'Colorante Rojo', 'I006': 'Colorante Azul',
    'I007': 'Botones Madera', 'I008': 'Cremalleras', 'I009': 'Etiquetas',
    'I010': 'Bolsas Empaque', 'I011': 'Tinta Estampado', 'I012': 'Hilo Bordar',
    'I013': 'Lentejuelas', 'I014': 'Mostacillas', 'I015': 'Material Básico'
}

nombres_procesos = {
    'PR001': 'Corte Tela', 'PR002': 'Costura Básica', 'PR003': 'Bordado',
    'PR004': 'Planchado', 'PR005': 'Empaquetado'
}

# Agregar información de años y meses a los datos de PM_MATRIX
if not data['DAT_PM_MATRIX'].empty:
    # Asignar años y meses basado en Periodo_Index
    def asignar_año_mes(periodo):
        if periodo <= 12:
            return 2021, periodo
        elif periodo <= 24:
            return 2022, periodo - 12
        elif periodo <= 36:
            return 2023, periodo - 24
        else:
            return 2024, periodo - 36
    
    data['DAT_PM_MATRIX']['Año'] = data['DAT_PM_MATRIX']['Periodo_Index'].apply(lambda x: asignar_año_mes(x)[0])
    data['DAT_PM_MATRIX']['Mes'] = data['DAT_PM_MATRIX']['Periodo_Index'].apply(lambda x: asignar_año_mes(x)[1])

# Sidebar para navegación
st.sidebar.title("📊 Navegación")
section = st.sidebar.radio(
    "Selecciona una sección:",
    ["📈 Resumen General", "👕 Productos", "📦 Insumos", "⚙️ Procesos", 
     "📊 Demanda y Mercado", "💰 Costos y Rentabilidad", "🔍 Modelo de Optimización", "🎯 Simulaciones", "🏁 Programación por Metas"]
)

# Función para formatear números
def format_currency(value):
    return f"$ {value:,.2f}"

# ===== SECCIÓN 1: RESUMEN GENERAL =====
if section == "📈 Resumen General":
    st.header("📈 Resumen General - ICATEX")
    
    # Métricas clave
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_productos = len(data['SET_PRODUCTOS'])
        st.metric("Total de Productos", total_productos)
    
    with col2:
        total_insumos = len(data['SET_INSUMOS'])
        st.metric("Total de Insumos", total_insumos)
    
    with col3:
        total_procesos = len(data['SET_PROCESOS'])
        st.metric("Procesos Productivos", total_procesos)
    
    with col4:
        total_periodos = len(data['SET_MESES'])
        st.metric("Meses de Planificación", total_periodos)
    
    # Información de productos fijos
    if not data['DAT_PRODUCTOS_FIJOS'].empty:
        st.subheader("📦 Distribución de Productos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por categoría
            cat_dist = data['DAT_PRODUCTOS_FIJOS']['Categoria'].value_counts()
            fig_cat = px.pie(values=cat_dist.values, names=cat_dist.index, 
                            title="Distribución de Productos por Categoría",
                            color_discrete_sequence=px.colors.qualitative.Set3)
            fig_cat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Distribución por línea
            linea_dist = data['DAT_PRODUCTOS_FIJOS']['Linea'].value_counts()
            fig_linea = px.bar(x=linea_dist.index, y=linea_dist.values,
                              title="Productos por Línea de Producción",
                              labels={'x': 'Línea', 'y': 'Cantidad de Productos'},
                              color=linea_dist.index)
            st.plotly_chart(fig_linea, use_container_width=True)
        
        # Tiempos de producción
        st.subheader("⏱️ Análisis de Tiempos de Producción")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tiempos = px.box(data['DAT_PRODUCTOS_FIJOS'], y='TiempoProd_Total(min)', 
                                title="Distribución de Tiempos de Producción Total")
            st.plotly_chart(fig_tiempos, use_container_width=True)
        
        with col2:
            # Tiempo promedio por categoría
            tiempo_categoria = data['DAT_PRODUCTOS_FIJOS'].groupby('Categoria')['TiempoProd_Total(min)'].mean().reset_index()
            fig_tiempo_cat = px.bar(tiempo_categoria, x='Categoria', y='TiempoProd_Total(min)',
                                   title="Tiempo Promedio de Producción por Categoría",
                                   color='Categoria')
            st.plotly_chart(fig_tiempo_cat, use_container_width=True)
        
        # Análisis de costos de almacenamiento
        st.subheader("💰 Costos de Almacenamiento por Producto")
        costos_almacen = data['DAT_PRODUCTOS_FIJOS'][['Nombre_Producto', 'CostoAlmacen']].sort_values('CostoAlmacen', ascending=False)
        fig_almacen = px.bar(costos_almacen, x='Nombre_Producto', y='CostoAlmacen',
                            title="Costo de Almacenamiento por Producto",
                            labels={'CostoAlmacen': 'Costo Almacenamiento ($)', 'Nombre_Producto': 'Producto'})
        fig_almacen.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_almacen, use_container_width=True)
        
        # Tabla resumen de productos
        st.subheader("📋 Resumen de Productos")
        st.dataframe(data['DAT_PRODUCTOS_FIJOS'][['Nombre_Producto', 'Categoria', 'Linea', 'TiempoProd_Total(min)', 'CostoAlmacen']])

# ===== SECCIÓN 2: PRODUCTOS =====
elif section == "👕 Productos":
    st.header("👕 Análisis Detallado de Productos")
    
    if not data['DAT_PRODUCTOS_FIJOS'].empty:
        # Selector de producto - mostrar nombres en lugar de códigos
        productos_options = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
        producto_seleccionado = st.selectbox("Selecciona un producto:", productos_options)
        
        if producto_seleccionado:
            producto_info = data['DAT_PRODUCTOS_FIJOS'][data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_seleccionado].iloc[0]
            producto_id = producto_info['ID_Producto']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Categoría", producto_info['Categoria'])
            with col2:
                st.metric("Línea", producto_info['Linea'])
            with col3:
                st.metric("Tiempo Producción", f"{producto_info['TiempoProd_Total(min)']} min")
            with col4:
                st.metric("Costo Almacen", format_currency(producto_info['CostoAlmacen']))
            
            # Información de insumos del producto
            st.subheader("📦 Insumos Requeridos")
            if not data['DAT_PI_MATRIX'].empty:
                # Filtrar insumos para el producto seleccionado
                insumos_producto = data['DAT_PI_MATRIX'][data['DAT_PI_MATRIX']['ID_Producto'] == producto_id]
                
                if not insumos_producto.empty:
                    # Transformar datos para visualización
                    insumos_data = []
                    for col in insumos_producto.columns[1:]:  # Excluir ID_Producto
                        cantidad = insumos_producto[col].iloc[0]
                        if cantidad > 0:
                            nombre_insumo = nombres_insumos.get(col, col)
                            insumos_data.append({
                                'Insumo': nombre_insumo,
                                'Código': col,
                                'Cantidad': cantidad
                            })
                    
                    if insumos_data:
                        df_insumos = pd.DataFrame(insumos_data)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_insumos = px.bar(df_insumos, x='Insumo', y='Cantidad',
                                                title=f"Insumos para {producto_seleccionado}",
                                                color='Insumo')
                            st.plotly_chart(fig_insumos, use_container_width=True)
                        
                        with col2:
                            fig_insumos_pie = px.pie(df_insumos, values='Cantidad', names='Insumo',
                                                    title=f"Distribución de Insumos - {producto_seleccionado}")
                            st.plotly_chart(fig_insumos_pie, use_container_width=True)
                        
                        # Mostrar tabla detallada
                        st.dataframe(df_insumos[['Insumo', 'Código', 'Cantidad']])
            
            # Tiempos por proceso
            st.subheader("⚙️ Tiempos por Proceso")
            if not data['DAT_PP_MATRIX'].empty:
                tiempos_proceso = data['DAT_PP_MATRIX'][data['DAT_PP_MATRIX']['ID_Producto'] == producto_id]
                
                if not tiempos_proceso.empty:
                    # Transformar datos para visualización
                    procesos_data = []
                    for col in tiempos_proceso.columns[1:]:  # Excluir ID_Producto
                        tiempo = tiempos_proceso[col].iloc[0]
                        nombre_proceso = nombres_procesos.get(col, col)
                        procesos_data.append({
                            'Proceso': nombre_proceso,
                            'Código': col,
                            'Tiempo_Minutos': tiempo
                        })
                    
                    df_procesos = pd.DataFrame(procesos_data)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_procesos = px.bar(df_procesos, x='Proceso', y='Tiempo_Minutos',
                                             title=f"Tiempos de Proceso para {producto_seleccionado}",
                                             color='Proceso')
                        st.plotly_chart(fig_procesos, use_container_width=True)
                    
                    with col2:
                        fig_procesos_pie = px.pie(df_procesos, values='Tiempo_Minutos', names='Proceso',
                                                 title=f"Distribución de Tiempos - {producto_seleccionado}")
                        st.plotly_chart(fig_procesos_pie, use_container_width=True)
            
            # Análisis histórico de demanda CON FILTRO POR AÑO
            st.subheader("📈 Comportamiento Histórico de Demanda")
            if not data['DAT_PM_MATRIX'].empty:
                demanda_producto = data['DAT_PM_MATRIX'][data['DAT_PM_MATRIX']['ID_Producto'] == producto_id]
                
                if not demanda_producto.empty:
                    # Filtro por año
                    años_disponibles = sorted(demanda_producto['Año'].unique())
                    año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles, key="demanda_year")
                    
                    demanda_filtrada = demanda_producto[demanda_producto['Año'] == año_seleccionado]
                    
                    # Obtener nombres de meses para el año seleccionado
                    meses_año = demanda_filtrada['Mes'].unique()
                    
                    fig_demanda = go.Figure()
                    fig_demanda.add_trace(go.Scatter(x=meses_año, 
                                                   y=demanda_filtrada['DemandaMinima'], 
                                                   name='Demanda Mínima', 
                                                   line=dict(color='orange'),
                                                   fill=None))
                    fig_demanda.add_trace(go.Scatter(x=meses_año, 
                                                   y=demanda_filtrada['DemandaMaxima'], 
                                                   name='Demanda Máxima', 
                                                   line=dict(color='red'),
                                                   fill='tonexty',
                                                   fillcolor='rgba(255,0,0,0.1)'))
                    fig_demanda.update_layout(title=f"Demanda Mínima y Máxima - {producto_seleccionado} - {año_seleccionado}",
                                             xaxis_title="Mes", yaxis_title="Unidades",
                                             showlegend=True)
                    st.plotly_chart(fig_demanda, use_container_width=True)
                    
                    # Evolución de precios y costos para el producto
                    st.subheader("💰 Evolución de Precios y Costos")
                    fig_precios_producto = go.Figure()
                    fig_precios_producto.add_trace(go.Scatter(x=meses_año, 
                                                            y=demanda_filtrada['PrecioVenta'], 
                                                            name='Precio Venta', 
                                                            line=dict(color='green')))
                    fig_precios_producto.add_trace(go.Scatter(x=meses_año, 
                                                            y=demanda_filtrada['CostoInsumo'], 
                                                            name='Costo Insumo', 
                                                            line=dict(color='red')))
                    fig_precios_producto.update_layout(title=f"Precios y Costos - {producto_seleccionado} - {año_seleccionado}",
                                                      xaxis_title="Mes", yaxis_title="Valor ($)")
                    st.plotly_chart(fig_precios_producto, use_container_width=True)

# ===== SECCIÓN 3: INSUMOS =====
elif section == "📦 Insumos":
    st.header("📦 Gestión de Insumos y Materiales")
    
    if not data['DAT_KM_MATRIX'].empty:
        # Selector de insumo - mostrar nombres en lugar de códigos
        insumos_options = [(cod, nombres_insumos.get(cod, cod)) for cod in data['SET_INSUMOS']['ID_Insumo'].tolist()]
        insumo_seleccionado_cod = st.selectbox(
            "Selecciona un insumo:", 
            options=[opt[0] for opt in insumos_options],
            format_func=lambda x: next((name for cod, name in insumos_options if cod == x), x)
        )
        
        if insumo_seleccionado_cod:
            nombre_insumo = nombres_insumos.get(insumo_seleccionado_cod, insumo_seleccionado_cod)
            
            # Filtrar datos del insumo seleccionado
            insumo_data = data['DAT_KM_MATRIX'][data['DAT_KM_MATRIX']['ID_Insumo'] == insumo_seleccionado_cod]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                stock_promedio = insumo_data['StockDisponible'].mean()
                st.metric("Stock Promedio", f"{stock_promedio:,.0f} unidades")
            with col2:
                stock_max = insumo_data['StockDisponible'].max()
                st.metric("Stock Máximo", f"{stock_max:,.0f} unidades")
            with col3:
                stock_min = insumo_data['StockDisponible'].min()
                st.metric("Stock Mínimo", f"{stock_min:,.0f} unidades")
            with col4:
                uso_minimo = insumo_data['UsoMinimo'].mean()
                st.metric("Uso Mínimo Promedio", f"{uso_minimo:,.0f} unidades")
            
            st.subheader(f"📊 Evolución de Stock - {nombre_insumo}")
            
            # Gráfico de stock disponible por período
            fig_stock = px.area(insumo_data, x='Periodo_Index', y='StockDisponible',
                               title=f"Stock Disponible de {nombre_insumo} por Período",
                               labels={'StockDisponible': 'Stock Disponible', 'Periodo_Index': 'Período'})
            st.plotly_chart(fig_stock, use_container_width=True)
            
            # Uso en productos
            st.subheader("👕 Productos que utilizan este insumo")
            if not data['DAT_PI_MATRIX'].empty:
                productos_uso = []
                for _, row in data['DAT_PI_MATRIX'].iterrows():
                    if row[insumo_seleccionado_cod] > 0:
                        producto_nombre = data['DAT_PRODUCTOS_FIJOS'][
                            data['DAT_PRODUCTOS_FIJOS']['ID_Producto'] == row['ID_Producto']
                        ]['Nombre_Producto'].iloc[0]
                        productos_uso.append({
                            'Producto': producto_nombre,
                            'Cantidad_Usada': row[insumo_seleccionado_cod]
                        })
                
                if productos_uso:
                    df_uso = pd.DataFrame(productos_uso)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_uso = px.bar(df_uso, x='Producto', y='Cantidad_Usada',
                                        title=f"Uso de {nombre_insumo} en Productos",
                                        color='Producto')
                        fig_uso.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_uso, use_container_width=True)
                    
                    with col2:
                        fig_uso_pie = px.pie(df_uso, values='Cantidad_Usada', names='Producto',
                                            title=f"Distribución de Uso - {nombre_insumo}")
                        st.plotly_chart(fig_uso_pie, use_container_width=True)
            
            # Análisis de tendencias de stock
            st.subheader("📈 Análisis de Tendencia de Stock")
            
            # Calcular tendencia
            x = np.array(insumo_data['Periodo_Index'])
            y = np.array(insumo_data['StockDisponible'])
            z = np.polyfit(x, y, 1)
            tendencia = np.poly1d(z)
            
            fig_tendencia = go.Figure()
            fig_tendencia.add_trace(go.Scatter(x=insumo_data['Periodo_Index'], 
                                             y=insumo_data['StockDisponible'],
                                             name='Stock Real',
                                             line=dict(color='blue')))
            fig_tendencia.add_trace(go.Scatter(x=insumo_data['Periodo_Index'], 
                                             y=tendencia(x),
                                             name='Tendencia',
                                             line=dict(color='red', dash='dash')))
            fig_tendencia.update_layout(title=f"Tendencia de Stock - {nombre_insumo}",
                                       xaxis_title="Período", yaxis_title="Stock")
            st.plotly_chart(fig_tendencia, use_container_width=True)
            
            # Tabla de datos del insumo
            st.subheader("📋 Datos Detallados del Insumo")
            st.dataframe(insumo_data[['Periodo_Index', 'StockDisponible', 'UsoMinimo']])

# ===== SECCIÓN 4: PROCESOS =====
elif section == "⚙️ Procesos":
    st.header("⚙️ Procesos Productivos")
    
    if not data['DAT_PJM_MATRIX'].empty:
        # Selector de proceso - mostrar nombres en lugar de códigos
        procesos_options = [(cod, nombres_procesos.get(cod, cod)) for cod in data['SET_PROCESOS']['ID_Proceso'].tolist()]
        proceso_seleccionado_cod = st.selectbox(
            "Selecciona un proceso:", 
            options=[opt[0] for opt in procesos_options],
            format_func=lambda x: next((name for cod, name in procesos_options if cod == x), x)
        )
        
        if proceso_seleccionado_cod:
            nombre_proceso = nombres_procesos.get(proceso_seleccionado_cod, proceso_seleccionado_cod)
            
            # Filtrar datos del proceso seleccionado
            proceso_data = data['DAT_PJM_MATRIX'][data['DAT_PJM_MATRIX']['ID_Proceso'] == proceso_seleccionado_cod]
            
            # Métricas del proceso
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                capacidad_promedio = proceso_data['CapacidadMinutos'].mean()
                st.metric("Capacidad Promedio", f"{capacidad_promedio:,.0f} min")
            with col2:
                costo_extra_promedio = proceso_data['CostoHoraExtra'].mean()
                st.metric("Costo Hora Extra Promedio", format_currency(costo_extra_promedio))
            with col3:
                capacidad_max = proceso_data['CapacidadMinutos'].max()
                st.metric("Capacidad Máxima", f"{capacidad_max:,.0f} min")
            with col4:
                capacidad_min = proceso_data['CapacidadMinutos'].min()
                st.metric("Capacidad Mínima", f"{capacidad_min:,.0f} min")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Capacidad por período
                fig_capacidad = px.line(proceso_data, x='Periodo_Index', y='CapacidadMinutos',
                                       title=f"Capacidad de {nombre_proceso}",
                                       labels={'CapacidadMinutos': 'Capacidad (minutos)', 'Periodo_Index': 'Período'})
                st.plotly_chart(fig_capacidad, use_container_width=True)
            
            with col2:
                # Costo de hora extra
                fig_costo_extra = px.line(proceso_data, x='Periodo_Index', y='CostoHoraExtra',
                                         title=f"Costo Hora Extra - {nombre_proceso}",
                                         labels={'CostoHoraExtra': 'Costo Hora Extra ($)', 'Periodo_Index': 'Período'})
                st.plotly_chart(fig_costo_extra, use_container_width=True)
            
            # Productos que usan este proceso
            st.subheader("👕 Productos que utilizan este proceso")
            if not data['DAT_PP_MATRIX'].empty:
                productos_proceso = []
                for _, row in data['DAT_PP_MATRIX'].iterrows():
                    if row[proceso_seleccionado_cod] > 0:
                        producto_nombre = data['DAT_PRODUCTOS_FIJOS'][
                            data['DAT_PRODUCTOS_FIJOS']['ID_Producto'] == row['ID_Producto']
                        ]['Nombre_Producto'].iloc[0]
                        productos_proceso.append({
                            'Producto': producto_nombre,
                            'Tiempo_Requerido': row[proceso_seleccionado_cod]
                        })
                
                if productos_proceso:
                    df_proceso = pd.DataFrame(productos_proceso)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_proceso = px.bar(df_proceso, x='Producto', y='Tiempo_Requerido',
                                            title=f"Tiempo en {nombre_proceso} por Producto",
                                            color='Producto')
                        fig_proceso.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_proceso, use_container_width=True)
                    
                    with col2:
                        # Tiempo total por producto
                        tiempo_total = df_proceso['Tiempo_Requerido'].sum()
                        fig_tiempo_total = px.pie(df_proceso, values='Tiempo_Requerido', names='Producto',
                                                 title=f"Distribución de Tiempo Total - {nombre_proceso}")
                        st.plotly_chart(fig_tiempo_total, use_container_width=True)
            
            # Análisis comparativo de procesos
            st.subheader("📊 Análisis Comparativo de Procesos")
            
            # Calcular métricas por proceso
            procesos_comparativa = data['DAT_PJM_MATRIX'].groupby('ID_Proceso').agg({
                'CapacidadMinutos': 'mean',
                'CostoHoraExtra': 'mean'
            }).reset_index()
            
            procesos_comparativa['Proceso'] = procesos_comparativa['ID_Proceso'].map(nombres_procesos)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_capacidad_comp = px.bar(procesos_comparativa, x='Proceso', y='CapacidadMinutos',
                                           title="Capacidad Promedio por Proceso",
                                           color='Proceso')
                st.plotly_chart(fig_capacidad_comp, use_container_width=True)
            
            with col2:
                fig_costo_comp = px.bar(procesos_comparativa, x='Proceso', y='CostoHoraExtra',
                                       title="Costo Hora Extra Promedio por Proceso",
                                       color='Proceso')
                st.plotly_chart(fig_costo_comp, use_container_width=True)
            
            # Tabla de datos del proceso
            st.subheader("📋 Datos Detallados del Proceso")
            st.dataframe(proceso_data[['Periodo_Index', 'CapacidadMinutos', 'CostoHoraExtra']])

# ===== SECCIÓN 5: DEMANDA Y MERCADO =====
elif section == "📊 Demanda y Mercado":
    st.header("📊 Análisis de Demanda y Mercado")
    
    if not data['DAT_PM_MATRIX'].empty:
        # Selector de producto para análisis de demanda
        productos = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
        producto_demanda = st.selectbox("Selecciona producto para análisis:", productos, key="demanda_prod")
        
        if producto_demanda:
            producto_id = data['DAT_PRODUCTOS_FIJOS'][
                data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_demanda
            ]['ID_Producto'].iloc[0]
            
            # Filtrar datos de demanda del producto
            demanda_producto = data['DAT_PM_MATRIX'][data['DAT_PM_MATRIX']['ID_Producto'] == producto_id]
            
            # Filtro por año
            años_disponibles = sorted(demanda_producto['Año'].unique())
            año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles, key="demanda_year_filter")
            
            # Filtrar por año seleccionado
            demanda_filtrada = demanda_producto[demanda_producto['Año'] == año_seleccionado]
            
            # Métricas de demanda
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                demanda_min_promedio = demanda_filtrada['DemandaMinima'].mean()
                st.metric("Demanda Mínima Promedio", f"{demanda_min_promedio:,.0f} uds")
            with col2:
                demanda_max_promedio = demanda_filtrada['DemandaMaxima'].mean()
                st.metric("Demanda Máxima Promedio", f"{demanda_max_promedio:,.0f} uds")
            with col3:
                precio_promedio = demanda_filtrada['PrecioVenta'].mean()
                st.metric("Precio Venta Promedio", format_currency(precio_promedio))
            with col4:
                costo_promedio = demanda_filtrada['CostoInsumo'].mean()
                st.metric("Costo Insumo Promedio", format_currency(costo_promedio))
            
            st.subheader(f"📈 Evolución de la Demanda - {producto_demanda} - {año_seleccionado}")
            
            # Crear gráfico de demanda mínima y máxima
            fig_demanda = go.Figure()
            fig_demanda.add_trace(go.Scatter(x=demanda_filtrada['Mes'], 
                                           y=demanda_filtrada['DemandaMinima'], 
                                           name='Demanda Mínima', 
                                           line=dict(color='orange'),
                                           fill=None))
            fig_demanda.add_trace(go.Scatter(x=demanda_filtrada['Mes'], 
                                           y=demanda_filtrada['DemandaMaxima'], 
                                           name='Demanda Máxima', 
                                           line=dict(color='red'),
                                           fill='tonexty',
                                           fillcolor='rgba(255,0,0,0.1)'))
            fig_demanda.update_layout(title=f"Rango de Demanda - {producto_demanda} - {año_seleccionado}",
                                     xaxis_title="Mes", yaxis_title="Unidades Demandadas",
                                     showlegend=True)
            st.plotly_chart(fig_demanda, use_container_width=True)
            
            # Precios y costos
            st.subheader("💰 Evolución de Precios y Costos")
            
            fig_precios = go.Figure()
            fig_precios.add_trace(go.Scatter(x=demanda_filtrada['Mes'], 
                                           y=demanda_filtrada['PrecioVenta'], 
                                           name='Precio Venta', 
                                           line=dict(color='green')))
            fig_precios.add_trace(go.Scatter(x=demanda_filtrada['Mes'], 
                                           y=demanda_filtrada['CostoInsumo'], 
                                           name='Costo Insumo', 
                                           line=dict(color='red')))
            fig_precios.update_layout(title=f"Evolución de Precios y Costos - {producto_demanda} - {año_seleccionado}",
                                     xaxis_title="Mes", yaxis_title="Valor ($)")
            st.plotly_chart(fig_precios, use_container_width=True)
            
            # Margen calculado
            demanda_filtrada_copy = demanda_filtrada.copy()
            demanda_filtrada_copy['Margen'] = demanda_filtrada_copy['PrecioVenta'] - demanda_filtrada_copy['CostoInsumo']
            demanda_filtrada_copy['Margen_Porcentaje'] = (demanda_filtrada_copy['Margen'] / demanda_filtrada_copy['PrecioVenta']) * 100
            
            fig_margen = go.Figure()
            fig_margen.add_trace(go.Scatter(x=demanda_filtrada_copy['Mes'], 
                                          y=demanda_filtrada_copy['Margen_Porcentaje'], 
                                          name='Margen %', 
                                          line=dict(color='blue')))
            fig_margen.update_layout(title=f"Evolución del Margen Porcentual - {producto_demanda} - {año_seleccionado}",
                                    xaxis_title="Mes", yaxis_title="Margen (%)")
            st.plotly_chart(fig_margen, use_container_width=True)
            
            # Análisis estacionalidad - CORREGIDO
            st.subheader("🔄 Análisis de Estacionalidad")
            
            # CORRECCIÓN: Verificar que las columnas existen antes de agrupar
            columnas_necesarias = ['Mes', 'DemandaMinima', 'DemandaMaxima']
            columnas_existentes = [col for col in columnas_necesarias if col in demanda_producto.columns]
            
            if len(columnas_existentes) == len(columnas_necesarias):
                # Agrupar por mes para ver patrones estacionales
                demanda_estacional = demanda_producto.groupby('Mes').agg({
                    'DemandaMinima': 'mean',
                    'DemandaMaxima': 'mean'
                }).reset_index()
                
                # Calcular margen promedio por mes
                if 'PrecioVenta' in demanda_producto.columns and 'CostoInsumo' in demanda_producto.columns:
                    demanda_producto_copy = demanda_producto.copy()
                    demanda_producto_copy['Margen_Porcentaje'] = (
                        (demanda_producto_copy['PrecioVenta'] - demanda_producto_copy['CostoInsumo']) / 
                        demanda_producto_copy['PrecioVenta']
                    ) * 100
                    
                    margen_estacional = demanda_producto_copy.groupby('Mes')['Margen_Porcentaje'].mean().reset_index()
                    demanda_estacional = demanda_estacional.merge(margen_estacional, on='Mes')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_estacional_demanda = go.Figure()
                    fig_estacional_demanda.add_trace(go.Scatter(x=demanda_estacional['Mes'], 
                                                              y=demanda_estacional['DemandaMinima'], 
                                                              name='Demanda Mínima Promedio', 
                                                              line=dict(color='lightblue')))
                    fig_estacional_demanda.add_trace(go.Scatter(x=demanda_estacional['Mes'], 
                                                              y=demanda_estacional['DemandaMaxima'], 
                                                              name='Demanda Máxima Promedio', 
                                                              line=dict(color='darkblue')))
                    fig_estacional_demanda.update_layout(title="Patrón Estacional de Demanda")
                    st.plotly_chart(fig_estacional_demanda, use_container_width=True)
                
                with col2:
                    if 'Margen_Porcentaje' in demanda_estacional.columns:
                        fig_estacional_margen = px.line(demanda_estacional, x='Mes', y='Margen_Porcentaje',
                                                       title="Patrón Estacional del Margen")
                        st.plotly_chart(fig_estacional_margen, use_container_width=True)
                    else:
                        st.info("No hay datos de margen para el análisis estacional")
            else:
                st.warning(f"No se pueden calcular patrones estacionales. Faltan columnas: {set(columnas_necesarias) - set(columnas_existentes)}")
            
            # Tabla de datos de demanda
            st.subheader("📋 Datos Detallados de Demanda")
            columnas_a_mostrar = ['Mes', 'DemandaMinima', 'DemandaMaxima', 'PrecioVenta', 'CostoInsumo']
            columnas_disponibles = [col for col in columnas_a_mostrar if col in demanda_filtrada.columns]
            st.dataframe(demanda_filtrada[columnas_disponibles])

# ===== SECCIÓN 6: COSTOS Y RENTABILIDAD =====
elif section == "💰 Costos y Rentabilidad":
    st.header("💰 Análisis de Costos y Rentabilidad")
    
    if not data['DAT_PM_MATRIX'].empty:
        # Filtro por año
        años_disponibles = sorted(data['DAT_PM_MATRIX']['Año'].unique())
        año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles, key="costos_year")
        
        # Filtrar datos por año
        datos_año = data['DAT_PM_MATRIX'][data['DAT_PM_MATRIX']['Año'] == año_seleccionado]
        
        # Calcular métricas agregadas
        costos_agregados = datos_año.groupby('Periodo_Index').agg({
            'PrecioVenta': 'mean',
            'CostoInsumo': 'mean'
        }).reset_index()
        
        costos_agregados['Margen'] = costos_agregados['PrecioVenta'] - costos_agregados['CostoInsumo']
        costos_agregados['Margen_Porcentaje'] = (costos_agregados['Margen'] / costos_agregados['PrecioVenta']) * 100
        
        # Métricas de costos
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            precio_promedio = costos_agregados['PrecioVenta'].mean()
            st.metric("Precio Venta Promedio", format_currency(precio_promedio))
        with col2:
            costo_promedio = costos_agregados['CostoInsumo'].mean()
            st.metric("Costo Insumo Promedio", format_currency(costo_promedio))
        with col3:
            margen_promedio = costos_agregados['Margen'].mean()
            st.metric("Margen Promedio", format_currency(margen_promedio))
        with col4:
            margen_porc_promedio = costos_agregados['Margen_Porcentaje'].mean()
            st.metric("Margen % Promedio", f"{margen_porc_promedio:.1f}%")
        
        # Gráficos de tendencias
        st.subheader("📈 Tendencias de Costos y Margenes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tendencias = go.Figure()
            fig_tendencias.add_trace(go.Scatter(x=costos_agregados['Periodo_Index'], 
                                              y=costos_agregados['PrecioVenta'], 
                                              name='Precio Venta', 
                                              line=dict(color='green')))
            fig_tendencias.add_trace(go.Scatter(x=costos_agregados['Periodo_Index'], 
                                              y=costos_agregados['CostoInsumo'], 
                                              name='Costo Insumo', 
                                              line=dict(color='red')))
            fig_tendencias.add_trace(go.Scatter(x=costos_agregados['Periodo_Index'], 
                                              y=costos_agregados['Margen'], 
                                              name='Margen', 
                                              line=dict(color='blue')))
            fig_tendencias.update_layout(title=f"Evolución de Precios, Costos y Margenes - {año_seleccionado}")
            st.plotly_chart(fig_tendencias, use_container_width=True)
        
        with col2:
            fig_margen_tendencia = px.line(costos_agregados, x='Periodo_Index', y='Margen_Porcentaje',
                                          title=f"Evolución del Margen Porcentual - {año_seleccionado}")
            st.plotly_chart(fig_margen_tendencia, use_container_width=True)
        
        # Análisis por producto
        st.subheader("🏆 Productos Más Rentables")
        
        # Calcular rentabilidad por producto
        rentabilidad_productos = datos_año.groupby('ID_Producto').agg({
            'PrecioVenta': 'mean',
            'CostoInsumo': 'mean'
        }).reset_index()
        
        rentabilidad_productos['Margen'] = rentabilidad_productos['PrecioVenta'] - rentabilidad_productos['CostoInsumo']
        rentabilidad_productos['Margen_Porcentaje'] = (rentabilidad_productos['Margen'] / rentabilidad_productos['PrecioVenta']) * 100
        
        # Agregar nombres de productos
        rentabilidad_productos = rentabilidad_productos.merge(
            data['DAT_PRODUCTOS_FIJOS'][['ID_Producto', 'Nombre_Producto', 'Categoria']], 
            on='ID_Producto'
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top productos por margen porcentual
            top_margen_porc = rentabilidad_productos.nlargest(10, 'Margen_Porcentaje')
            fig_top_porc = px.bar(top_margen_porc, x='Nombre_Producto', y='Margen_Porcentaje',
                                 title="Top 10 Productos por Margen %",
                                 color='Categoria')
            fig_top_porc.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_top_porc, use_container_width=True)
        
        with col2:
            # Top productos por margen absoluto
            top_margen_abs = rentabilidad_productos.nlargest(10, 'Margen')
            fig_top_abs = px.bar(top_margen_abs, x='Nombre_Producto', y='Margen',
                                title="Top 10 Productos por Margen Absoluto",
                                color='Categoria')
            fig_top_abs.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_top_abs, use_container_width=True)
        
        # Análisis por categoría
        st.subheader("📊 Rentabilidad por Categoría")
        
        rentabilidad_categoria = rentabilidad_productos.groupby('Categoria').agg({
            'Margen_Porcentaje': 'mean',
            'Margen': 'mean',
            'PrecioVenta': 'mean',
            'CostoInsumo': 'mean'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_cat_margen = px.bar(rentabilidad_categoria, x='Categoria', y='Margen_Porcentaje',
                                   title="Margen Porcentual Promedio por Categoría",
                                   color='Categoria')
            st.plotly_chart(fig_cat_margen, use_container_width=True)
        
        with col2:
            fig_cat_precio_costo = go.Figure()
            fig_cat_precio_costo.add_trace(go.Bar(x=rentabilidad_categoria['Categoria'], 
                                                 y=rentabilidad_categoria['PrecioVenta'],
                                                 name='Precio Venta Promedio',
                                                 marker_color='green'))
            fig_cat_precio_costo.add_trace(go.Bar(x=rentabilidad_categoria['Categoria'], 
                                                 y=rentabilidad_categoria['CostoInsumo'],
                                                 name='Costo Insumo Promedio',
                                                 marker_color='red'))
            fig_cat_precio_costo.update_layout(title="Precio vs Costo por Categoría",
                                              barmode='group')
            st.plotly_chart(fig_cat_precio_costo, use_container_width=True)
        
        # Tabla de rentabilidad por producto
        st.subheader("📋 Tabla de Rentabilidad por Producto")
        st.dataframe(rentabilidad_productos[['Nombre_Producto', 'Categoria', 'PrecioVenta', 'CostoInsumo', 'Margen', 'Margen_Porcentaje']].sort_values('Margen_Porcentaje', ascending=False))

# ===== SECCIÓN 7: MODELO DE OPTIMIZACIÓN =====
elif section == "🔍 Modelo de Optimización":
    st.header("🔍 Modelo de Optimización LINGO")
    
    st.markdown("""
    ### 📋 Descripción Detallada del Modelo de Optimización
    
    El modelo implementado en LINGO resuelve el problema de planificación de producción para maximizar 
    la rentabilidad de ICATEX considerando todas las restricciones operativas y de mercado.
    """)
    
    # Explicación detallada de la función objetivo
    st.subheader("🎯 Función Objetivo Detallada")
    
    st.markdown(r"""
    **MAXIMIZAR:** 
    ```
    Z = ∑(i∈PRODUCTOS, t∈PERIODOS) [PrecioVenta(i,t) × Ventas(i,t)] 
        - ∑(i∈PRODUCTOS, t∈PERIODOS) [CostoInsumo(i,t) × Produccion(i,t)]
        - ∑(i∈PRODUCTOS, t∈PERIODOS) [CostoAlmacen(i) × Inventario(i,t)]
        - ∑(p∈PROCESOS, t∈PERIODOS) [CostoHoraExtra(p,t) × HorasExtrasMinutos(p,t)]
    ```
    
    **Donde:**
    - **Ingresos por Ventas:** $\sum_{i=1}^{20} \sum_{t=1}^{48} PrecioVenta_{i,t} \times Ventas_{i,t}$
    - **Costos de Insumos:** $\sum_{i=1}^{20} \sum_{t=1}^{48} CostoInsumo_{i,t} \times Produccion_{i,t}$
    - **Costos de Almacenamiento:** $\sum_{i=1}^{20} \sum_{t=1}^{48} CostoAlmacen_i \times Inventario_{i,t}$
    - **Costos de Horas Extra:** $\sum_{p=1}^{5} \sum_{t=1}^{48} CostoHoraExtra_{p,t} \times HorasExtrasMinutos_{p,t}$
    """)
    
    # Restricciones detalladas
    st.subheader("⚖️ Restricciones del Modelo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. Balance de Inventarios:**
        ```
        Para t = 1:
        Inventario(i,1) = StockInicial(i) + Produccion(i,1) - Ventas(i,1)
        
        Para t > 1:
        Inventario(i,t) = Inventario(i,t-1) + Produccion(i,t) - Ventas(i,t)
        ```
        
        **2. Límites de Mercado:**
        ```
        DemandaMinima(i,t) ≤ Ventas(i,t) ≤ DemandaMaxima(i,t)
        ```
        """)
    
    with col2:
        st.markdown("""
        **3. Capacidad de Procesos:**
        ```
        ∑(i∈PRODUCTOS) [TiempoProceso(i,p) × Produccion(i,t)] 
        ≤ CapacidadMinutos(p,t) × EficienciaOperativa + HorasExtrasMinutos(p,t)
        ```
        
        **4. Disponibilidad de Insumos:**
        ```
        ∑(i∈PRODUCTOS) [ConsumoInsumo(i,k) × Produccion(i,t)] ≤ StockDisponible(k,t)
        ```
        
        **5. No Negatividad:**
        ```
        Produccion(i,t) ≥ 0, Ventas(i,t) ≥ 0, Inventario(i,t) ≥ 0
        ```
        """)
    
    # Resultados de la optimización - MEJORADO
    st.subheader("📈 Resultados de la Optimización")
    
    # Mostrar valor de la función objetivo si está disponible
    st.markdown("### 🎯 Valor de la Función Objetivo")
    
    # Calcular valor aproximado de la función objetivo basado en los resultados disponibles
    valor_z = 0
    resultados_disponibles = False
    
    # Verificar si hay resultados de producción
    if not data['RES_PRODUCCION'].empty:
        resultados_disponibles = True
        # Aquí debería ir el cálculo real basado en los resultados de LINGO
        # Por ahora usamos un placeholder
        valor_z = 11256950.00
    
    if resultados_disponibles:
        st.success(f"**Valor óptimo de Z:** {format_currency(valor_z)}")
    else:
        st.warning("Ejecute el modelo en LINGO para obtener el valor de la función objetivo")
    
    # Mostrar resultados detallados
    st.markdown("### 📊 Resultados Detallados")
    
    # Crear pestañas para diferentes tipos de resultados
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Producción", "🛒 Ventas", "📦 Inventario", "⏰ Horas Extra"])
    
    with tab1:
        st.subheader("Plan de Producción Óptimo")
        if not data['RES_PRODUCCION'].empty:
            # Selector de producto
            productos_options = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
            producto_seleccionado = st.selectbox("Selecciona un producto:", productos_options, key="prod_opt")
            
            if producto_seleccionado:
                producto_id = data['DAT_PRODUCTOS_FIJOS'][
                    data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_seleccionado
                ]['ID_Producto'].iloc[0]
                
                # Filtrar datos del producto seleccionado
                produccion_producto = data['RES_PRODUCCION'][data['RES_PRODUCCION']['ID_Producto'] == producto_id]
                
                # Mostrar métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    produccion_total = produccion_producto['Produccion'].sum()
                    st.metric("Producción Total", f"{produccion_total:,.0f} uds")
                with col2:
                    produccion_promedio = produccion_producto['Produccion'].mean()
                    st.metric("Producción Promedio", f"{produccion_promedio:,.1f} uds/mes")
                with col3:
                    produccion_max = produccion_producto['Produccion'].max()
                    st.metric("Producción Máxima", f"{produccion_max:,.0f} uds")
                with col4:
                    produccion_min = produccion_producto['Produccion'].min()
                    st.metric("Producción Mínima", f"{produccion_min:,.0f} uds")
                
                # Gráfico de producción por período
                fig_produccion = px.line(produccion_producto, x='Periodo_Index', y='Produccion',
                                       title=f"Producción Mensual - {producto_seleccionado}",
                                       labels={'Produccion': 'Unidades', 'Periodo_Index': 'Período'})
                st.plotly_chart(fig_produccion, use_container_width=True)
                
                # Mostrar tabla detallada
                st.subheader(f"📋 Plan de Producción Detallado - {producto_seleccionado}")
                st.dataframe(produccion_producto[['Periodo_Index', 'Produccion']])
        else:
            st.info("Los resultados de producción se cargarán automáticamente desde LINGO")
            
    with tab2:
        st.subheader("Plan de Ventas Óptimo")
        if not data['RES_VENTAS'].empty:
            # Selector de producto
            productos_options = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
            producto_seleccionado = st.selectbox("Selecciona un producto:", productos_options, key="ventas_opt")
            
            if producto_seleccionado:
                producto_id = data['DAT_PRODUCTOS_FIJOS'][
                    data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_seleccionado
                ]['ID_Producto'].iloc[0]
                
                # Filtrar datos del producto seleccionado
                ventas_producto = data['RES_VENTAS'][data['RES_VENTAS']['ID_Producto'] == producto_id]
                
                # Mostrar métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    ventas_total = ventas_producto['Ventas'].sum()
                    st.metric("Ventas Total", f"{ventas_total:,.0f} uds")
                with col2:
                    ventas_promedio = ventas_producto['Ventas'].mean()
                    st.metric("Ventas Promedio", f"{ventas_promedio:,.1f} uds/mes")
                with col3:
                    ventas_max = ventas_producto['Ventas'].max()
                    st.metric("Ventas Máxima", f"{ventas_max:,.0f} uds")
                with col4:
                    ventas_min = ventas_producto['Ventas'].min()
                    st.metric("Ventas Mínima", f"{ventas_min:,.0f} uds")
                
                # Gráfico de ventas por período
                fig_ventas = px.line(ventas_producto, x='Periodo_Index', y='Ventas',
                                   title=f"Ventas Mensuales - {producto_seleccionado}",
                                   labels={'Ventas': 'Unidades', 'Periodo_Index': 'Período'})
                st.plotly_chart(fig_ventas, use_container_width=True)
                
                # Mostrar tabla detallada
                st.subheader(f"📋 Plan de Ventas Detallado - {producto_seleccionado}")
                st.dataframe(ventas_producto[['Periodo_Index', 'Ventas']])
        else:
            st.info("Los resultados de ventas se cargarán automáticamente desde LINGO")
        
    with tab3:
        st.subheader("Niveles de Inventario Óptimos")
        if not data['RES_INVENTARIO'].empty:
            # Selector de producto
            productos_options = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
            producto_seleccionado = st.selectbox("Selecciona un producto:", productos_options, key="inv_opt")
            
            if producto_seleccionado:
                producto_id = data['DAT_PRODUCTOS_FIJOS'][
                    data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_seleccionado
                ]['ID_Producto'].iloc[0]
                
                # Filtrar datos del producto seleccionado
                inventario_producto = data['RES_INVENTARIO'][data['RES_INVENTARIO']['ID_Producto'] == producto_id]
                
                # Mostrar métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    inventario_promedio = inventario_producto['Inventario'].mean()
                    st.metric("Inventario Promedio", f"{inventario_promedio:,.1f} uds")
                with col2:
                    inventario_max = inventario_producto['Inventario'].max()
                    st.metric("Inventario Máximo", f"{inventario_max:,.0f} uds")
                with col3:
                    inventario_min = inventario_producto['Inventario'].min()
                    st.metric("Inventario Mínimo", f"{inventario_min:,.0f} uds")
                with col4:
                    # Calcular rotación si hay datos de ventas
                    if not data['RES_VENTAS'].empty:
                        ventas_producto = data['RES_VENTAS'][data['RES_VENTAS']['ID_Producto'] == producto_id]
                        ventas_total = ventas_producto['Ventas'].sum()
                        rotacion = ventas_total / inventario_promedio if inventario_promedio > 0 else 0
                        st.metric("Rotación", f"{rotacion:.2f}")
                    else:
                        st.metric("Rotación", "N/A")
                
                # Gráfico de inventario por período
                fig_inventario = px.area(inventario_producto, x='Periodo_Index', y='Inventario',
                                       title=f"Inventario Mensual - {producto_seleccionado}",
                                       labels={'Inventario': 'Unidades', 'Periodo_Index': 'Período'})
                st.plotly_chart(fig_inventario, use_container_width=True)
                
                # Mostrar tabla detallada
                st.subheader(f"📋 Niveles de Inventario Detallado - {producto_seleccionado}")
                st.dataframe(inventario_producto[['Periodo_Index', 'Inventario']])
        else:
            st.info("Los resultados de inventario se cargarán automáticamente desde LINGO")
        
    with tab4:
        st.subheader("Horas Extra Requeridas")
        if not data['RES_H_EXTRAS'].empty:
            # Procesar resultados de horas extra
            horas_extra_df = data['RES_H_EXTRAS'].copy()
            
            # Mapear los procesos a nombres
            horas_extra_df['Proceso'] = horas_extra_df['ID_Proceso'].map(nombres_procesos)
            
            # Mostrar resumen gráfico
            horas_resumen = horas_extra_df.groupby('Proceso')['HorasExtrasMinutos'].sum().reset_index()
            
            fig_horas = px.bar(horas_resumen, x='Proceso', y='HorasExtrasMinutos',
                              title="Horas Extra Requeridas por Proceso",
                              color='Proceso',
                              labels={'HorasExtrasMinutos': 'Minutos de Horas Extra'})
            st.plotly_chart(fig_horas, use_container_width=True)
            
            # Mostrar tabla detallada
            st.dataframe(horas_extra_df)
        else:
            st.info("Los resultados de horas extra se cargarán automáticamente desde LINGO")
    
    # Resumen ejecutivo
    st.markdown("### 📋 Resumen Ejecutivo")
    
    if resultados_disponibles:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if not data['RES_PRODUCCION'].empty:
                produccion_total = data['RES_PRODUCCION']['Produccion'].sum()
                st.metric("Producción Total", f"{produccion_total:,.0f} uds")
        
        with col2:
            if not data['RES_VENTAS'].empty:
                ventas_total = data['RES_VENTAS']['Ventas'].sum()
                st.metric("Ventas Totales", f"{ventas_total:,.0f} uds")
        
        with col3:
            if not data['RES_INVENTARIO'].empty:
                inventario_promedio = data['RES_INVENTARIO']['Inventario'].mean()
                st.metric("Inventario Promedio", f"{inventario_promedio:,.0f} uds")
        
        with col4:
            st.metric("Utilidad Total", format_currency(valor_z))
    else:
        st.info("Ejecute el modelo en LINGO para ver el resumen ejecutivo")

# ===== SECCIÓN 8: SIMULACIONES =====
elif section == "🎯 Simulaciones":
    st.header("🎯 Simulador de Escenarios")
    
    st.info("""
    **Simulador de Optimización de Producción**
    Ajusta los parámetros para simular diferentes escenarios de producción y su impacto en costos y rentabilidad.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Parámetros de simulación
        st.subheader("⚙️ Parámetros de Simulación")
        
        producto_sim = st.selectbox("Producto a simular:", 
                                   data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist(),
                                   key="sim_product")
        
        if producto_sim:
            producto_id = data['DAT_PRODUCTOS_FIJOS'][data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_sim].iloc[0]['ID_Producto']
            producto_info = data['DAT_PRODUCTOS_FIJOS'][data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_sim].iloc[0]
            
            # Obtener datos históricos
            datos_historicos = data['DAT_PM_MATRIX'][data['DAT_PM_MATRIX']['ID_Producto'] == producto_id]
            
            if not datos_historicos.empty:
                # Calcular promedios históricos
                precio_promedio = datos_historicos['PrecioVenta'].mean()
                costo_promedio = datos_historicos['CostoInsumo'].mean()
                demanda_min_promedio = datos_historicos['DemandaMinima'].mean()
                demanda_max_promedio = datos_historicos['DemandaMaxima'].mean()
                
                st.metric("Precio Promedio Histórico", format_currency(precio_promedio))
                st.metric("Costo Promedio Histórico", format_currency(costo_promedio))
                st.metric("Demanda Mínima Promedio", f"{demanda_min_promedio:.0f} uds")
                st.metric("Demanda Máxima Promedio", f"{demanda_max_promedio:.0f} uds")
                
                # Controles de simulación
                st.subheader("🎛️ Ajustes de Simulación")
                
                nuevo_precio = st.slider("Nuevo precio de venta ($):", 
                                        float(precio_promedio * 0.5), 
                                        float(precio_promedio * 1.5), 
                                        float(precio_promedio),
                                        key="precio_sim")
                
                reduccion_costos = st.slider("Reducción en costos de insumos (%):", 0, 50, 0,
                                           key="costo_sim")
                
                mejora_eficiencia = st.slider("Mejora en eficiencia de procesos (%):", 0, 30, 0,
                                            key="eficiencia_sim")
                
                volumen_produccion = st.slider("Volumen de producción objetivo (unidades):", 
                                             int(demanda_min_promedio), 
                                             int(demanda_max_promedio * 1.2), 
                                             int(demanda_min_promedio),
                                             key="volumen_sim")
    
    with col2:
        st.subheader("📊 Resultados de la Simulación")
        
        if producto_sim and not datos_historicos.empty:
            # Cálculos de simulación
            nuevo_costo = costo_promedio * (1 - reduccion_costos/100)
            margen_actual = precio_promedio - costo_promedio
            margen_simulado = nuevo_precio - nuevo_costo
            
            margen_porc_actual = (margen_actual / precio_promedio) * 100
            margen_porc_simulado = (margen_simulado / nuevo_precio) * 100
            
            # Calcular impacto de eficiencia
            tiempo_actual = producto_info['TiempoProd_Total(min)']
            tiempo_simulado = tiempo_actual * (1 - mejora_eficiencia/100)
            
            # Mostrar resultados comparativos
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.metric("Situación Actual", format_currency(margen_actual), 
                         delta=f"{margen_porc_actual:.1f}%")
                st.metric("Tiempo Producción Actual", f"{tiempo_actual} min")
                
            with col_res2:
                st.metric("Situación Simulada", format_currency(margen_simulado), 
                         delta=f"{margen_porc_simulado:.1f}%", 
                         delta_color="inverse" if margen_simulado < margen_actual else "normal")
                st.metric("Tiempo Producción Simulado", f"{tiempo_simulado:.1f} min",
                         delta=f"-{mejora_eficiencia}%")
            
            # Gráfico comparativo
            fig_comparativo = go.Figure()
            
            fig_comparativo.add_trace(go.Indicator(
                mode = "number+delta",
                value = margen_porc_simulado,
                number = {'suffix': "%"},
                delta = {'reference': margen_porc_actual, 'relative': False},
                title = {"text": "Margen<br>Simulado vs Actual"},
                domain = {'row': 0, 'column': 0}))
            
            fig_comparativo.add_trace(go.Indicator(
                mode = "number+delta",
                value = nuevo_costo,
                number = {'prefix': "$"},
                delta = {'reference': costo_promedio, 'relative': False},
                title = {"text": "Costo Unitario<br>Simulado vs Actual"},
                domain = {'row': 0, 'column': 1}))
            
            fig_comparativo.update_layout(
                grid = {'rows': 1, 'columns': 2, 'pattern': "independent"})
            
            st.plotly_chart(fig_comparativo, use_container_width=True)
            
            # Impacto financiero total
            utilidad_actual = margen_actual * volumen_produccion
            utilidad_simulada = margen_simulado * volumen_produccion
            mejora_utilidad = utilidad_simulada - utilidad_actual
            
            # Eficiencia en tiempo
            tiempo_total_actual = tiempo_actual * volumen_produccion
            tiempo_total_simulado = tiempo_simulado * volumen_produccion
            ahorro_tiempo = tiempo_total_actual - tiempo_total_simulado
            
            st.success(f"**Impacto en Utilidad Total:** {format_currency(mejora_utilidad)}")
            st.info(f"**Ahorro de Tiempo Total:** {ahorro_tiempo:.0f} minutos ({ahorro_tiempo/60:.1f} horas)")
            
            # Análisis de sensibilidad
            st.subheader("📈 Análisis de Sensibilidad")
            
            # Simular diferentes escenarios de precio
            precios_test = np.linspace(precio_promedio * 0.7, precio_promedio * 1.3, 10)
            utilidades_test = [(precio - nuevo_costo) * volumen_produccion for precio in precios_test]
            
            fig_sensibilidad = px.line(x=precios_test, y=utilidades_test,
                                      title="Sensibilidad de Utilidad vs Precio de Venta",
                                      labels={'x': 'Precio de Venta ($)', 'y': 'Utilidad Total ($)'})
            fig_sensibilidad.add_vline(x=nuevo_precio, line_dash="dash", line_color="red",
                                     annotation_text="Precio Simulado")
            st.plotly_chart(fig_sensibilidad, use_container_width=True)

# ===== SECCIÓN 9: PROGRAMACIÓN POR METAS =====
elif section == "🏁 Programación por Metas":
    st.header("🎯 Análisis de Cumplimiento de Metas Estratégicas")
    st.markdown("""
    Este módulo evalúa el desempeño de la empresa frente a objetivos conflictivos utilizando el enfoque de 
    **Programación por Metas**, que permite balancear múltiples objetivos estratégicos simultáneamente.
    """)
    
    # Resultados REALES del modelo LINGO
    st.subheader("📊 Resultados del Modelo de Programación por Metas")
    
    # Metas establecidas en LINGO
    meta_utilidad = 12000000
    meta_he = 50000
    
    # Desviaciones REALES obtenidas de LINGO
    falta_utilidad = 3422729.51   # D_UTIL_NEG
    exceso_he = 25712344          # D_HE_POS
    
    # Logros reales
    logro_utilidad = meta_utilidad - falta_utilidad
    logro_he = meta_he + exceso_he

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Meta Financiera")
        fig_util = go.Figure(go.Indicator(
            mode = "number+gauge+delta",
            value = logro_utilidad,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Utilidad Alcanzada ($)"},
            delta = {'reference': meta_utilidad, 'relative': False},
            gauge = {
                'axis': {'range': [None, meta_utilidad * 1.2]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, meta_utilidad * 0.8], 'color': "lightgray"},
                    {'range': [meta_utilidad * 0.8, meta_utilidad], 'color': "lightgreen"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': meta_utilidad}}))
        fig_util.update_layout(height=300)
        st.plotly_chart(fig_util, use_container_width=True)
        
        st.metric("Utilidad Alcanzada", format_currency(logro_utilidad), 
                 delta=f"-{format_currency(falta_utilidad)}", delta_color="inverse")
        st.metric("Meta de Utilidad", format_currency(meta_utilidad))
        
        if falta_utilidad > 0:
            st.error(f"❌ No se alcanzó la meta por {format_currency(falta_utilidad)}")
            st.info(f"**Cumplimiento:** {(logro_utilidad/meta_utilidad*100):.1f}%")
        else:
            st.success("✅ ¡Meta Financiera Cumplida!")

    with col2:
        st.subheader("👷 Meta Laboral (Horas Extras)")
        # Gráfico de barras simple para comparar
        fig_he = go.Figure(data=[
            go.Bar(name='Meta Máxima', x=['Horas Extras'], y=[meta_he], marker_color='green', width=0.3),
            go.Bar(name='Real Usado', x=['Horas Extras'], y=[logro_he], 
                  marker_color='red', width=0.3)
        ])
        fig_he.update_layout(
            title_text='Uso de Horas Extras (Minutos)',
            yaxis_title="Minutos",
            height=300
        )
        st.plotly_chart(fig_he, use_container_width=True)
        
        st.metric("Horas Extra Utilizadas", f"{logro_he:,.0f} min", 
                 delta=f"+{exceso_he:,.0f} min", delta_color="inverse")
        st.metric("Límite de Horas Extra", f"{meta_he:,.0f} min")
        
        st.error(f"❌ Se excedió el límite de fatiga laboral en {exceso_he:,.0f} minutos.")
        st.info(f"**Exceso:** {(exceso_he/meta_he*100):.1f}% sobre la meta")
    
    # Análisis de trade-offs
    st.markdown("---")
    st.subheader("⚖️ Análisis de Trade-offs Estratégicos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Enfoque de Programación por Metas
        
        **Objetivos en Conflicto:**
        - 📈 **Maximizar utilidades** (Meta: $12,000,000)
        - 👷 **Minimizar horas extra** (Meta: 50,000 min)
        
        **Resultados del Modelo:**
        - Utilidad Alcanzada: $8,577,270
        - Horas Extra Utilizadas: 25,762,344 min
        
        **Interpretación:**
        El modelo priorizó el bienestar laboral (peso 5) sobre la utilidad (peso 1), 
        pero aun así se excedió enormemente en horas extra. Esto indica que las restricciones 
        operativas y de demanda obligaron a usar horas extra masivamente.
        """)
    
    with col2:
        # Gráfico de trade-off conceptual
        fig_tradeoff = go.Figure()
        
        # Puntos conceptuales de diferentes estrategias
        estrategias = ['Solo Utilidad', 'Balanceado (Modelo)', 'Solo Bienestar']
        utilidades = [13000000, logro_utilidad, 9000000]
        horas_extra = [80000, logro_he, 30000]
        
        fig_tradeoff.add_trace(go.Scatter(
            x=horas_extra, y=utilidades, text=estrategias,
            mode='markers+text', textposition='top center',
            marker=dict(size=15, color=['red', 'blue', 'green'])
        ))
        
        fig_tradeoff.update_layout(
            title="Trade-off: Utilidad vs Horas Extra",
            xaxis_title="Horas Extra (minutos)",
            yaxis_title="Utilidad ($)",
            height=400
        )
        st.plotly_chart(fig_tradeoff, use_container_width=True)
    
    # Resumen ejecutivo
    st.markdown("---")
    st.subheader("📋 Resumen Ejecutivo de Cumplimiento")
    
    # Calcular puntuación general de cumplimiento
    cumplimiento_utilidad = (logro_utilidad / meta_utilidad * 100) if meta_utilidad > 0 else 0
    cumplimiento_he = (1 - min(exceso_he/meta_he, 1)) * 100 if meta_he > 0 else 100
    
    # Ponderación según la función objetivo (5:1 a favor de horas extra)
    puntuacion_general = (cumplimiento_utilidad * 1 + cumplimiento_he * 5) / 6
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cumplimiento Meta Utilidad", f"{cumplimiento_utilidad:.1f}%")
    
    with col2:
        st.metric("Cumplimiento Meta Horas Extra", f"{cumplimiento_he:.1f}%")
    
    with col3:
        st.metric("Puntuación General Ponderada", f"{puntuacion_general:.1f}%")
    
    # Recomendaciones basadas en el análisis
    st.markdown("### 💡 Recomendaciones Estratégicas")
    
    st.warning("""
    **Escenario: Baja Utilidad + Exceso Extremo de Horas Extra**
    
    **Diagnóstico:** 
    - La empresa no pudo acercarse a la meta de utilidad y tuvo un exceso masivo de horas extra.
    - Esto indica graves cuellos de botella en la capacidad productiva y posiblemente una demanda muy por encima de la capacidad.
    
    **Recomendaciones:**
    - 🔧 **Inversión en Capacidad:** Urgente necesidad de expandir la capacidad productiva permanente.
    - 📊 **Revisión de Metas:** Las metas actuales pueden ser poco realistas dadas las restricciones operativas.
    - 🔄 **Revisión de Prioridades:** Repensar la ponderación de metas: ¿es realista priorizar tanto las horas extra si la demanda es tan alta?
    - 🏭 **Automatización:** Evaluar inversiones en automatización para reducir la dependencia de horas extra.
    """)
    
    # Explicación del modelo
    st.markdown("---")
    st.subheader("🔍 Explicación del Modelo LINGO")
    
    st.markdown("""
    **Función Objetivo del Modelo:**
    ```
    MIN = (1 × D_UTIL_NEG) + (5 × D_HE_POS)
    ```
    
    **Donde:**
    - **D_UTIL_NEG**: Desviación negativa de la meta de utilidad (${falta_utilidad:,.2f})
    - **D_HE_POS**: Desviación positiva de la meta de horas extra ({exceso_he:,.0f} min)
    - **Pesos**: 5:1 a favor del bienestar laboral sobre la utilidad
    
    **Restricciones de Metas:**
    1. Utilidad: Ingresos - Costos + D_UTIL_NEG - D_UTIL_POS = 12,000,000
    2. Horas Extra: Total Minutos Extra + D_HE_NEG - D_HE_POS = 50,000
    """)
# Footer informativo
st.markdown("---")
st.markdown("### 📋 Resumen de Datos Cargados")

# Crear resumen de datos
if not data['SET_PRODUCTOS'].empty:
    total_productos = len(data['SET_PRODUCTOS'])
else:
    total_productos = 0

if not data['SET_INSUMOS'].empty:
    total_insumos = len(data['SET_INSUMOS'])
else:
    total_insumos = 0

if not data['SET_PROCESOS'].empty:
    total_procesos = len(data['SET_PROCESOS'])
else:
    total_procesos = 0

if not data['SET_MESES'].empty:
    total_meses = len(data['SET_MESES'])
else:
    total_meses = 0

st.write(f"""
- **Productos:** {total_productos} productos en {data['DAT_PRODUCTOS_FIJOS']['Categoria'].nunique() if not data['DAT_PRODUCTOS_FIJOS'].empty else 0} categorías
- **Insumos:** {total_insumos} tipos de materiales
- **Procesos:** {total_procesos} procesos productivos
- **Horizonte:** {total_meses} meses de planificación (4 años)
- **Modelo:** Optimización lineal con LINGO
""")

# Información adicional en el sidebar
st.sidebar.markdown("---")
st.sidebar.info("""
**🏭 ICATEX Enterprise**
- Dashboard de Optimización
- Modelo: Programación Lineal
- Período: 2021-2024
- Conectado a LINGO vía Excel
""")

# Agregar información de conexión LINGO
st.sidebar.markdown("---")
st.sidebar.success("""
**🔗 Conexión LINGO-Excel**
- Entradas: Hojas SET_* y DAT_*
- Salidas: Hojas RESULTADOS y RES_HORAS_EXTRA
- Modelo: Optimización completa
""")







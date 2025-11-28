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
@st.cache_data
def load_data():
    file_path = "ICATEX_Lingo_4Anios.xlsx"
    
    data = {}
    sheets = [
        'SET_PRODUCTOS', 'SET_MESES', 'SET_INSUMOS', 'SET_PROCESOS',
        'DAT_PI_MATRIX', 'DAT_PP_MATRIX', 'DAT_PM_MATRIX', 'DAT_PJM_MATRIX',
        'DAT_KM_MATRIX', 'DAT_PRODUCTOS_FIJOS', 'RESULTADOS', 'RES_HORAS_EXTRA'
    ]
    
    for sheet in sheets:
        try:
            data[sheet] = pd.read_excel(file_path, sheet_name=sheet)
        except Exception as e:
            st.warning(f"No se pudo cargar la hoja {sheet}: {e}")
            data[sheet] = pd.DataFrame()
    
    return data

# Cargar los datos
data = load_data()

# Sidebar para navegación
st.sidebar.title("📊 Navegación")
section = st.sidebar.radio(
    "Selecciona una sección:",
    ["📈 Resumen General", "👕 Productos", "📦 Insumos", "⚙️ Procesos", 
     "📊 Demanda y Mercado", "💰 Costos y Rentabilidad", "🔍 Modelo de Optimización"]
)

# Función para formatear números
def format_currency(value):
    return f"$ {value:.2f}"

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
        st.subheader("📦 Información de Productos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por categoría
            cat_dist = data['DAT_PRODUCTOS_FIJOS']['Categoria'].value_counts()
            fig_cat = px.pie(values=cat_dist.values, names=cat_dist.index, 
                            title="Productos por Categoría")
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Distribución por línea
            linea_dist = data['DAT_PRODUCTOS_FIJOS']['Linea'].value_counts()
            fig_linea = px.bar(x=linea_dist.index, y=linea_dist.values,
                              title="Productos por Línea")
            st.plotly_chart(fig_linea, use_container_width=True)
        
        # Tiempos de producción
        st.subheader("⏱️ Tiempos de Producción")
        fig_tiempos = px.box(data['DAT_PRODUCTOS_FIJOS'], y='TiempoProd_Total(min)', 
                            title="Distribución de Tiempos de Producción Total")
        st.plotly_chart(fig_tiempos, use_container_width=True)

# ===== SECCIÓN 2: PRODUCTOS =====
elif section == "👕 Productos":
    st.header("👕 Análisis de Productos")
    
    if not data['DAT_PRODUCTOS_FIJOS'].empty:
        # Selector de producto
        productos = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
        producto_seleccionado = st.selectbox("Selecciona un producto:", productos)
        
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
                        if insumos_producto[col].iloc[0] > 0:
                            insumos_data.append({
                                'Insumo': col,
                                'Cantidad': insumos_producto[col].iloc[0]
                            })
                    
                    if insumos_data:
                        df_insumos = pd.DataFrame(insumos_data)
                        fig_insumos = px.bar(df_insumos, x='Insumo', y='Cantidad',
                                            title=f"Insumos para {producto_seleccionado}")
                        st.plotly_chart(fig_insumos, use_container_width=True)
            
            # Tiempos por proceso
            st.subheader("⚙️ Tiempos por Proceso")
            if not data['DAT_PP_MATRIX'].empty:
                tiempos_proceso = data['DAT_PP_MATRIX'][data['DAT_PP_MATRIX']['ID_Producto'] == producto_id]
                
                if not tiempos_proceso.empty:
                    # Transformar datos para visualización
                    procesos_data = []
                    for col in tiempos_proceso.columns[1:]:  # Excluir ID_Producto
                        procesos_data.append({
                            'Proceso': col,
                            'Tiempo_Minutos': tiempos_proceso[col].iloc[0]
                        })
                    
                    df_procesos = pd.DataFrame(procesos_data)
                    fig_procesos = px.bar(df_procesos, x='Proceso', y='Tiempo_Minutos',
                                         title=f"Tiempos de Proceso para {producto_seleccionado}")
                    st.plotly_chart(fig_procesos, use_container_width=True)

# ===== SECCIÓN 3: INSUMOS =====
elif section == "📦 Insumos":
    st.header("📦 Gestión de Insumos")
    
    if not data['DAT_KM_MATRIX'].empty:
        # Selector de insumo
        insumos = data['SET_INSUMOS']['ID_Insumo'].tolist()
        insumo_seleccionado = st.selectbox("Selecciona un insumo:", insumos)
        
        if insumo_seleccionado:
            # Filtrar datos del insumo seleccionado
            insumo_data = data['DAT_KM_MATRIX'][data['DAT_KM_MATRIX']['ID_Insumo'] == insumo_seleccionado]
            
            st.subheader(f"📊 Stock Disponible - {insumo_seleccionado}")
            
            # Gráfico de stock disponible por período
            fig_stock = px.line(insumo_data, x='Periodo_Index', y='StockDisponible',
                               title=f"Stock Disponible de {insumo_seleccionado} por Período")
            st.plotly_chart(fig_stock, use_container_width=True)
            
            # Uso en productos
            st.subheader("👕 Productos que utilizan este insumo")
            if not data['DAT_PI_MATRIX'].empty:
                productos_uso = []
                for _, row in data['DAT_PI_MATRIX'].iterrows():
                    if row[insumo_seleccionado] > 0:
                        producto_nombre = data['DAT_PRODUCTOS_FIJOS'][
                            data['DAT_PRODUCTOS_FIJOS']['ID_Producto'] == row['ID_Producto']
                        ]['Nombre_Producto'].iloc[0]
                        productos_uso.append({
                            'Producto': producto_nombre,
                            'Cantidad_Usada': row[insumo_seleccionado]
                        })
                
                if productos_uso:
                    df_uso = pd.DataFrame(productos_uso)
                    fig_uso = px.bar(df_uso, x='Producto', y='Cantidad_Usada',
                                    title=f"Uso de {insumo_seleccionado} en Productos")
                    st.plotly_chart(fig_uso, use_container_width=True)

# ===== SECCIÓN 4: PROCESOS =====
elif section == "⚙️ Procesos":
    st.header("⚙️ Procesos Productivos")
    
    if not data['DAT_PJM_MATRIX'].empty:
        # Selector de proceso
        procesos = data['SET_PROCESOS']['ID_Proceso'].tolist()
        proceso_seleccionado = st.selectbox("Selecciona un proceso:", procesos)
        
        if proceso_seleccionado:
            # Filtrar datos del proceso seleccionado
            proceso_data = data['DAT_PJM_MATRIX'][data['DAT_PJM_MATRIX']['ID_Proceso'] == proceso_seleccionado]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Capacidad por período
                fig_capacidad = px.line(proceso_data, x='Periodo_Index', y='CapacidadMinutos',
                                       title=f"Capacidad de {proceso_seleccionado}")
                st.plotly_chart(fig_capacidad, use_container_width=True)
            
            with col2:
                # Costo de hora extra
                fig_costo_extra = px.line(proceso_data, x='Periodo_Index', y='CostoHoraExtra',
                                         title=f"Costo Hora Extra - {proceso_seleccionado}")
                st.plotly_chart(fig_costo_extra, use_container_width=True)
            
            # Productos que usan este proceso
            st.subheader("👕 Productos que utilizan este proceso")
            if not data['DAT_PP_MATRIX'].empty:
                productos_proceso = []
                for _, row in data['DAT_PP_MATRIX'].iterrows():
                    if row[proceso_seleccionado] > 0:
                        producto_nombre = data['DAT_PRODUCTOS_FIJOS'][
                            data['DAT_PRODUCTOS_FIJOS']['ID_Producto'] == row['ID_Producto']
                        ]['Nombre_Producto'].iloc[0]
                        productos_proceso.append({
                            'Producto': producto_nombre,
                            'Tiempo_Requerido': row[proceso_seleccionado]
                        })
                
                if productos_proceso:
                    df_proceso = pd.DataFrame(productos_proceso)
                    fig_proceso = px.bar(df_proceso, x='Producto', y='Tiempo_Requerido',
                                        title=f"Tiempo en {proceso_seleccionado} por Producto")
                    st.plotly_chart(fig_proceso, use_container_width=True)

# ===== SECCIÓN 5: DEMANDA Y MERCADO =====
elif section == "📊 Demanda y Mercado":
    st.header("📊 Análisis de Demanda y Mercado")
    
    if not data['DAT_PM_MATRIX'].empty:
        # Selector de producto para análisis de demanda
        productos = data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'].tolist()
        producto_demanda = st.selectbox("Selecciona producto para análisis:", productos)
        
        if producto_demanda:
            producto_id = data['DAT_PRODUCTOS_FIJOS'][
                data['DAT_PRODUCTOS_FIJOS']['Nombre_Producto'] == producto_demanda
            ]['ID_Producto'].iloc[0]
            
            # Filtrar datos de demanda del producto
            demanda_producto = data['DAT_PM_MATRIX'][data['DAT_PM_MATRIX']['ID_Producto'] == producto_id]
            
            st.subheader(f"📈 Evolución de la Demanda - {producto_demanda}")
            
            # Crear gráfico de demanda mínima y máxima
            fig_demanda = go.Figure()
            fig_demanda.add_trace(go.Scatter(x=demanda_producto['Periodo_Index'], 
                                           y=demanda_producto['DemandaMinima'], 
                                           name='Demanda Mínima', 
                                           line=dict(color='orange')))
            fig_demanda.add_trace(go.Scatter(x=demanda_producto['Periodo_Index'], 
                                           y=demanda_producto['DemandaMaxima'], 
                                           name='Demanda Máxima', 
                                           line=dict(color='red'),
                                           fill='tonexty'))
            fig_demanda.update_layout(title=f"Demanda Mínima y Máxima - {producto_demanda}",
                                     xaxis_title="Período", yaxis_title="Demanda")
            st.plotly_chart(fig_demanda, use_container_width=True)
            
            # Precios y costos
            st.subheader("💰 Evolución de Precios y Costos")
            
            fig_precios = go.Figure()
            fig_precios.add_trace(go.Scatter(x=demanda_producto['Periodo_Index'], 
                                           y=demanda_producto['PrecioVenta'], 
                                           name='Precio Venta', 
                                           line=dict(color='green')))
            fig_precios.add_trace(go.Scatter(x=demanda_producto['Periodo_Index'], 
                                           y=demanda_producto['CostoInsumo'], 
                                           name='Costo Insumo', 
                                           line=dict(color='red')))
            fig_precios.update_layout(title=f"Precio de Venta vs Costo de Insumos - {producto_demanda}",
                                     xaxis_title="Período", yaxis_title="Valor ($)")
            st.plotly_chart(fig_precios, use_container_width=True)
            
            # Margen calculado
            demanda_producto_copy = demanda_producto.copy()
            demanda_producto_copy['Margen'] = demanda_producto_copy['PrecioVenta'] - demanda_producto_copy['CostoInsumo']
            demanda_producto_copy['Margen_Porcentaje'] = (demanda_producto_copy['Margen'] / demanda_producto_copy['PrecioVenta']) * 100
            
            fig_margen = go.Figure()
            fig_margen.add_trace(go.Scatter(x=demanda_producto_copy['Periodo_Index'], 
                                          y=demanda_producto_copy['Margen_Porcentaje'], 
                                          name='Margen %', 
                                          line=dict(color='blue')))
            fig_margen.update_layout(title=f"Margen Porcentual - {producto_demanda}",
                                    xaxis_title="Período", yaxis_title="Margen (%)")
            st.plotly_chart(fig_margen, use_container_width=True)

# ===== SECCIÓN 6: COSTOS Y RENTABILIDAD =====
elif section == "💰 Costos y Rentabilidad":
    st.header("💰 Análisis de Costos y Rentabilidad")
    
    if not data['DAT_PM_MATRIX'].empty:
        # Calcular métricas agregadas
        costos_agregados = data['DAT_PM_MATRIX'].groupby('Periodo_Index').agg({
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
            fig_tendencias.update_layout(title="Evolución de Precios, Costos y Margenes")
            st.plotly_chart(fig_tendencias, use_container_width=True)
        
        with col2:
            fig_margen_tendencia = px.line(costos_agregados, x='Periodo_Index', y='Margen_Porcentaje',
                                          title="Evolución del Margen Porcentual")
            st.plotly_chart(fig_margen_tendencia, use_container_width=True)
        
        # Análisis por producto
        st.subheader("🏆 Productos Más Rentables")
        
        # Calcular rentabilidad por producto
        rentabilidad_productos = data['DAT_PM_MATRIX'].groupby('ID_Producto').agg({
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
                                 title="Top 10 Productos por Margen %")
            st.plotly_chart(fig_top_porc, use_container_width=True)
        
        with col2:
            # Top productos por margen absoluto
            top_margen_abs = rentabilidad_productos.nlargest(10, 'Margen')
            fig_top_abs = px.bar(top_margen_abs, x='Nombre_Producto', y='Margen',
                                title="Top 10 Productos por Margen Absoluto")
            st.plotly_chart(fig_top_abs, use_container_width=True)

# ===== SECCIÓN 7: MODELO DE OPTIMIZACIÓN =====
else:
    st.header("🔍 Modelo de Optimización")
    
    st.markdown("""
    ### 📋 Descripción del Modelo de Optimización
    
    El modelo implementado en LINGO resuelve el problema de planificación de producción para maximizar 
    la rentabilidad de ICATEX considerando:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Función Objetivo:**
        ```
        MAX Z = Σ(Ingresos por Ventas) 
               - Σ(Costos de Insumos)
               - Σ(Costos de Almacenamiento)
               - Σ(Costos de Horas Extra)
        ```
        
        **📊 Variables de Decisión:**
        - Producción por producto y período
        - Ventas por producto y período  
        - Inventario por producto y período
        - Horas extras por proceso y período
        """)
    
    with col2:
        st.markdown("""
        **⚖️ Restricciones Principales:**
        1. **Balance de Inventarios**
        2. **Límites de Demanda** (Mínima y Máxima)
        3. **Capacidad de Procesos**
        4. **Disponibilidad de Insumos**
        5. **No Negatividad**
        """)
    
    st.markdown("---")
    
    # Mostrar estructura de datos del modelo
    st.subheader("🏗️ Estructura de Datos del Modelo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Conjunto Productos", len(data['SET_PRODUCTOS']))
        st.metric("Conjunto Procesos", len(data['SET_PROCESOS']))
    
    with col2:
        st.metric("Conjunto Insumos", len(data['SET_INSUMOS']))
        st.metric("Períodos de Planificación", len(data['SET_MESES']))
    
    with col3:
        if not data['DAT_PM_MATRIX'].empty:
            st.metric("Registros en Matriz PM", len(data['DAT_PM_MATRIX']))
        if not data['DAT_PJM_MATRIX'].empty:
            st.metric("Registros en Matriz PJM", len(data['DAT_PJM_MATRIX']))
    
    # Visualización de capacidades y restricciones
    st.subheader("📊 Capacidades y Restricciones del Sistema")
    
    if not data['DAT_PJM_MATRIX'].empty:
        # Capacidad por proceso
        capacidad_promedio = data['DAT_PJM_MATRIX'].groupby('ID_Proceso')['CapacidadMinutos'].mean().reset_index()
        fig_capacidad = px.bar(capacidad_promedio, x='ID_Proceso', y='CapacidadMinutos',
                              title="Capacidad Promedio por Proceso (minutos)")
        st.plotly_chart(fig_capacidad, use_container_width=True)
    
    # Información sobre resultados
    st.subheader("📈 Resultados de la Optimización")
    
    st.info("""
    **ℹ️ Nota:** Los resultados de optimización se cargarán automáticamente desde LINGO 
    una vez que el modelo sea ejecutado. Las hojas RESULTADOS y RES_HORAS_EXTRA del 
    archivo Excel mostrarán la solución óptima encontrada.
    """)
    
    # Mostrar estado actual de resultados (vacíos por ahora)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estado de Resultados:**")
        if not data['RESULTADOS'].empty:
            st.success("✅ Resultados disponibles")
            st.dataframe(data['RESULTADOS'].head())
        else:
            st.warning("⏳ Resultados pendientes de ejecución")
    
    with col2:
        st.write("**Estado de Horas Extra:**")
        if not data['RES_HORAS_EXTRA'].empty:
            st.success("✅ Horas extra calculadas")
            st.dataframe(data['RES_HORAS_EXTRA'].head())
        else:
            st.warning("⏳ Horas extra pendientes de cálculo")

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
- Salidas: Hojas RES_*
- Modelo: Optimización completa
""")

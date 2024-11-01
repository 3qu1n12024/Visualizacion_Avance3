import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static 

# Cargar el archivo shapefile
ny = gpd.read_file(r'C:\ProgramData\anaconda3\envs\nuevo_entorno\Scripts\Proyecto_Visualizacion\Borough_Boundaries')

# Cargar el archivo CSV
df = pd.read_csv(r'C:\ProgramData\anaconda3\envs\nuevo_entorno\Scripts\Proyecto_Visualizacion\NYC_Collisions.csv')

# Rellenar valores nulos y procesar el DataFrame
df.drop(columns=['Cross Street'], inplace=True)
df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
df['Borough'] = df['Borough'].fillna('Unknown')
df['Contributing Factor'] = df['Contributing Factor'].fillna('Unspecified')
df['Street Name'] = df['Street Name'].fillna('Unspecified')
df['Date'] = pd.to_datetime(df['Date'])
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S')
df['Persons Injured'] = df['Persons Injured'].fillna(0).astype(int)
df['Year'] = df['Date'].dt.year
df['Hour'] = df['Time'].dt.hour  # Extraer la hora del accidente

# Agrupar los accidentes por distrito y año
accidents_per_borough = df.groupby(['Borough', 'Year']).size().reset_index(name='Accident_Count')
ny = ny.rename(columns={'boro_name': 'Borough'})
ny = ny.merge(accidents_per_borough, on='Borough')

# Seleccionar el año
selected_year = st.sidebar.selectbox('Selecciona el Año', df['Year'].unique())  # Usar la barra lateral

# Filtrar los datos según el año seleccionado
filtered_df = df[df['Year'] == selected_year]
ny_year = ny[ny['Year'] == selected_year].copy()  # Hacer una copia del DataFrame filtrado

# Crear un diccionario de colores para cada distrito
colors = {
    'Manhattan': 'lightblue',
    'Bronx': 'lightgreen',
    'Brooklyn': 'salmon',
    'Queens': 'lightcoral',
    'Staten Island': 'lightgoldenrodyellow',
    'Unknown': 'gray'
}

# Asignar colores a cada distrito
ny_year.loc[:, 'Color'] = ny_year['Borough'].map(colors)  # Usar .loc para evitar SettingWithCopyWarning

# Ordenar los datos por Accident_Count en orden descendente
ny_year = ny_year.sort_values('Accident_Count', ascending=True)

# Gráfico de accidentes por distrito
st.subheader(f'Accidentes de Tránsito por Distrito en {selected_year}')
fig, ax = plt.subplots(figsize=(10, 6))  # Ajusta el tamaño según prefieras
ny_year.plot(kind='barh', x='Borough', y='Accident_Count', ax=ax, color=ny_year['Color'])
ax.set_xlabel('Cantidad de Accidentes')
ax.set_ylabel('Distritos')
st.pyplot(fig)  # Mostrar la figura en Streamlit

# Gráfico de accidentes por tipo de vehículo
st.subheader('Accidentes por Tipo de Vehículo por Distrito')
top_vehicles = filtered_df['Vehicle Type'].value_counts().nlargest(3).index.tolist()
filtered_accidents = filtered_df[filtered_df['Vehicle Type'].isin(top_vehicles)]
accidents_by_vehicle = filtered_accidents.groupby(['Borough', 'Vehicle Type']).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(10, 6))
accidents_by_vehicle.plot(kind='bar', ax=ax)
ax.set_xlabel('Distritos')
ax.set_ylabel('Cantidad de Accidentes')
st.pyplot(fig)

# Gráfico de accidentes por factores contribuyentes
st.subheader('Top 3 Factores Contribuyentes por Distrito')
top_factors = filtered_df['Contributing Factor'].value_counts().nlargest(3).index.tolist()
filtered_factors = filtered_df[filtered_df['Contributing Factor'].isin(top_factors)]
accidents_by_factor = filtered_factors.groupby(['Borough', 'Contributing Factor']).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(10, 6))
accidents_by_factor.plot(kind='bar', ax=ax)
ax.set_xlabel('Distritos')
ax.set_ylabel('Cantidad de Accidentes')
st.pyplot(fig)

# Seleccionar distrito para filtrado
selected_borough = st.selectbox('Selecciona un Distrito', filtered_df['Borough'].unique())

# Filtrar DataFrame según el distrito seleccionado
filtered_borough_data = filtered_df[filtered_df['Borough'] == selected_borough]

# Seleccionar top 3 "Street Name" y "Contributing Factor" del distrito seleccionado
top_streets = filtered_borough_data['Street Name'].value_counts().nlargest(3).index.tolist()
top_factors = filtered_borough_data['Contributing Factor'].value_counts().nlargest(3).index.tolist()

selected_street = st.selectbox('Selecciona una Calle de los Top 3', top_streets)
selected_factor = st.selectbox('Selecciona un Factor Contribuyente de los Top 3', top_factors)

# Filtrar datos según la calle y el factor seleccionados
filtered_data = filtered_borough_data[(filtered_borough_data['Street Name'] == selected_street) &
                                       (filtered_borough_data['Contributing Factor'] == selected_factor)]

# Agrupar por distrito y hora
accidents_by_hour = filtered_data.groupby(['Borough', 'Hour']).size().unstack(fill_value=0)

# Graficar una línea por cada distrito
st.subheader(f'Accidentes por Hora del Día para {selected_street} y {selected_factor}')
fig, ax = plt.subplots(figsize=(10, 6))
for borough in accidents_by_hour.index:
    ax.plot(accidents_by_hour.columns, accidents_by_hour.loc[borough], marker='o', linewidth=2, label=borough)

ax.set_xlabel('Hora del Día')
ax.set_ylabel('Cantidad de Accidentes')
ax.set_xticks(range(0, 24))
ax.set_xticklabels(range(0, 24))
ax.grid()
ax.legend(title='Distritos')
st.pyplot(fig)  # Mostrar la figura en Streamlit

# Filtrar datos para distrito y la calle seleccionada
filtered_borough_mapa = filtered_df[(filtered_df['Borough'] == selected_borough) & 
                                     (filtered_df['Street Name'] == selected_street)]

# Crear un mapa centrado en Brooklyn
map_center = [filtered_borough_mapa['Latitude'].mean(), filtered_borough_mapa['Longitude'].mean()]
borough_map = folium.Map(location=map_center, zoom_start=12)

# Agregar puntos de calor
heat_data = [[row['Latitude'], row['Longitude']] for index, row in filtered_borough_mapa.iterrows()]
HeatMap(heat_data).add_to(borough_map)

# Mostrar el mapa en Streamlit
st.subheader(f'Mapa de Calor de Accidentes en {selected_street} en {selected_borough}')
folium_static(borough_map)

# import libraries
import streamlit as st
import pandas as pd
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import plotly.express as px
import kota as kota
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
import pydeck as pdk
from google.cloud import storage
from st_files_connection import FilesConnection
import os
import osmnx as ox


# set page config
st.set_page_config(
    page_title="Banten",
    layout="wide", 
    page_icon= ":house:", 
    menu_items= {'About':'Made by Daniel Caesar Pratama'}, 
    initial_sidebar_state= "collapsed"
)


# ------------------------------------------------------------------------------
# connect to google cloud service
gcs_credentials = st.secrets.connections.gcs
storage_client = storage.Client.from_service_account_info(info=gcs_credentials)

# import base data
@st.cache_data
def get_data(file_name):
    df = pd.read_csv(f"data/{file_name}")
    return df

@st.cache_data
def get_geom(geom_URL):
    # Read the GeoJSON file using geopandas
    # gdf = gpd.read_file(geom_URL)
    bucket_name = 'datakota-bucket'
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(geom_URL)
    # Download the file to a local temporary file
    with open('temp.geojson', 'wb') as temp_file:
        blob.download_to_file(temp_file, timeout=900)
    # Read the GeoJSON file using geopandas
    gdf = gpd.read_file('temp.geojson')
    # Don't forget to clean up the temporary file
    os.remove('temp.geojson')
    return gdf

# import base_df
base_df = get_data("base_df_banten.csv")
base_df['KODE_PROVINSI'] = base_df['KODE_PROVINSI'].astype(str)
base_df['KODE_KAB_KOTA'] = base_df['KODE_KAB_KOTA'].apply(lambda x: "{:.2f}".format(x))



# ------------------------------------------------------------------------------
# SET UP SIDEBAR
with st.sidebar:
    # SET UP TITLE 
    st.subheader('Contact us!')
    st.write('Created by Datakota')
    st.markdown("""
    [twitter](https://twitter.com/danielcaesarp)  
    [instagram](https://instagram.com/datakota.app)  
    [email](hi.datakota@gmail.com)  
    [github](https://github.com/danielcpratama/datakota)

    """)

# ------------------------------------------------------------------------------
col1, col2 = st.columns([0.2,0.8])
col1.image('logo/photo.png', width=200)
col2.title("Dashboard Strategi Kampanye Provinsi Banten")
col2.subheader("Andra Soni - Dimyati 2024")
col2.image('logo/logo.png', width=100)

tab1, tab2, tab3, tab4, = st.tabs(['A. Kalkulator Asumsi RTV', 'B. Strategi Relawan', 'C. Profil Kawasan', 'D. Strategi Peletakan APK'])
# -----TAB1-------------------------------------------------------------------------
# ASSUMPTIONS
with tab1:
    colA, colB =  st.columns([0.3,0.7])
    # set up basic assumptions
    with colA:
        with st.container(border=True, height=470):
            st.markdown('#### Asumsi Dasar')
            target_final = st.number_input('Target Suara Akhir (%)', min_value=0, max_value=100, step=5, value=55)
            target_rumah_relawan = st.number_input('Target Rumah per Relawan', min_value=0, max_value=200, step=5, value=100)
            DPT_per_rumah = st.number_input('Asumsi DPT per Rumah', min_value=0.00, max_value=5.00, step=0.05, value=2.95)
            Optimisme = st.number_input('Dari 10 rumah yang relawan datangi, berapa estimasi pemilih akhir Andra?', min_value=1, max_value=10, step=1, value=7)
    # set up basic scenario
    with colB:
        with st.container(border=True, height=470):
            st.markdown('#### Strategi Distribusi Relawan')
            option_df = pd.DataFrame(
                {
                    'Hasil Survey': ['Survey Tinggi', 'Survey Sedang', 'Survey Rendah'],
                    'Potensi Tinggi': ['Tambah Usaha', 'Tambah Usaha', 'Tambah Usaha'],
                    'Potensi Sedang': ['Pertahankan Usaha', 'Pertahankan Usaha', 'Tambah Usaha'],
                    'Potensi Rendah': ['Pertahankan Usaha', 'Kurangi Usaha', 'Kurangi Usaha'],
                }
            )
        
            option_list = ['Tambah Usaha', 'Pertahankan Usaha', 'Kurangi Usaha']
            option_fin = st.data_editor(option_df, 
                           column_config={
                               'Hasil Survey':st.column_config.Column(disabled=True),
                               'Potensi Tinggi':st.column_config.SelectboxColumn(options=option_list, required=True),
                               'Potensi Sedang':st.column_config.SelectboxColumn(options=option_list, required=True),
                               'Potensi Rendah':st.column_config.SelectboxColumn(options=option_list, required=True)
                           }, 
                           use_container_width=True, 
                           hide_index=True
                           )
            st.caption('** Kolom Survey menandakan pemilih Tina Nur Alam pada polling')
            st.caption('** Potensi menandakan pemilih Lainnya/Tidak Tahu/Tidak Jawab pada polling')

            colX, colY, colZ = st.columns([1,1,1])
            with colX:
                increase_rate = st.number_input('Tambah Usaha (%)', min_value=100, max_value=200, step=10, value=130)
                st.caption(f'Jika suatu daerah awalnya dikerahkan 100 orang, maka sekarang dikerahkan {increase_rate} orang')
            with colY:
                retain_rate = st.number_input('Pertahankan Usaha (%)', min_value=50, max_value=200, step=10, value=100)
                st.caption(f'Jika suatu daerah awalnya dikerahkan 100 orang, maka sekarang dikerahkan {retain_rate} orang')
            with colZ:
                reduce_rate = st.number_input('Kurangi Usaha (%)', min_value=50, max_value=100, step=10, value=70)
                st.caption(f'Jika suatu daerah awalnya dikerahkan 100 orang, maka sekarang dikerahkan {reduce_rate} orang')

    # import dapil df
    dapil_df = get_data('survey_df.csv')
    # calculate key summary metrics given assumptions
    options_melt = option_fin.melt(id_vars=['Hasil Survey'])
    options_melt['strategy_key'] = options_melt['Hasil Survey'] + '_' + options_melt['variable']
    dapil_df = pd.merge(dapil_df, options_melt[['strategy_key', 'value']], on='strategy_key', how='left').rename(columns={'value':'strategy'})
    # calculate percentage of effort
    dapil_df['persentase'] = 0
    for index, row in dapil_df.iterrows():
        if row['strategy'] == 'Tambah Usaha':
            dapil_df.at[index, 'persentase']  = increase_rate
        elif row['strategy'] == 'Pertahankan Usaha':
            dapil_df.at[index, 'persentase']  = retain_rate
        else:
            dapil_df.at[index, 'persentase']  = reduce_rate
    dapil_df['target_suara'] = dapil_df['Total_DPT']*target_final/100
    dapil_df['target_rumah'] = dapil_df['target_suara']/DPT_per_rumah
    dapil_df['target_relawan'] = dapil_df['target_rumah']*(10/Optimisme)/target_rumah_relawan
    # display metrics
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        col1.metric(label='Total DPT', value=f'{dapil_df.Total_DPT.sum():,}')
        col2.metric(label='Total Target Suara', value=f'{dapil_df.Total_DPT.sum()*target_final/100:,.0f}', delta=f'{target_final}%')
        col3.metric(label='Total Target Rumah', value=f'{dapil_df.target_rumah.sum():,.0f}')
        col4.metric(label='Total Target Relawan', value=f'{dapil_df.target_relawan.sum():,.0f}')
    
    # st.dataframe(dapil_df)
    # st.dataframe(base_df)

# -----TAB2-------------------------------------------------------------------------
with tab2:
    colA, colB = st.columns([0.2,0.8])
    with colA:
        with st.container(border=True):
            # PILIHAN FILTER
            # ---------------------------------------
            st.markdown('##### 1. Pilih Analisis')
            
            # Selectbox for Extent subset
            extent_list = ['se-Provinsi', 'se-Kota', 'se-Kecamatan']
            extent_analysis = st.selectbox('Skala Analisis', options=extent_list, key='extent')
            
            # Selectbox for smallest unit
            if extent_analysis == 'se-Provinsi':
                unit_list = ['KAB_KOTA', ] #'KECAMATAN', 'DESA_KELURAHAN'
            elif extent_analysis == 'se-Kota':
                unit_list = ['KECAMATAN', ] #'DESA_KELURAHAN'
            else: 
                unit_list = ['DESA_KELURAHAN']
            unit_analysis = st.selectbox('Unit Analisis', options=unit_list, key='units')
            # ---------------------------------------
            st.markdown('#### 2. Filter Lokasi')

            # Selectbox for Kota subset
            if extent_analysis == 'se-Provinsi':
                city_list = ['Semua Kota/Kabupaten'] #+ list(base_df.NAMA_KAB_KOTA.unique())
            else:
                # city_list = list(base_df.sort_values(by='NAMA_KAB_KOTA').NAMA_KAB_KOTA.unique())
                city_list = ['Kota Tangerang Selatan', 'Kota Tangerang']
            city_analysis = st.selectbox('Pilih Kota', options=city_list, key='city')

            # Selectbox for Kecamatan subset
            if extent_analysis == 'se-Kecamatan':
                kec_list = list(base_df[base_df.NAMA_KAB_KOTA == city_analysis].sort_values(by='NAMA_KECAMATAN').NAMA_KECAMATAN.unique())
            else :
                kec_list = ['Semua Kecamatan']
            # else:
            #     city_list = ['Semua Kecamatan'] + list(base_df[base_df.NAMA_KAB_KOTA == city_analysis].sort_values(by='NAMA_KECAMATAN').NAMA_KECAMATAN.unique())
            kec_analysis = st.selectbox('Pilih Kecamatan', options=kec_list, key='kecamatan', disabled=True)
            
            # ---------------------------------------
            st.markdown('#### 3. Visualisasikan Data')
            # select options for visualization
            viz_list = ['Peta & Grafik', 'Tabel']
            visualization = st.radio('Pilih jenis visualisasi', options=viz_list, key='visualisasi')

            

    with colB:            
        # join values from basic assumption
        relawan_df = pd.merge(base_df, dapil_df[['KODE_KEC', 'persentase', 'strategy', 'Survey', 'Potensi']], on='KODE_KEC', how='left')
        # perform calculation
        relawan_df['target_suara'] = round(relawan_df['Total_DPT']*target_final/100,0)
        relawan_df['target_rumah'] = round(relawan_df['target_suara']/DPT_per_rumah,0)
        relawan_df['target_relawan'] = round(relawan_df['target_rumah']*(10/Optimisme)/target_rumah_relawan,0)
        relawan_df['sum_product'] = relawan_df['target_relawan']*(relawan_df['persentase']/100)
        relawan_df['distribusi_relawan'] = round((relawan_df['persentase']/100)*(relawan_df['target_relawan']*(relawan_df['target_relawan'].sum()/relawan_df['sum_product'].sum())),0)
    
        # ------------------------------------------------------------------------------
            # get geometry according to filter on sidebar

        geom_URL = f'geom/{unit_analysis}_BY_PROVINCE/Banten_{unit_analysis}.geojson'

        with st.spinner('dicariin dulu ya...'):
            if extent_analysis == 'se-Provinsi':
                gdf = get_geom(geom_URL=geom_URL)
            elif extent_analysis == 'se-Kota':
                gdf = get_geom(geom_URL=geom_URL)
                gdf = gdf[gdf.NAMA_KAB_KOTA == city_analysis]     
            else: 
                gdf = get_geom(geom_URL=geom_URL)
                gdf = gdf[gdf.NAMA_KECAMATAN == kec_analysis]     
            gdf.KODE_PROVINSI = gdf.KODE_PROVINSI.astype(str)

        relawan_ori_list = ['Total_DPT', 'target_suara', 'target_rumah', 'distribusi_relawan']
        relawan_viz_list = ['Total DPT', 'Target Suara', 'Target Rumah', 'Distribusi Relawan']
        if unit_analysis == 'DESA_KELURAHAN':
            pivot_df = relawan_df[['KODE_KEL_DESA'] + relawan_ori_list]
            pivot_df.columns = ['KODE_KEL_DESA'] + relawan_viz_list
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on='KODE_KEL_DESA').rename(columns={'NAMA_KEL_DESA':'NAMA_DESA_KELURAHAN'})
        elif unit_analysis == 'KECAMATAN':
            pivot_df = relawan_df[['KODE_KEC'] + relawan_ori_list].groupby(by=f'KODE_KEC').sum().reset_index()
            pivot_df.columns = ['KODE_KEC'] + relawan_viz_list
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on=f'KODE_KEC')
        elif unit_analysis == 'KAB_KOTA':
            pivot_df = relawan_df[['KODE_KAB_KOTA'] + relawan_ori_list].groupby(by=f'KODE_KAB_KOTA').sum().reset_index()
            pivot_df.columns = ['KODE_KAB_KOTA'] + relawan_viz_list
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on=f'KODE_KAB_KOTA')

        if visualization == 'Peta & Grafik':
            
            analysis = st.selectbox('Pilih Visualisasi', options=relawan_viz_list)
            
            # display map
            col1, col2 = st.columns([0.7,0.3])
            with col1:
                cmap = 'OrRd'
                title = str.title(f'Peta {analysis}, seluruh {unit_analysis} di {kec_analysis}, {city_analysis}')
                st.markdown(f'##### {title}')
                tooltip = [f'NAMA_{unit_analysis}', analysis]
                map = kota.make_map(pivot_gdf, column=analysis, tooltip=tooltip, cmap=cmap)
                with st.container(border=True, height= 450):
                            st_folium(map, 
                                returned_objects= [],
                                height = 400, 
                                use_container_width=True
                                )
                # MAKING LEGENDS
                cropped_png = kota.make_legend(pivot_gdf, column=analysis, cmap=cmap)
                st.image(cropped_png,  width=400) #caption='Legend',

            with col2:
                st.container(border=True, height=110).metric('Total DPT', value= f'{pivot_gdf["Total DPT"].sum():,.0f}')
                st.container(border=True, height=110).metric('Total Target Suara', value= f'{pivot_gdf["Target Suara"].sum():,.0f}')
                st.container(border=True, height=110).metric('Total Rumah', value= f'{pivot_gdf["Target Rumah"].sum():,.0f}')
                st.container(border=True, height=110).metric('Total Kebutuhan Relawan', value= f'{pivot_gdf["Distribusi Relawan"].sum():,.0f}')
        
        else:
            st.markdown(f'#### Tabel Rekapitulasi Strategi Relawan di {kec_analysis}, {city_analysis}')
            st.dataframe(pivot_gdf.drop(columns='geometry'), height=480)
            csv = pivot_gdf.drop(columns='geometry').to_csv().encode("utf-8")
            st.download_button('simpan tabel', data=csv, file_name=f'RekapRelawan_{kec_analysis}_{city_analysis}.csv', mime="text/csv", type='primary')

# -----TAB3-------------------------------------------------------------------------
with tab3:
    # import dataset
    demo_df = get_data('demo_df.csv').drop(columns='Unnamed: 0')
    demo_df['KODE_PROVINSI'] = demo_df['KODE_PROVINSI'].astype(str)
    demo_df['KODE_KAB_KOTA'] = demo_df['KODE_KAB_KOTA'].apply(lambda x: "{:.2f}".format(x))



    colA, colB = st.columns([0.2,0.8])
    with colA:
        with st.container(border=True):
            # PILIHAN FILTER
            # ---------------------------------------
            st.markdown('##### 1. Pilih Analisis')
            
            # Selectbox for Extent subset
            extent_list = ['se-Provinsi', 'se-Kota', 'se-Kecamatan']
            extent_analysis = st.selectbox('Skala Analisis', options=extent_list, key='extent2')
            
            # Selectbox for smallest unit
            if extent_analysis == 'se-Provinsi':
                unit_list = ['KAB_KOTA', ] #'KECAMATAN', 'DESA_KELURAHAN'
            elif extent_analysis == 'se-Kota':
                unit_list = ['KECAMATAN', ] #'DESA_KELURAHAN'
            else: 
                unit_list = ['DESA_KELURAHAN']
            unit_analysis = st.selectbox('Unit Analisis', options=unit_list, key='units2', disabled=True)
            # ---------------------------------------
            st.markdown('#### 2. Filter Lokasi')

            # Selectbox for Kota subset
            if extent_analysis == 'se-Provinsi':
                city_list = ['Semua Kota/Kabupaten'] #+ list(base_df.NAMA_KAB_KOTA.unique())
            else:
                # city_list = list(base_df.sort_values(by='NAMA_KAB_KOTA').NAMA_KAB_KOTA.unique())
                city_list = ['Kota Tangerang Selatan', 'Kota Tangerang']
            city_analysis = st.selectbox('Pilih Kota', options=city_list, key='city2')

            # Selectbox for Kecamatan subset
            if extent_analysis == 'se-Kecamatan':
                kec_list = list(base_df[base_df.NAMA_KAB_KOTA == city_analysis].sort_values(by='NAMA_KECAMATAN').NAMA_KECAMATAN.unique())
            else :
                kec_list = ['Semua Kecamatan']
            # else:
            #     city_list = ['Semua Kecamatan'] + list(base_df[base_df.NAMA_KAB_KOTA == city_analysis].sort_values(by='NAMA_KECAMATAN').NAMA_KECAMATAN.unique())
            kec_analysis = st.selectbox('Pilih Kecamatan', options=kec_list, key='kecamatan2', disabled=True)
            
            # ---------------------------------------
            st.markdown('#### 3. Visualisasikan Data')
            # select options for visualization
            viz_list = ['Peta & Grafik', 'Tabel']
            visualization = st.radio('Pilih jenis visualisasi', options=viz_list, key='visualisasi2')
    
    with colB:
        # selectbox for profile
        col1, col2 = st.columns([1,1])
        profile_list = ['Usia', 'Pekerjaan', 'Pendidikan', 'Agama']
        profile = col1.selectbox('Pilih Profil', options=profile_list)

        with col2:
            if profile == 'Usia':
                sub_profile_list = list(demo_df.columns)[6:9]
            elif profile == 'Pekerjaan':
                sub_profile_list = list(demo_df.columns)[9:13]
            elif profile == 'Pendidikan':
                sub_profile_list = list(demo_df.columns)[13:16]
            else:
                sub_profile_list = list(demo_df.columns)[16:]
            
            sub_profile = st.selectbox('Pilih detail profil', options = sub_profile_list)

        # ------------------------------------------------------------------------------
        # get geometry according to filter on sidebar

        geom_URL = f'geom/{unit_analysis}_BY_PROVINCE/Banten_{unit_analysis}.geojson'

        with st.spinner('dicariin dulu ya...'):
            if extent_analysis == 'se-Provinsi':
                gdf = get_geom(geom_URL=geom_URL)
            elif extent_analysis == 'se-Kota':
                gdf = get_geom(geom_URL=geom_URL)
                gdf = gdf[gdf.NAMA_KAB_KOTA == city_analysis]     
            else: 
                gdf = get_geom(geom_URL=geom_URL)
                gdf = gdf[gdf.NAMA_KECAMATAN == kec_analysis]     
            gdf.KODE_PROVINSI = gdf.KODE_PROVINSI.astype(str)
        
        demo_list = list(demo_df.columns[6:])
        if unit_analysis == 'DESA_KELURAHAN':
            pivot_df = demo_df[['KODE_KEL_DESA'] + demo_list]
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on='KODE_KEL_DESA').rename(columns={'NAMA_KEL_DESA':'NAMA_DESA_KELURAHAN'})
        elif unit_analysis == 'KECAMATAN':
            pivot_df = demo_df[['KODE_KEC'] + demo_list].groupby(by=f'KODE_KEC').sum().reset_index()
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on='KODE_KEC')
        elif unit_analysis == 'KAB_KOTA':
            pivot_df = demo_df[['KODE_KAB_KOTA'] + demo_list].groupby(by=f'KODE_{unit_analysis}').sum().reset_index()
            pivot_gdf = pd.merge(gdf,pivot_df, how='left', on='KODE_KAB_KOTA')
        
        if visualization == ('Peta & Grafik'):
            
            colX, colY = st.columns([0.7,0.3])
            with colX:
                cmap = 'OrRd'
                title = str.title(f'Peta {sub_profile}, seluruh {unit_analysis} di {kec_analysis}, {city_analysis}')
                st.markdown(f'##### {title}')
                tooltip = [f'NAMA_{unit_analysis}', sub_profile]
                map = kota.make_map(pivot_gdf, column=sub_profile, tooltip=tooltip, cmap=cmap)
                with st.container(border=True, height= 450):
                            st_folium(map, 
                                returned_objects= [],
                                height = 400, 
                                use_container_width=True
                                )
                
                # MAKING LEGENDS
                cropped_png = kota.make_legend(pivot_gdf, column=sub_profile, cmap=cmap)
                st.image(cropped_png,  width=400) #caption='Legend',
            
            with colY:
                with st.container(border=True, height=100):
                    st.metric(label=f'Total Populasi {profile} {sub_profile}', value=f"{pivot_gdf[sub_profile].sum():,}")
                with st.container(border=True, height=400):
                    place_ind = 'NAMA_' + str(unit_analysis)
                    sort_df = pivot_gdf[[place_ind] + sub_profile_list]
                    sort_df['total'] = sort_df[sub_profile_list].sum(axis = 1)
                    sort_df = sort_df.sort_values(by= sub_profile, ascending = True)
                    

                    plot_title = f'Komposisi {profile}'
                    axis_label = f'Populasi berdasar {profile}'
                    fig = px.bar(sort_df, 
                                x = sub_profile_list,
                                y = f'NAMA_{unit_analysis}',
                                title= plot_title, #template = 'seaborn', 
                                color_discrete_sequence = px.colors.qualitative.T10
                                )

                    # Update layout for the legend to be below the chart
                    fig.update_layout(
                        legend=dict(
                            yanchor="top",
                            y=-0.3,  # Adjust this value to move the legend further down or up
                            xanchor="center",
                            x=-0.5,
                        )
                    )

                    # fig.update_traces(colorscale = 'Cividis')
                    fig.update_xaxes(title_text = axis_label)
                    st.plotly_chart(fig, use_container_width = True)
        else:
            st.markdown(f'#### Tabel Rekapitulasi Profil Kawasan di {kec_analysis}, {city_analysis}')
            st.dataframe(pivot_gdf.drop(columns='geometry'), height=480)
            csv = pivot_gdf.drop(columns='geometry').to_csv().encode("utf-8")
            st.download_button('simpan tabel', data=csv, file_name=f'RekapDemografi_{kec_analysis}_{city_analysis}.csv', mime="text/csv", type='primary')

# -----TAB4-------------------------------------------------------------------------
with tab4:
    colA, colB = st.columns([0.2,0.8])
    with colA:
        with st.container(border=True):
            # PILIHAN FILTER
            # ---------------------------------------
            st.markdown('##### 1. Pilih Analisis')
            
            # Selectbox for Extent subset
            extent_list = ['se-Kelurahan']
            extent_analysis = st.selectbox('Skala Analisis', options=extent_list, key='extent3')
            
            # Selectbox for smallest unit
            if extent_analysis == 'se-Provinsi':
                unit_list = ['KAB_KOTA', 'KECAMATAN', 'DESA_KELURAHAN']
            elif extent_analysis == 'se-Kota':
                unit_list = ['KECAMATAN', 'DESA_KELURAHAN']
            else: 
                unit_list = ['DESA_KELURAHAN']
            unit_analysis = st.selectbox('Unit Analisis', options=unit_list, key='units3')
            # ---------------------------------------
            st.markdown('#### 2. Filter Lokasi')

            # Selectbox for Kota subset
            if extent_analysis == 'se-Provinsi':
                city_list = ['Semua Kota/Kabupaten'] #+ list(base_df.NAMA_KAB_KOTA.unique())
            else:
                # city_list = list(base_df.sort_values(by='NAMA_KAB_KOTA').NAMA_KAB_KOTA.unique())
                city_list = ['Kota Tangerang Selatan', 'Kota Tangerang']
            city_analysis = st.selectbox('Pilih Kota', options=city_list, key='city3')

            # Selectbox for Kecamatan subset
            if extent_analysis == 'se-Kelurahan':
                kec_list = list(base_df[base_df.NAMA_KAB_KOTA == city_analysis].sort_values(by='NAMA_KECAMATAN').NAMA_KECAMATAN.unique())[:3]
            else :
                kec_list = ['Semua Kecamatan']
            
            kec_analysis = st.selectbox('Pilih Kecamatan', options=kec_list, key='kecamatan3')
            
            # Selectbox for Kelurahan subset
            if extent_analysis == 'se-Kelurahan':
                kel_list = list(base_df[base_df.NAMA_KECAMATAN == kec_analysis].sort_values(by='NAMA_KEL_DESA').NAMA_KEL_DESA.unique())[:3]
            else :
                kel_list = ['Semua Kelurahan']
            
            kel_analysis = st.selectbox('Pilih Kelurahan', options=kel_list, key='kelurahan3')
            
            
    with colB:
        # import analysis boundary
        network_geom_URL = f'geom/DESA_KELURAHAN_BY_PROVINCE/Banten_DESA_KELURAHAN.geojson'

        # point_geom_URL = f'data/POI_sultra.geojson'

        try:
            with st.spinner('dicariin dulu ya...'):
                gdf_network = get_geom(geom_URL=network_geom_URL)
                gdf_network = gdf_network[gdf_network.NAMA_KEL_DESA == kel_analysis]     
                gdf_network.KODE_PROVINSI = gdf_network.KODE_PROVINSI.astype(str)
                
                try:
                    with st.spinner('cari titik keramaian...'):
                        # Fetch POIs as in previous example
                        tags = {
                            'amenity': True,
                            'shop': True,  # Fetch all types of shops
                            'leisure': ['park', 'fitness_centre', 'sports_centre', 'swimming_pool'],
                            'tourism': ['museum', 'attraction', 'gallery', 'zoo'],
                            'railway': 'station'
                        }
                        
                        gdf_poi = ox.geometries_from_polygon(gdf_network.to_crs(4326).geometry.item(), tags)
                        gdf_poi = gdf_poi[gdf_poi.geometry.type == 'Point'].reset_index()
                        gdf_poi = gdf_poi.to_crs(4326)
                        # Extract longitude and latitude for Pydeck
                        gdf_poi["Longitude"] = gdf_poi.geometry.x
                        gdf_poi["Latitude"] = gdf_poi.geometry.y
                        
                        # create tooltip
                        def create_tooltip(row):
                            values = [row['name'], row['name:en'], row['amenity'], row['shop']]
                            filtered_values = [str(value) for value in values if value is not None and pd.notna(value)]
                            return ', '.join(filtered_values)
    
                        # Apply the function to each row in gdf_poi
                        gdf_poi['tooltip'] = gdf_poi.apply(create_tooltip, axis=1)
                    except:
                        continue
                

            data = kota.get_network_centrality(gdf_network)

            # Normalize betweenness centrality and get colors from a colormap
            cmap = plt.get_cmap('Reds')  # Choose your colormap (e.g., 'viridis', 'plasma', etc.)
            norm = mcolors.Normalize(vmin=data['betweenness_centrality'].min(), vmax=data['betweenness_centrality'].max())
            
            # Apply colormap to each row in your dataframe
            data['line_color'] = data['betweenness_centrality'].apply(lambda x: [int(c * 255) for c in cmap(norm(x))[:3]])
            data['tooltip'] = data['name']

            Jalan = pdk.Layer(
                    "GeoJsonLayer",
                    data,
                    get_path = 'geometry',
                    get_line_width="betweenness_centrality * 300 + 15",  # Scale the width as needed
                    width_min_scale = 1.5,
                    get_line_color = "line_color",
                    pickable=True, 
                    opacity = 0.6
                    
                )
            
            Heatmap = pdk.Layer(
                    "HeatmapLayer",
                    gdf_poi,
                    opacity=0.5,
                    get_position=["Longitude", "Latitude"],
                    # aggregation=pdk.types.String("MEAN"),
                    threshold=0.5,
                    pickable = False
                    
                )
            POI = pdk.Layer(
                    "ScatterplotLayer",
                    gdf_poi,
                    opacity=0.9,
                    get_position=["Longitude", "Latitude"],
                    get_fill_color=[255, 0, 0],
                    pickable = True,
                    get_radius=20
                    
                )
            # Define the view state
            view_state = pdk.ViewState(
                latitude=gdf_network.to_crs(4326).geometry.centroid.y.mean(),
                longitude=gdf_network.to_crs(4326).geometry.centroid.x.mean(),
                # zoom=10,
                pitch=0
            )

            # Create the deck
            deck = pdk.Deck(
                layers=[Heatmap, Jalan,POI],
                initial_view_state=view_state,
                map_provider="mapbox",
                map_style=pdk.map_styles.MAPBOX_SATELLITE,
                tooltip={"text": "{tooltip}"},  # Adjust the tooltip to match your data
                height=550,
            )
                # Display in Streamlit
            with st.container(border=True, height = 600):
                st.caption('Lokasi APK bisa diprioritaskan di area/jalan berwarna merah gelap')
                st.pydeck_chart(deck)
            
        except:
            st.warning('maaf pencarian gagal, silahkan coba area lain')
    
       
        

    
       
        

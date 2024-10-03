import streamlit as st
from google.cloud import storage
import bcrypt
import datetime
import time
from st_files_connection import FilesConnection
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from selenium import webdriver
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import io
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
import networkx as nx
import osmnx as ox
import pydeck as pdk



def make_map(data, column, cmap, tooltip):
    map = data.explore(column = data[column],
                        cmap = cmap,
                        tiles = 'CartoDB positron',
                        tooltip = tooltip,
                        scheme = 'EqualInterval', 
                        k = 10, 
                        highlight = True, 
                        popup = True,
                        legend = False,
                        style_kwds = {'stroke':0.5,
                                        'color' : 'black',
                                        'weight' : 0.5,
                                        'fillOpacity' : 0.8
                                        }, 
                        legend_kwds = {'colorbar': False},                                                           
                        min_zoom = 7
                        )
    return map


def make_legend(data, column, cmap):
    legend_fig, legend_ax = plt.subplots(figsize=(50, 3))  # Adjust figsize as needed

    data.plot(ax=legend_ax, column=column, cmap=cmap, legend=True, 
                    legend_kwds = {'orientation':'horizontal', 'fmt':'{:,.0f}'})

    #legend_ax.legend(loc= 'lower right')
    legend_ax.clear()
    legend_ax.axis('off')  # Turn off axis

    # Save the legend plot as a PNG image
    legend_png = BytesIO()
    legend_fig.savefig(legend_png, format='png', bbox_inches = 'tight', dpi = 150)
    plt.close(legend_fig)

    # Load the legend PNG image from BytesIO
    legend_png.seek(0)
    img = Image.open(legend_png)

    # Define the cropping parameters
    left = 0
    top = 300  # Adjust this value as needed to crop from the top
    right = img.width
    bottom = img.height

    # Crop the image
    cropped_img = img.crop((left, top, right, bottom))

    # Convert the cropped image back to BytesIO
    cropped_png = io.BytesIO()
    cropped_img.save(cropped_png, format='PNG')
    return cropped_png


def get_network_centrality(_network):
    # import street network
    with st.spinner('nyari jalan'):
        G = ox.graph_from_polygon(polygon=_network.to_crs(4326).geometry.item(), simplify=True, network_type='drive')

    # Calculate betweenness centrality for nodes
    with st.spinner('ngitung dulu'):
        betweenness_centrality = nx.edge_betweenness_centrality(G)#, normalized=True, weight='length')

    # Convert graph nodes to GeoDataFrame
    with st.spinner('bikin tabel'):
        gdf_nodes = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Add betweenness centrality as a new column in the GeoDataFrame
        gdf_nodes['betweenness_centrality'] = pd.Series(betweenness_centrality)

    return gdf_nodes
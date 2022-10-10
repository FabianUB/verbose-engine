import asyncio
from lib2to3.pytree import convert
from math import prod
from operator import index
import streamlit as st
import streamlit_authenticator as stauth
import hydralit_components as hc
import numpy as np
from datetime import datetime
from st_aggrid import AgGrid
import pandas as pd
import altair as alt
from streamlit.hello.utils import show_code
import datetime
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import io
from deta import Deta
from urllib.error import URLError
import yaml
import base64

def displayPDF(file):
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="675" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def get_data_cleaned(proveedor):
    deta = Deta('a0kv6ay3_MBndet58XcwtGCWVntnKqyF743Wcixkt')
    db = deta.Base('ordenesCompra')
    fetch = db.fetch({'PROVEEDOR':proveedor})
    results = pd.DataFrame(fetch.items)
    while(fetch.last != None):
        fetch = db.fetch({'PROVEEDOR':proveedor}, last=fetch.last)
        results = results.append(fetch.items)
    results['PAX'] = results['PAX'].astype(int)
    results['FECHA'] = pd.to_datetime(results['FECHA'])
    return results

def get_product(proveedor):
    deta = Deta('a0kv6ay3_MBndet58XcwtGCWVntnKqyF743Wcixkt')
    db = deta.Base('ordenesCompra')
    fetch = db.fetch({'PROVEEDOR':proveedor})
    producto = pd.DataFrame(fetch.items)
    producto = producto['PRODUCTO'].unique()[0]
    db = deta.Base('main')
    fetch = db.fetch({'PRODUCTO':producto})
    results = pd.DataFrame(fetch.items)
    while(fetch.last != None):
        fetch = db.fetch({'PRODUCTO':producto}, last=fetch.last)
        results = results.append(fetch.items)
    
    results['HORA'] = results['HORA'].str.replace('am','')
    results['HORA'] = results['HORA'].str.replace('pm', '')
    results['FECHA'] = pd.to_datetime(results['FECHA'] + '' + results['HORA'], format='%Y-%m-%d%H:%M')
    
    return results, producto

st.set_page_config(
        page_title="Inicio Panel Proveedores",
        page_icon="👋",
    )

def add_logo():
    st.sidebar.image("welogo.png", use_column_width=True)

def run():
    add_logo()
    st.write("# Panel para Proveedores")

    with open('credentials.yaml') as file:
        config = yaml.safe_load(file)
    
    theme_date = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-clock'}
    theme_pax = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-user'}
    theme_year = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-calendar'}
    theme_month = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-calendar'}
    theme_desc = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-tag'}
    theme_price = {'bgcolor': '#f9f9f9','title_color': 'black','content_color': 'black','icon_color': 'black', 'icon': 'fa fa-credit-card'}

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    st.session_state["name"], st.session_state["authentication_status"], st.session_state["username"] = authenticator.login('Login', 'main')

    if st.session_state["authentication_status"]:
        st.write('# Bievenido, ' + st.session_state['name'])
        st.write('')
        df, producto = get_product(st.session_state['name'])
        st.write('## Estadisticas')
        cols = st.columns(2)
        today = datetime.date.today()
        now = datetime.datetime.now()
        currentMonth = today.month
        currentYear = today.year
        plazasCY = df[df['FECHA'].dt.year == currentYear]
        plazasCY = plazasCY['PAX'].sum()
        plazasCM = df[df['FECHA'].dt.month == currentMonth]
        plazasCM = plazasCM['PAX'].sum()
        with cols[0]:
            hc.info_card(title='PAX Año', content=str(plazasCY) + ' Plazas',theme_override=theme_year)
        with cols[1]:
            hc.info_card(title='PAX Mes', content=str(plazasCM) + ' Plazas',theme_override=theme_month)
        df = df.sort_index()
        df = df.groupby(df['FECHA']).sum()
        nearest = df.truncate(before=now)
        nearest = nearest.reset_index()
        st.write('## Proximo Evento')
        cols = st.columns(2)
        with cols[0]:
            hc.info_card(title='Fecha', content=str(nearest.iloc[0]['FECHA'].strftime('%d-%m-%Y %H:%M')),theme_override=theme_date)
        with cols[1]:
            hc.info_card(title='Pax', content=str(nearest.iloc[0]['PAX']) + ' Plazas',theme_override=theme_pax)

        with open(st.session_state["username"] + ".pdf", "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        
        st.write('## Servicios')
        st.write('### Servicio 1')
        cols = st.columns(2)
        with cols[0]:
            hc.info_card(title='Descripción', content='Texto aqui',theme_override=theme_desc)
        with cols[1]:
            hc.info_card(title='PVP', content='Precio aqui',theme_override=theme_price)
    
        st.write('## Contrato')
        with st.expander("Ver Contrato"):
            displayPDF(st.session_state["username"] + ".pdf")

        st.download_button(label="Descargar Contrato",
                    data=PDFbyte,
                    file_name="contrato.pdf",
                    mime='application/octet-stream')
    


    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
            


    


if __name__ == "__main__":
    run()
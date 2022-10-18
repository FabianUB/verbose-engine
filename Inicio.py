import asyncio
from lib2to3.pytree import convert
from math import prod
from operator import index
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.switch_page_button import switch_page
import hydralit_components as hc
import numpy as np
import datetime
from datetime import datetime
from st_aggrid import AgGrid
import pandas as pd
import altair as alt
from streamlit.hello.utils import show_code
from streamlit_option_menu import option_menu
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
from PIL import Image
import json

def intro():
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
    """, unsafe_allow_html=True)
    selected = option_menu(None, ["Inicio", "Calendario", "Finance"], 
        icons=['house', 'calendar', 'clipboard-data', 'box-arrow-in-left'], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    if selected == "Inicio":
        pass
    elif selected == "Calendario":
        st.warning("Funciona")
        switch_page("Calendario")
    elif selected == "Finance":
        switch_page("Finance")

    image = Image.open('banner.png')
    st.image(image, use_column_width='always')
    st.write("""
    <style>
    @import url('https://fonts.googleapis.com/css?family=Barlow Condensed' rel='stylesheet'');
    html, body, [class*="css"]  {
    font-family: 'Barlow Condensed';
    }
    </style>
    """, unsafe_allow_html=True)

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
    productos = producto['PRODUCTO'].unique()
    db = deta.Base('main')
    results = pd.DataFrame()
    for producto in productos:
        fetch = db.fetch({'PRODUCTO':producto})
        while(fetch.last != None):
            fetch = db.fetch({'PRODUCTO':producto}, last=fetch.last)
            results = results.append(fetch.items)
    
    results['SISTEMA'] = results['HORA'].apply(lambda x: x[-2:])
    results['HORA'] = results['HORA'].astype(str)
    results['HORA'] = results['HORA'].str.replace('am','')
    results['HORA'] = results['HORA'].str.replace('pm', '')
    results['HORA'] = pd.to_datetime(results['HORA'], format="%H:%M")
    condition = (results['HORA'].dt.hour < 12) & (results['SISTEMA'] == 'pm')
    results.loc[condition, 'HORA']  = results.loc[condition, 'HORA'] + datetime.timedelta(hours=12)
    results['HORA'] = results['HORA'].apply(lambda x : x.strftime('%H:%M'))
    results['FECHA'] = pd.to_datetime(results['FECHA'] + '' + results['HORA'], format='%Y-%m-%d%H:%M')
    
    return results, productos

def card(fecha, producto, plazas, nproductos):
    rem = int(60 / nproductos)
    return f"""
    <div class="card my-0 pb-0 border-dark border-5" style="width: {rem}rem; margin: 0 auto; float: none;">
        <div class='card-header my-0 pb-0 d-flex flex-column'>
            <h2 class="card-title text-center">{producto}</h2>
        </div>
        <div class="card-body my-0 pb-0 d-flex flex-column">
            <h3 class="card-title text-center">{fecha}</h3>
            <h3 class="card-title text-center">{plazas} PAX</h3>
        </div>
    </div>
    """

def cardStats(title, amount):
    return f"""
    <div class="card my-0 pb-0 border-dark border-5" style="width: 32rem; margin: 0 auto; float: none;">
        <div class='card-header my-0 pb-0 d-flex flex-column'>
            <h2 class="card-title text-center">{title}</h2>
        </div>
        <div class="card-body my-0 pb-0 d-flex flex-column">
            <h3 class="card-title text-center">{amount} €</h3>
        </div>
    </div>
    """

def showEvents(df, productos):
    st.write('## PRÓXIMOS EVENTOS')
    numProd = len(productos)
    cols = st.columns(numProd)
    for x in range(0,numProd):
        df2 = df
        df2 = df2.iloc[: , :-3]
        producto = productos[x]
        df2 = df2.loc[df2['PRODUCTO'] == producto, ['BOOKING ID', 'FECHA', 'PAX', 'PRODUCTO']]
        df2 = df2.reset_index(drop=True)
        df2 = df2.sort_index()
        df2 = df2.groupby(df2['FECHA']).sum()
        df2 = df2.sort_index()
        now = datetime.datetime.now()
        nearest = df2.truncate(before=now)
        nearest = nearest.reset_index()
        cols[x].markdown(card(nearest.iloc[0]['FECHA'].strftime('%d-%m-%Y %H:%M'), producto, nearest.iloc[0]['PAX'], numProd), unsafe_allow_html=True)
def showStats(df, productos):
    st.write('## SALES')
    cols = st.columns(2)
    today = datetime.date.today()
    now = datetime.datetime.now()
    earliest = df['FECHA'].min()
    latest = df['FECHA'].max()
    currentMonth = today.month
    currentYear = today.year
    plazasCY = df[df['FECHA'].dt.year == currentYear]
    plazasCY = plazasCY['TOTAL BRUTO'].sum()
    plazasCM = df[df['FECHA'].dt.month == currentMonth]
    plazasCM = plazasCM['TOTAL BRUTO'].sum()
    cols = st.columns(2)
    cols[0].markdown(cardStats('FACTURACIÓN ANUAL', round(plazasCY, 2)), unsafe_allow_html=True)
    cols[1].markdown(cardStats('FACTURACIÓN MENSUAL', round(plazasCM, 2)), unsafe_allow_html=True)
    df = df.groupby(df['FECHA'].dt.month).sum()
    indexMap = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
    df = df.rename(indexMap)
    fig = px.bar(df, x=df.index, y='TOTAL BRUTO')
    st.plotly_chart(fig, use_container_width=True)

def showFeedback():
    st.write('## RATINGS')
    with open(st.session_state["username"] + ".json") as json_file:
        data = json.load(json_file)
    airbnb = Image.open('airbnb.png')
    tripadvisor = Image.open('tripadvisor.png')
    gyg = Image.open('gyg.png')
    expedia = Image.open('expedia.png')
    cols = st.columns(4)
    cols[0].image(airbnb)
    cols[1].image(tripadvisor)
    cols[2].image(gyg)
    cols[3].image(expedia)
    cols = st.columns(4)
    airbnbRating = str(data['airbnb']) + ' ⭐'
    tripadvisorRating = str(data['tripadvisor']) + ' ⭐'
    gygRating = str(data['getyourguide']) + ' ⭐'
    expediaRating = str(data['expedia']) + ' ⭐'
    cols[0].metric('Airbnb',airbnbRating)
    cols[1].metric('TripAdvisor',tripadvisorRating)
    cols[2].metric('GetYourGuide',gygRating)
    cols[3].metric('Expedia',expediaRating)

def showBadFeedback():
    st.write('## NEGATIVE FEEDBACK')
    with open(st.session_state["username"] + ".json") as json_file:
        data = json.load(json_file)
    text1 = data['badreview1']
    fecha1 = data['fechabad1']
    estrella1 = data['estrellabad1']
    cols = st.columns(3)
    cols[0].write(text1)
    cols[1].write(fecha1)
    cols[2].write(estrella1 + ' ⭐')
    text2 = data['badreview2']
    fecha2 = data['fechabad2']
    estrella2 = data['estrellabad2']
    cols = st.columns(3)
    cols[0].write(text2)
    cols[1].write(fecha2)
    cols[2].write(estrella2 + ' ⭐')
    text3 = data['badreview3']
    fecha3 = data['fechabad3']
    estrella3 = data['estrellabad3']
    cols = st.columns(3)
    cols[0].write(text3)
    cols[1].write(fecha3)
    cols[2].write(estrella3 + ' ⭐')
def showContrato():
    st.write('## CONTRATO')
    try:
        with open(st.session_state["username"] + ".pdf", "rb") as pdf_file:
            PDFbyte = pdf_file.read()
    
        
        with st.expander("Ver Contrato"):
            displayPDF(st.session_state["username"] + ".pdf")
        
        st.download_button(label="Descargar Contrato",
                data=PDFbyte,
                file_name="contrato.pdf",
                mime='application/octet-stream')
    except:
        st.info('No se puede mostrar el contrato en estos momentos')


st.set_page_config(
        page_title="Inicio Panel Proveedores",
        page_icon="👋",
        initial_sidebar_state="collapsed",
        layout="wide"
    )

def add_logo():
    st.sidebar.image("welogo.png", use_column_width=True)

def run():
    intro()
    

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
        authenticator.logout('Logout', 'sidebar')
        df, productos = get_product(st.session_state['name'])
        
        showEvents(df, productos)
        st.write('\n \n')
        showStats(df, productos)
        st.write('\n \n')
        showFeedback()
        st.write('\n \n')
        showBadFeedback()
        st.write('\n \n')
        showContrato()
        
        


        
    


    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
            


    


if __name__ == "__main__":
    run()
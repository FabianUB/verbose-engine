from matplotlib.pyplot import text, title
import streamlit as st
import streamlit.components.v1 as components
from streamlit.logger import get_logger
from streamlit_option_menu import option_menu
from fileinput import filename
import pandas as pd
from st_aggrid import AgGrid
import os
import time
import datetime
import calendar
import streamlit as st
import streamlit_authenticator as stauth
from mplcal import MplCalendar
from deta import Deta
from PIL import Image
import unittest
import yaml
from streamlit_extras.switch_page_button import switch_page
from PIL import Image

def intro(authenticator):
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
    """, unsafe_allow_html=True)
    selected = option_menu(None, ["Inicio", "Calendario", "Finance"], 
        icons=['house', 'calendar', 'clipboard-data', 'box-arrow-in-left'], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    if selected == "Inicio":
        switch_page("Inicio")
    elif selected == "Calendario":
        pass
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
def add_logo():
    st.sidebar.image("welogo.png", use_column_width=True)

def get_product(proveedor, firstDayMonth, lastDayMonth):
    deta = Deta('a0kv6ay3_MBndet58XcwtGCWVntnKqyF743Wcixkt')
    db = deta.Base('ordenesCompra')
    fetch = db.fetch({'PROVEEDOR':proveedor})
    producto = pd.DataFrame(fetch.items)
    if len(producto['PRODUCTO'].unique()) == 1:
        producto = producto['PRODUCTO'].unique()[0]
        db = deta.Base('main')
        fetch = db.fetch({'PRODUCTO':producto})
        results = pd.DataFrame(fetch.items)
        while(fetch.last != None):
            fetch = db.fetch({'PRODUCTO':producto}, last=fetch.last)
            results = results.append(fetch.items)
    elif len(producto['PRODUCTO'].unique()) > 1:
        producto = producto['PRODUCTO'].unique()
        db = deta.Base('main')
        results = pd.DataFrame()
        for x in producto:
            fetch = db.fetch({'PRODUCTO':x})
            while(fetch.last != None):
                fetch = db.fetch({'PRODUCTO':x}, last=fetch.last)
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
    results = results.query('`FECHA` >= @firstDayMonth and `FECHA` <= @lastDayMonth')
    results = results.groupby([results['FECHA'], results['PRODUCTO']], as_index=False).sum()
    
    
    return results
    

st.set_page_config(
        page_title="Calendario",
        page_icon="????",
        initial_sidebar_state="collapsed",
        layout="wide"
)

with open('credentials.yaml') as file:
    add_logo()
    config = yaml.safe_load(file)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    intro(authenticator)
    st.session_state["name"], st.session_state["authentication_status"], st.session_state["username"] = authenticator.login('Login', 'main')

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar')
    st.write("# Calendario")
    
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.write(st.session_state['name'])
    today = datetime.date.today()
    currentMonth = today.month
    currentYear = today.year
    year = st.selectbox('A??o', range(2022, 2023), index=0)
    month = st.selectbox('Mes', range(1, 13), index=currentMonth-1)
    firstDayOfMonth = datetime.date(year, month, 1)
    lastDayofMonth = datetime.date(year, month, calendar.monthrange(year, month)[1])
    results = get_product(st.session_state['name'], firstDayOfMonth, lastDayofMonth)
    columns = ['FECHA', 'PAX', 'COSTE INDIVIDUAL', 'COSTE TOTAL', 'PRODUCTO', 'HORA']
    results['DIA'] = results['FECHA'].dt.dayofweek
    cal = MplCalendar(year, month)
    for index, row in results.iterrows():
        fecha = row['FECHA'].day
        sistema = ''
        if row['FECHA'].hour < 12:
            sistema = "AM"
        else:
            sistema = "PM"
        infoPax = 'Pax: ' + str(row['PAX'])
        texto = row['PRODUCTO'] + "(" + sistema + ")" + "\n" + infoPax
        cal.add_event(fecha, texto)
    
    st.pyplot(cal.show())
        
    
        
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')
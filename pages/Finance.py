from lib2to3.pytree import convert
from operator import index
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
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
import calendar
import io
from deta import Deta
from urllib.error import URLError
import yaml
from streamlit_extras.switch_page_button import switch_page
from PIL import Image

def intro():
    st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
    """, unsafe_allow_html=True)
    selected = option_menu(None, ["Inicio", "Calendario", "Finance"], 
        icons=['house', 'calendar', 'clipboard-data'], 
        menu_icon="cast", default_index=2, orientation="horizontal")
    if selected == "Inicio":
        switch_page("Inicio")
    elif selected == "Calendario":
        switch_page("Calendario")
    elif selected == "Finance":
        pass
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

def get_data_cleaned(proveedor, startDate, endDate):
    deta = Deta('a0kv6ay3_MBndet58XcwtGCWVntnKqyF743Wcixkt')
    db = deta.Base('ordenesCompra')
    fetch = db.fetch({'PROVEEDOR':proveedor})
    results = pd.DataFrame(fetch.items)
    while(fetch.last != None):
        fetch = db.fetch({'PROVEEDOR':proveedor}, last=fetch.last)
        results = results.append(fetch.items)
    results['FECHA'] = pd.to_datetime(results['FECHA'])
    results = results.query('`FECHA` >= @startDate and `FECHA` <= @endDate')
    return results
def add_logo():
    st.sidebar.image("welogo.png", use_column_width=True)

def run():
    intro()

    st.write("# Finance")

    with open('credentials.yaml') as file:
        config = yaml.safe_load(file)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )


    st.session_state["name"], st.session_state["authentication_status"], st.session_state["username"] = authenticator.login('Login', 'main')

    if st.session_state["authentication_status"]:
        cols = st.columns(2)
        currentDate = datetime.date.today()
        firstDayOfMonth = datetime.date(currentDate.year, currentDate.month, 1)
        currentDate = datetime.date.today()
        lastDayOfMonth = datetime.date(currentDate.year, currentDate.month, calendar.monthrange(currentDate.year, currentDate.month)[1])
        start = cols[0].date_input('Fecha Inicio', firstDayOfMonth)
        end = cols[1].date_input('Fecha Fin', lastDayOfMonth)
        results = get_data_cleaned(st.session_state["name"], start, end)
        columns = ['FECHA', 'PAX', 'COSTE INDIVIDUAL', 'COSTE TOTAL', 'PRODUCTO', 'HORA']
        results['FECHA'] = results['FECHA'].dt.strftime('%d/%m/%Y')
        results = results[columns]
        results['COSTE INDIVIDUAL'] = results['COSTE INDIVIDUAL'].map('{:,.2f}€'.format)
        costeTotalSum = results['COSTE TOTAL'].sum()
        costeTotalMean = results['COSTE TOTAL'].mean()
        results['COSTE TOTAL'] = results['COSTE TOTAL'].map('{:,.2f}€'.format)
        AgGrid(results)

        
        paxTotal = results['PAX'].astype(int)
        cols = st.columns(2)
        diasDeOperacion = cols[0].metric('Dias de Operación', str(len(results.index)))
        importeTotal = cols[1].metric('Importe Total', str(round(costeTotalSum, 2)) + '€')
        cols = st.columns(2) 
        paxMedia = cols[0].metric('Media Pax Dia', str(round(paxTotal.mean(), 2)))
        euroMedia = cols[1].metric('Importe Medio', str(round(costeTotalMean, 2)) + '€')

    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
            



if __name__ == "__main__":
    st.set_page_config(
        page_title="Finance",
        page_icon="👋",
        initial_sidebar_state="collapsed",
        layout="wide"
    )
    run()
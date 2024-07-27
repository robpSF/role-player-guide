import re
import os
import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from fpdf import FPDF
import tempfile

# Function to split the permissions and expand the dataframe
def split_permissions(df, column):
    # Split the permissions by comma
    df[column] = df[column].str.split(',')
    # Explode the DataFrame so that each permission has its own row
    return df.explode(column)

# Function to replace emojis with "~" in the PDF output
def replace_emojis(text):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002500-\U00002BEF"  # chinese char
                           u"\U00002702-\U000027B0"
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           u"\U0001f926-\U0001f937"
                           u"\U00010000-\U0010ffff"
                           u"\u2640-\u2642"
                           u"\u2600-\u2B55"
                           u"\u200d"
                           u"\u23cf"
                           u"\u23e9"
                           u"\u231a"
                           u"\ufe0f"  # dingbats
                           u"\u3030"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'~', text)

# Function to create PDF
class PDF(FPDF):
    pass

def create_pdf(df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    grouped = df.groupby('Permissions')
    
    for permission, group in grouped:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt=replace_emojis(permission.strip()), ln=True, align='L')
        
        for index, row in group.iterrows():
            pdf.set_font("Arial", style='', size=10)
            
            # Add image if available
            y_before = pdf.get_y()
            if row['Image']:
                try:
                    response = requests.get(row['Image'])
                    image = Image.open(BytesIO(response.content))
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        image.save(tmpfile.name)
                        pdf.image(tmpfile.name, x=10, y=y_before, w=30, h=30)
                except Exception as e:
                    print(f"Error loading image: {e}")
            
            # Add text details next to the image
            pdf.set_xy(45, y_before)  # Set x position next to the image
            line_height = 6  # Adjust line height here
            text = (f"Name: {replace_emojis(row.get('Name', ''))}\n"
                    f"Handle: {replace_emojis(row['Handle'])}\n"
                    f"Faction: {replace_emojis(row.get('Faction', ''))}\n"
                    f"Beliefs: {replace_emojis(row.get('Beliefs', ''))}\n"
                    f"Tags: {replace_emojis(row.get('Tags', ''))}\n"
                    f"Bio: {replace_emojis(row['Bio'])}\n")
            pdf.multi_cell(0, line_height, txt=text)
            pdf.cell(0, line_height, ln=True)
        pdf.cell(0, line_height, ln=True, border='B')
        
    return pdf.output(dest='S').encode('latin1')

# Streamlit app
st.title('Persona and Permissions Matcher')

# File uploader for persona details
persona_file = st.file_uploader("Upload Persona Details File", type=["xlsx"])
# File uploader for permissions
permissions_file = st.file_uploader("Upload Permissions File", type=["xlsx"])

if persona_file and permissions_file:
    # Read the uploaded files
    persona_df = pd.read_excel(persona_file)
    permissions_df = pd.read_excel(permissions_file)
    
    # Merge dataframes on the Handle column, adding Bio and Image to permissions_df
    merged_df = pd.merge(permissions_df, persona_df[['Handle', 'Bio', 'Image']], on='Handle', how='left')
    
    # Replace NaN values with empty string
    merged_df.fillna('', inplace=True)
    
    # Split and expand the permissions
    expanded_df = split_permissions(merged_df, 'Permissions')
    
    # Display the expanded dataframe
    st.write("Expanded DataFrame", expanded_df)
    
    # Group by individual Permissions
    grouped = expanded_df.groupby('Permissions')

    # Create a subheader for each permission and display the image and bio
    for permission, group in grouped:
        st.subheader(permission.strip())
        for index, row in group.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                if row['Image']:
                    try:
                        response = requests.get(row['Image'])
                        image = Image.open(BytesIO(response.content))
                        image = image.resize((100, 100))
                        st.image(image, caption=row['Handle'], width=100)
                    except Exception as e:
                        st.write("Error loading image:", e)
                else:
                    st.write("No image available")
            with col2:
                st.markdown(f"**Name:** {row.get('Name', '')}  \n"
                            f"**Handle:** {row['Handle']}  \n"
                            f"**Faction:** {row.get('Faction', '')}  \n"
                            f"**Beliefs:** {row.get('Beliefs', '')}  \n"
                            f"**Tags:** {row.get('Tags', '')}")
                st.write(row['Bio'])
        st.markdown('---')

    # Option to download the expanded dataframe as CSV
    @st.cache
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(expanded_df)
    
    st.download_button(
        "Download Expanded Data as CSV",
        csv,
        "expanded_data.csv",
        "text/csv",
        key='download-csv'
    )
    
    # Option to download the expanded dataframe as PDF
    pdf = create_pdf(expanded_df)
    
    st.download_button(
        "Download Expanded Data as PDF",
        pdf,
        "expanded_data.pdf",
        "application/pdf",
        key='download-pdf'
    )

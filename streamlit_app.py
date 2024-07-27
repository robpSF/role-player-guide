import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from fpdf import FPDF

# Function to split the permissions and expand the dataframe
def split_permissions(df, column):
    # Split the permissions by comma
    df[column] = df[column].str.split(',')
    # Explode the DataFrame so that each permission has its own row
    return df.explode(column)

# Function to create PDF
def create_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    grouped = df.groupby('Permissions')
    
    for permission, group in grouped:
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, txt=permission.strip(), ln=True, align='L')
        
        for index, row in group.iterrows():
            pdf.set_font("Arial", style='', size=12)
            pdf.multi_cell(0, 10, txt=f"Name: {row.get('Name', '')}\n"
                                      f"Handle: {row['Handle']}\n"
                                      f"Faction: {row.get('Faction', '')}\n"
                                      f"Beliefs: {row.get('Beliefs', '')}\n"
                                      f"Tags: {row.get('Tags', '')}\n"
                                      f"Bio: {row['Bio']}\n")
            pdf.cell(0, 10, ln=True)
        pdf.cell(0, 10, ln=True, border='B')
        
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

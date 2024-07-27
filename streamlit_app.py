import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO

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
    
    # Merge dataframes on the Handle column
    merged_df = pd.merge(permissions_df, persona_df, on='Handle', how='left')
    
    # Reorder the columns
    merged_df = merged_df[['Name', 'Handle', 'Faction', 'Permissions', 'Bio', 'Image']]
    
    # Display the merged dataframe
    st.write("Merged DataFrame", merged_df)
    
    # Create a subheader for each permission and display the image and bio
    for index, row in merged_df.iterrows():
        st.subheader(f"{row['Handle']}")
        col1, col2 = st.columns([1, 3])
        with col1:
            if pd.notna(row['Image']):
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
            st.markdown(f"**Name:** {row['Name']}")
            st.markdown(f"**Handle:** {row['Handle']}")
            st.markdown(f"**Faction:** {row['Faction']}")
            st.markdown(f"**Permissions:** {row['Permissions']}")
            st.write(row['Bio'])

    # Option to download the merged dataframe
    @st.cache
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(merged_df)
    
    st.download_button(
        "Download Merged Data",
        csv,
        "merged_data.csv",
        "text/csv",
        key='download-csv'
    )

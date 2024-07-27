import streamlit as st
import pandas as pd

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
    merged_df = pd.merge(permissions_df, persona_df[['Handle', 'Bio', 'Image']], on='Handle', how='left')
    
    # Display the merged dataframe
    st.write("Merged DataFrame", merged_df)
    
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

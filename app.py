import streamlit as st
import pandas as pd
import re
import io
import altair as alt

st.set_page_config(page_title="Data Transformation Automation", layout="wide")

st.title("Sales Data")
st.write("Test")

uploaded_file = st.file_uploader("Upload Excel File (e.g. SalesDetails.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Read data assuming the header is on the 7th row (skip rows 0-5)
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Validate required columns
        required_cols = ['Category', 'Item', 'Gross Amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"The following columns are missing from the table: {', '.join(missing_cols)}.\nPlease ensure the uploaded table has its header on the 7th row.")
        else:
            # 1. Filter rows with Category "01-Ticketing" or "TC01-Ticket Cartenz"
            valid_categories = ["01-Ticketing", "TC01-Ticket Cartenz"]
            df_filtered = df[df['Category'].isin(valid_categories)].copy()
            
            # 2. Create new columns
            df_filtered['New Category'] = 'null'
            df_filtered['Source'] = 'null'
            
            indices_to_drop = []
            
            # 3 & 4. Item Identification
            for idx, row in df_filtered.iterrows():
                item = str(row['Item']).strip()
                item_lower = item.lower()
                category = str(row['Category'])
                gross_amt = row['Gross Amount']
                
                # Try parsing gross_amt into float if possible
                try:
                    gross_amt_val = float(gross_amt)
                except (ValueError, TypeError):
                    gross_amt_val = None
                
                # Check for Socks first (ends with XXS, XS, S, M, L)
                if re.search(r'\b(XXS|XS|S|M|L)$', item, re.IGNORECASE):
                    df_filtered.at[idx, 'Source'] = 'kaos kaki'
                    
                    # Exclude row if Source is "kaos kaki" and Gross Amount is 0
                    if gross_amt_val == 0:
                        indices_to_drop.append(idx)
                        
                    continue # Move to next row since no ticket pattern applies to socks
                
                # Initialize defaults to 'null'
                new_cat = 'null'
                source = 'null'
                
                # --- IDENTIFY NEW CATEGORY ---
                if re.search(r'2\s*jam', item_lower):
                    new_cat = 'Tiket Bermain - 2 Jam'
                elif re.search(r'3\s*jam', item_lower):
                    new_cat = 'Tiket Bermain - 3 Jam'
                elif re.search(r'(1\s*comp|companion\s*1)', item_lower):
                    new_cat = 'Tiket Pendamping - 1 Orang'
                elif re.search(r'(2\s*comp|companion\s*2)', item_lower):
                    new_cat = 'Tiket Pendamping - 2 Orang'
                    
                # --- IDENTIFY SOURCE ---
                if new_cat == 'null':
                    source = 'null'

                elif 'blibli' in item_lower:
                    source = 'BLIBLI'

                elif re.search(r'tiket\s*com|ticket\s*com|tiket\.com|ticket\.com', item_lower):
                    source = 'TIKET.COM'

                elif 'website' in item_lower or 'web' in item_lower:
                    source = 'WEBSITE'

                elif re.search(r'skye|marshall|sbsp', item_lower):
                    source = 'KAOS KAKI'

                else:
                    source = 'WALK IN'
                
                df_filtered.at[idx, 'New Category'] = new_cat
                df_filtered.at[idx, 'Source'] = source

            # Apply row deletion for socks with Gross Amount 0
            df_result = df_filtered.drop(index=indices_to_drop)
            
            # Hide rows where both 'New Category' and 'Source' are 'null'
            df_result = df_result[~((df_result['New Category'] == 'null') & (df_result['Source'] == 'null'))]
            
            # Hide Unnamed: 0 column (if present)
            unnamed_cols = [col for col in df_result.columns if 'Unnamed:' in str(col)]
            if unnamed_cols:
                df_result = df_result.drop(columns=unnamed_cols)
            
            st.success("✅ File successfully processed!")
            
            # Important columns to preview
            display_cols = ['Category', 'Item', 'New Category', 'Source', 'Gross Amount']
            other_cols = [col for col in df_result.columns if col not in display_cols]
            df_display = df_result[display_cols + other_cols]
            
            st.write("### Transformation Result Preview:")
            st.dataframe(df_display, use_container_width=True)
            
            # Chart generation below the dataframe
            st.write("---")
            st.write("### Gross Amount by New Category")
            chart1_data = df_result[df_result['New Category'] != 'null'].groupby('New Category', as_index=False)['Gross Amount'].sum()
            if not chart1_data.empty:
                base1 = alt.Chart(chart1_data).encode(
                    x=alt.X('Gross Amount:Q', title='Gross Amount'),
                    y=alt.Y('New Category:N', sort='-x', title='New Category')
                )
                bars1 = base1.mark_bar()
                text1 = base1.mark_text(align='left', baseline='middle', dx=3).encode(
                    text=alt.Text('Gross Amount:Q', format=',.0f')
                )
                chart1 = (bars1 + text1).properties(height=300)
                st.altair_chart(chart1, use_container_width=True)
            else:
                st.info("No data available for New Category.")

            st.write("### Gross Amount by Source")
            chart2_data = df_result[df_result['Source'] != 'null'].groupby('Source', as_index=False)['Gross Amount'].sum()
            if not chart2_data.empty:
                base2 = alt.Chart(chart2_data).encode(
                    x=alt.X('Gross Amount:Q', title='Gross Amount'),
                    y=alt.Y('Source:N', sort='-x', title='Source')
                )
                bars2 = base2.mark_bar()
                text2 = base2.mark_text(align='left', baseline='middle', dx=3).encode(
                    text=alt.Text('Gross Amount:Q', format=',.0f')
                )
                chart2 = (bars2 + text2).properties(height=300)
                st.altair_chart(chart2, use_container_width=True)
            else:
                st.info("No data available for Source.")
                
            st.write("---")
            
            # Create Excel file for download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Sales_Data_Processed')
            
            processed_data = output.getvalue()
            
            st.download_button(
                label="📥 Download Result (.xlsx)",
                data=processed_data,
                file_name="SalesDetails_Processed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"A technical error occurred: {e}")

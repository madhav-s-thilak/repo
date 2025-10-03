import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Load state mapping + coordinates for India
STATE_COORDS = {
    "Andhra Pradesh": [15.9129, 79.74],
    "Arunachal Pradesh": [28.218, 94.7278],
    "Assam": [26.2006, 92.9376],
    "Bihar": [25.0961, 85.3131],
    "Chhattisgarh": [21.2787, 81.8661],
    "Goa": [15.2993, 74.124],
    "Gujarat": [22.2587, 71.1924],
    "Haryana": [29.0588, 76.0856],
    "Himachal Pradesh": [31.1048, 77.1734],
    "Jharkhand": [23.6102, 85.2799],
    "Karnataka": [15.3173, 75.7139],
    "Kerala": [10.8505, 76.2711],
    "Madhya Pradesh": [22.9734, 78.6569],
    "Maharashtra": [19.7515, 75.7139],
    "Manipur": [24.6637, 93.9063],
    "Meghalaya": [25.467, 91.3662],
    "Mizoram": [23.1645, 92.9376],
    "Nagaland": [26.1584, 94.5624],
    "Odisha": [20.9517, 85.0985],
    "Punjab": [31.1471, 75.3412],
    "Rajasthan": [27.0238, 74.2179],
    "Sikkim": [27.533, 88.5122],
    "Tamil Nadu": [11.1271, 78.6569],
    "Telangana": [18.1124, 79.0193],
    "Tripura": [23.9408, 91.9882],
    "Uttar Pradesh": [26.8467, 80.9462],
    "Uttarakhand": [30.0668, 79.0193],
    "West Bengal": [22.9868, 87.855],
    "Delhi": [28.7041, 77.1025],
    "Jammu and Kashmir": [33.7782, 76.5762],
    "Ladakh": [34.1526, 77.5771],
    "Puducherry": [11.9416, 79.8083],
    "Chandigarh": [30.7333, 76.7794],
    "Dadra and Nagar Haveli and Daman and Diu": [20.4283, 72.8397],
    "Lakshadweep": [10.5667, 72.6417],
    "Andaman and Nicobar Islands": [11.7401, 92.6586],
}

# Enhanced data cleaning functions
def clean_date(date_str):
    """Clean and standardize date formats"""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    
    return date_str

def clean_state_name(state):
    """Normalize only exact state/UT names; others become 'Unknown'."""
    if pd.isna(state) or not str(state).strip():
        return "Unknown"
    s = str(state).strip().upper()
    state_map = {
        "ANDHRA PRADESH":"Andhra Pradesh","ARUNACHAL PRADESH":"Arunachal Pradesh",
        "ASSAM":"Assam","BIHAR":"Bihar","CHHATTISGARH":"Chhattisgarh",
        "GOA":"Goa","GUJARAT":"Gujarat","HARYANA":"Haryana",
        "HIMACHAL PRADESH":"Himachal Pradesh","JHARKHAND":"Jharkhand",
        "KARNATAKA":"Karnataka","KERALA":"Kerala","MADHYA PRADESH":"Madhya Pradesh",
        "MAHARASHTRA":"Maharashtra","MANIPUR":"Manipur","MEGHALAYA":"Meghalaya",
        "MIZORAM":"Mizoram","NAGALAND":"Nagaland","ODISHA":"Odisha",
        "PUNJAB":"Punjab","RAJASTHAN":"Rajasthan","SIKKIM":"Sikkim",
        "TAMIL NADU":"Tamil Nadu","TELANGANA":"Telangana","TRIPURA":"Tripura",
        "UTTAR PRADESH":"Uttar Pradesh","UTTARAKHAND":"Uttarakhand","WEST BENGAL":"West Bengal",
        "DELHI":"Delhi","JAMMU AND KASHMIR":"Jammu and Kashmir","LADAKH":"Ladakh",
        "PUDUCHERRY":"Puducherry","CHANDIGARH":"Chandigarh",
        "DADRA AND NAGAR HAVELI AND DAMAN AND DIU":"Dadra and Nagar Haveli and Daman and Diu",
        "LAKSHADWEEP":"Lakshadweep","ANDAMAN AND NICOBAR ISLANDS":"Andaman and Nicobar Islands"
    }
    return state_map.get(s, "Unknown")


def clean_category_name(cat):
    """Return exactly one of CAT-1, CAT-2, CAT-3 per entry."""
    if pd.isna(cat) or not str(cat).strip():
        return "Unknown"
    c = str(cat).upper()
    if re.search(r'CAT[- ]?1|CATEGORY[- ]?1|\b1\b', c):
        return "CAT-1"
    if re.search(r'CAT[- ]?2|CATEGORY[- ]?2|\b2\b', c):
        return "CAT-2"
    if re.search(r'CAT[- ]?3|CATEGORY[- ]?3|\b3\b', c):
        return "CAT-3"
    return "Unknown"


def clean_single_category(category):
    """Clean a single category"""
    category = category.strip().upper()
    
    # Extract numbers from category string
    numbers = re.findall(r'\d+', category)
    
    # Check for specific patterns
    if any(x in category for x in ['CAT1', 'CAT 1', 'CAT-1', 'CATEGORY 1', 'CATEGORY1']) or '1' in numbers:
        return 'CAT-1'
    elif any(x in category for x in ['CAT2', 'CAT 2', 'CAT-2', 'CATEGORY 2', 'CATEGORY2']) or '2' in numbers:
        return 'CAT-2'
    elif any(x in category for x in ['CAT3', 'CAT 3', 'CAT-3', 'CATEGORY 3', 'CATEGORY3']) or '3' in numbers:
        return 'CAT-3'
    elif any(x in category for x in ['CAT4', 'CAT 4', 'CAT-4', 'CATEGORY 4', 'CATEGORY4']) or '4' in numbers:
        return 'CAT-4'
    
    # Default case
    return 'Unknown'

def clean_company_name(company):
    """Enhanced company name cleaning"""
    if pd.isna(company):
        return "Unknown Company"
    
    company = str(company).strip()
    
    # Remove extra spaces and normalize
    company = re.sub(r'\s+', ' ', company)
    
    # Fix common abbreviations
    company = company.replace(' Pvt Ltd', ' Pvt. Ltd.')
    company = company.replace(' Private Limited', ' Pvt. Ltd.')
    company = company.replace(' LLP', ' LLP')
    
    # Title case
    company = company.title()
    
    return company

def clean_capacity(capacity):
    """Enhanced capacity cleaning"""
    if pd.isna(capacity):
        return 0
    
    capacity_str = str(capacity).strip().upper()
    
    # Remove common units and symbols
    capacity_clean = re.sub(r'[^\d.-]', '', capacity_str)
    
    try:
        return float(capacity_clean) if capacity_clean else 0
    except:
        return 0

def clean_contact_number(contact):
    """Clean and standardize contact numbers"""
    if pd.isna(contact):
        return ""
    
    contact_str = str(contact)
    
    # Remove scientific notation
    if 'e+' in contact_str.lower():
        try:
            contact_str = f"{float(contact_str):.0f}"
        except:
            pass
    
    # Clean the contact number
    contact_clean = re.sub(r'[^\d,+\-\s()]', '', contact_str)
    
    return contact_clean.strip()

def clean_epr_status(status):
    """Clean EPR certification status"""
    if pd.isna(status):
        return "Not Specified"
    
    status = str(status).strip().upper()
    
    if any(x in status for x in ['CERTIFIED', 'YES', 'TRUE', 'DONE']):
        return 'Certified'
    elif any(x in status for x in ['NOT CERTIFIED', 'NO', 'FALSE']):
        return 'Not Certified'
    elif any(x in status for x in ['READY', 'READY TO']):
        return 'Ready To Certify'
    elif any(x in status for x in ['PROCESS', 'IN PROCESS']):
        return 'In Process'
    else:
        return 'Not Specified'

def clean_documents_status(status):
    """Clean document status"""
    if pd.isna(status):
        return "Not Specified"
    
    status = str(status).strip().upper()
    
    if any(x in status for x in ['WITH DOCUMENTS', 'WITH', 'YES', 'AVAILABLE']):
        return 'With Documents'
    elif any(x in status for x in ['WITHOUT', 'NO', 'NOT AVAILABLE']):
        return 'Without Documents'
    elif any(x in status for x in ['NOT SURE', 'UNSURE']):
        return 'Not Sure'
    else:
        return 'Not Specified'

def remove_duplicates(df):
    """Remove duplicate entries based on company name and contact"""
    # Create a composite key for duplicate detection
    df['duplicate_key'] = df['Company'].fillna('').str.upper() + '|' + df['Contact No.'].fillna('').str.replace(r'[^\d]', '', regex=True)
    
    # Keep first occurrence of each duplicate
    df_deduped = df.drop_duplicates(subset=['duplicate_key'], keep='first')
    df_deduped = df_deduped.drop('duplicate_key', axis=1)
    
    return df_deduped

# Replace the load_and_clean_data() function in your code with this updated version:

@st.cache_data(ttl=600)
def load_and_clean_data():
    """Load and clean both datasets directly from Google Sheets."""
    
    # Google Sheets CSV export URLs
    recyclers_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1yRg1dZQwxP-Uz81JaFSXCkyPxwChN_ot605kC-1tc1g"
        "/export?format=csv&gid=0"
    )
    positive_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1yRg1dZQwxP-Uz81JaFSXCkyPxwChN_ot605kC-1tc1g"
        "/export?format=csv&gid=1813673668"
    )

    import requests, io

    # Load recyclers data via requests to skip SSL verification
    try:
        resp = requests.get(recyclers_url, verify=False)
        resp.raise_for_status()
        recyclers_df = pd.read_csv(io.StringIO(resp.text), header=1)
        recyclers_df = recyclers_df[
            ['Date', 'Column 2', 'Name', 'Contact No.', 'Email',
             'EPR Certified', 'Documents', 'States', 'Category',
             'Capacity (MT/Annum)', 'Owner', 'Type', 'Remarks']
        ].copy()
        recyclers_df.rename(
            columns={'Column 2': 'Company', 'Capacity (MT/Annum)': 'Capacity'},
            inplace=True
        )
        st.success(f"✅ Loaded recyclers data: {len(recyclers_df)} entries")
    except Exception as e:
        st.error(f"❌ Error loading recyclers data: {e}")
        return None, None

    # Load positive leads data via requests
    try:
        resp2 = requests.get(positive_url, verify=False)
        resp2.raise_for_status()
        positive_df = pd.read_csv(io.StringIO(resp2.text))
        positive_df.rename(columns={'Capacity(Annum)': 'Capacity'}, inplace=True)
        st.success(f"✅ Loaded positive leads data: {len(positive_df)} entries")
    except Exception as e:
        st.error(f"❌ Error loading positive leads data: {e}")
        return None, None

    # Clean both datasets
    datasets = {'All Recyclers': recyclers_df, 'Positive Leads': positive_df}
    cleaned_datasets = {}

    for name, df in datasets.items():
        df_clean = df.copy()
        df_clean['Date'] = df_clean['Date'].apply(clean_date)
        df_clean['Company'] = df_clean['Company'].apply(clean_company_name)
        df_clean['States'] = df_clean['States'].apply(clean_state_name)
        df_clean['Category'] = df_clean['Category'].apply(clean_category_name)
        df_clean['Capacity'] = df_clean['Capacity'].apply(clean_capacity)
        df_clean['Contact No.'] = df_clean['Contact No.'].apply(clean_contact_number)
        df_clean['EPR Certified'] = df_clean['EPR Certified'].apply(clean_epr_status)
        df_clean['Documents'] = df_clean['Documents'].apply(clean_documents_status)
        df_clean = remove_duplicates(df_clean)
        df_clean['Data_Quality_Score'] = calculate_data_quality_score(df_clean)
        df_clean['Dataset'] = name
        cleaned_datasets[name] = df_clean

    return cleaned_datasets['All Recyclers'], cleaned_datasets['Positive Leads']


def calculate_data_quality_score(df):
    """Calculate data quality score for each row"""
    scores = []
    
    for _, row in df.iterrows():
        score = 0
        total_fields = 0
        
        # Check important fields
        fields_to_check = ['Company', 'States', 'Contact No.', 'EPR Certified', 'Category']
        
        for field in fields_to_check:
            total_fields += 1
            if pd.notna(row[field]) and str(row[field]).strip() not in ['', 'Unknown', 'Not Specified']:
                score += 1
        
        # Bonus for having capacity data
        if pd.notna(row['Capacity']) and row['Capacity'] > 0:
            score += 0.5
            total_fields += 0.5
        
        # Bonus for having email
        if pd.notna(row['Email']) and '@' in str(row['Email']):
            score += 0.5
            total_fields += 0.5
        
        scores.append((score / total_fields * 100) if total_fields > 0 else 0)
    
    return scores

# Streamlit App Configuration
st.set_page_config(
    page_title="Enhanced Plastic Waste Recyclers Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .data-quality-good { color: #28a745; font-weight: bold; }
    .data-quality-medium { color: #ffc107; font-weight: bold; }
    .data-quality-poor { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🏭 Enhanced Plastic Waste Recyclers Dashboard</h1>
    <p>Comprehensive analysis of plastic waste recycling companies across India</p>
</div>
""", unsafe_allow_html=True)

# Load data
recyclers_data, positive_data = load_and_clean_data()

if recyclers_data is not None and positive_data is not None:
    
    # Sidebar Configuration
    st.sidebar.markdown("### 🎛️ Dashboard Controls")
    
    # Dataset selection
    dataset_choice = st.sidebar.selectbox(
        "📊 Select Dataset",
        ["All Recyclers", "Positive Leads", "Combined View"],
        help="Choose which dataset to analyze"
    )
    
    # Determine which data to use
    if dataset_choice == "All Recyclers":
        df_to_use = recyclers_data
    elif dataset_choice == "Positive Leads":
        df_to_use = positive_data
    else:  # Combined View
        df_to_use = pd.concat([recyclers_data, positive_data], ignore_index=True)
    
    # Filters Section
    st.sidebar.markdown("### 🔍 Filters")
    
    # Company search
    company_search = st.sidebar.text_input(
        "🏢 Search Company Name",
        help="Type to search for specific companies"
    )
    
    # State filter
    available_states = sorted([s for s in df_to_use['States'].unique() if s != 'Unknown'])
    state_filter = st.sidebar.multiselect(
        "🗺️ Filter by State",
        available_states,
        help="Select one or more states"
    )
    
    # Category filter
    available_categories = [cat for cat in df_to_use['Category'].unique() if cat not in ['Unknown', '']]
    category_filter = st.sidebar.multiselect(
        "📦 Filter by Category",
        available_categories,
        help="Select one or more waste categories"
    )
    
    # EPR Status filter
    epr_statuses = df_to_use['EPR Certified'].unique()
    epr_filter = st.sidebar.multiselect(
        "📋 EPR Certification Status",
        epr_statuses,
        help="Filter by EPR certification status"
    )
    
    # Document Status filter
    doc_statuses = df_to_use['Documents'].unique()
    doc_filter = st.sidebar.multiselect(
        "📄 Document Status",
        doc_statuses,
        help="Filter by document availability"
    )
    
    # Owner filter
    owners = sorted([o for o in df_to_use['Owner'].unique() if pd.notna(o)])
    owner_filter = st.sidebar.multiselect(
        "👤 Filter by Owner",
        owners,
        help="Filter by data owner/collector"
    )
    
    # Capacity filter
    if df_to_use['Capacity'].max() > 0:
        capacity_range = st.sidebar.slider(
            "⚖️ Capacity Range (MT/Annum)",
            min_value=0,
            max_value=int(df_to_use['Capacity'].max()),
            value=(0, int(df_to_use['Capacity'].max())),
            help="Filter by processing capacity"
        )
    else:
        capacity_range = (0, 0)
    
    # Data Quality filter
    quality_threshold = st.sidebar.slider(
        "📊 Minimum Data Quality (%)",
        min_value=0,
        max_value=100,
        value=0,
        help="Filter by data quality score"
    )
    
    # Advanced Options
    with st.sidebar.expander("⚙️ Advanced Options"):
        show_duplicates = st.checkbox("Show Potential Duplicates", help="Highlight similar companies")
        show_contact_verified = st.checkbox("Show Contact Verified Only", help="Only show entries with valid contacts")
        show_email_available = st.checkbox("Show Email Available Only", help="Only show entries with email addresses")
    
    # Apply filters
    filtered_df = df_to_use.copy()
    
    if company_search:
        filtered_df = filtered_df[filtered_df['Company'].str.contains(company_search, case=False, na=False)]
    
    if state_filter:
        filtered_df = filtered_df[filtered_df['States'].isin(state_filter)]
    
    if category_filter:
        # Handle multi-category entries
        category_mask = filtered_df['Category'].apply(
            lambda x: any(cat in str(x) for cat in category_filter) if pd.notna(x) else False
        )
        filtered_df = filtered_df[category_mask]
    
    if epr_filter:
        filtered_df = filtered_df[filtered_df['EPR Certified'].isin(epr_filter)]
    
    if doc_filter:
        filtered_df = filtered_df[filtered_df['Documents'].isin(doc_filter)]
    
    if owner_filter:
        filtered_df = filtered_df[filtered_df['Owner'].isin(owner_filter)]
    
    if capacity_range[1] > 0:
        filtered_df = filtered_df[
            (filtered_df['Capacity'] >= capacity_range[0]) & 
            (filtered_df['Capacity'] <= capacity_range[1])
        ]
    
    if quality_threshold > 0:
        filtered_df = filtered_df[filtered_df['Data_Quality_Score'] >= quality_threshold]
    
    if show_contact_verified:
        filtered_df = filtered_df[filtered_df['Contact No.'].str.len() >= 10]
    
    if show_email_available:
        filtered_df = filtered_df[filtered_df['Email'].str.contains('@', na=False)]
    
    # Sorting options
    st.sidebar.markdown("### 🔄 Sorting Options")
    sort_columns = [col for col in filtered_df.columns if col not in ['Dataset']]
    sort_column = st.sidebar.selectbox("Sort by", sort_columns)
    sort_order = st.sidebar.selectbox("Sort Order", ["Ascending", "Descending"])
    
    # Apply sorting
    filtered_df = filtered_df.sort_values(
        by=sort_column,
        ascending=(sort_order == "Ascending")
    )
    
    # Main Dashboard Content
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_companies = len(filtered_df)
        st.metric(
            "🏢 Total Companies", 
            f"{total_companies:,}",
            help=f"Out of {len(df_to_use):,} total entries"
        )
    
    with col2:
        unique_states = filtered_df['States'].nunique()
        st.metric(
            "🗺️ States Covered", 
            unique_states,
            help="Number of unique states represented"
        )
    
    with col3:
        certified_companies = len(filtered_df[filtered_df['EPR Certified'] == 'Certified'])
        certification_rate = (certified_companies / total_companies * 100) if total_companies > 0 else 0
        st.metric(
            "📋 EPR Certified", 
            f"{certified_companies} ({certification_rate:.1f}%)",
            help="Companies with EPR certification"
        )
    
    with col4:
        total_capacity = filtered_df['Capacity'].sum()
        st.metric(
            "⚖️ Total Capacity", 
            f"{total_capacity:,.0f} MT/year",
            help="Combined processing capacity"
        )
    
    # Additional metrics row
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        avg_quality = filtered_df['Data_Quality_Score'].mean()
        quality_color = "🟢" if avg_quality >= 70 else "🟡" if avg_quality >= 40 else "🔴"
        st.metric(
            f"{quality_color} Avg Data Quality",
            f"{avg_quality:.1f}%",
            help="Average data completeness score"
        )
    
    with col6:
        with_documents = len(filtered_df[filtered_df['Documents'] == 'With Documents'])
        doc_rate = (with_documents / total_companies * 100) if total_companies > 0 else 0
        st.metric(
            "📄 With Documents",
            f"{with_documents} ({doc_rate:.1f}%)",
            help="Companies with required documents"
        )
    
    with col7:
        with_email = len(filtered_df[filtered_df['Email'].str.contains('@', na=False)])
        email_rate = (with_email / total_companies * 100) if total_companies > 0 else 0
        st.metric(
            "📧 Email Available",
            f"{with_email} ({email_rate:.1f}%)",
            help="Companies with email addresses"
        )
    
    
    with col8:
        positive_leads = len(filtered_df[
            (filtered_df['EPR Certified'] == 'Certified') & 
            (filtered_df['Documents'] == 'With Documents')
        ])

        lead_rate = (positive_leads / total_companies * 100) if total_companies > 0 else 0
    st.metric(
        "✅ Positive Leads",
        f"{positive_leads} ({lead_rate:.1f}%)",
        help="Companies with EPR Certified AND With Documents"
    )

    
    # Visualizations
    st.markdown("## 📊 Data Analysis & Visualizations")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", "🗺️ Geographic", "📦 Categories", "📋 EPR Status", "👥 Team Performance"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Companies by State
            state_counts = filtered_df['States'].value_counts().head(15)
            if not state_counts.empty:
                fig_bar = px.bar(
                    x=state_counts.values,
                    y=state_counts.index,
                    orientation='h',
                    title="Top 15 States by Company Count",
                    labels={'x': 'Number of Companies', 'y': 'State'},
                    color=state_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No state data available for visualization")
        
        with col2:
            # EPR Certification Status
            epr_counts = filtered_df['EPR Certified'].value_counts()
            if not epr_counts.empty:
                colors = ['#28a745', '#ffc107', '#17a2b8', '#6c757d', '#dc3545']
                fig_pie = px.pie(
                    values=epr_counts.values,
                    names=epr_counts.index,
                    title="EPR Certification Status Distribution",
                    color_discrete_sequence=colors[:len(epr_counts)]
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=500)
                st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab2:
        st.markdown("### 🗺️ Geographic Distribution")
        
        # Prepare map data
        map_data = filtered_df.copy()
        
        # Add coordinates
        map_data['lat'] = map_data['States'].map(
            lambda x: STATE_COORDS.get(x, [20.0, 78.0])[0] if x in STATE_COORDS else 20.0
        )
        map_data['lon'] = map_data['States'].map(
            lambda x: STATE_COORDS.get(x, [20.0, 78.0])[1] if x in STATE_COORDS else 78.0
        )
        
        # Add jitter to avoid overlapping
        np.random.seed(42)
        map_data['lat'] += np.random.uniform(-0.5, 0.5, len(map_data))
        map_data['lon'] += np.random.uniform(-0.5, 0.5, len(map_data))
        
        # Filter valid coordinates
        valid_map_data = map_data[(map_data['lat'] != 20.0) | (map_data['lon'] != 78.0)]
        
        if len(valid_map_data) > 0:
            st.map(valid_map_data[['lat', 'lon']], zoom=4)
            
            # State-wise capacity analysis
            st.markdown("### Capacity Analysis by State")
            capacity_by_state = filtered_df.groupby('States')['Capacity'].agg(['count', 'sum', 'mean']).round(2)
            capacity_by_state.columns = ['Company Count', 'Total Capacity (MT)', 'Avg Capacity (MT)']
            capacity_by_state = capacity_by_state[capacity_by_state['Total Capacity (MT)'] > 0].sort_values('Total Capacity (MT)', ascending=False)
            
            if not capacity_by_state.empty:
                st.dataframe(capacity_by_state.head(10), use_container_width=True)
        else:
            st.info("No valid geographic data available for mapping")
    
    with tab3:
        st.markdown("### 📦 Category Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution
            # Parse multiple categories
            all_categories = []
            for cat in filtered_df['Category'].dropna():
                if ',' in str(cat):
                    all_categories.extend([c.strip() for c in str(cat).split(',')])
                else:
                    all_categories.append(str(cat))
            
            cat_series = pd.Series(all_categories)
            cat_counts = cat_series.value_counts()
            
            if not cat_counts.empty:
                fig_cat = px.bar(
                    x=cat_counts.index,
                    y=cat_counts.values,
                    title="Waste Category Distribution",
                    labels={'x': 'Category', 'y': 'Number of Companies'},
                    color=cat_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig_cat.update_layout(height=400)
                st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Capacity by category
            category_capacity = []
            for _, row in filtered_df.iterrows():
                if pd.notna(row['Category']) and row['Capacity'] > 0:
                    if ',' in str(row['Category']):
                        cats = [c.strip() for c in str(row['Category']).split(',')]
                        for cat in cats:
                            category_capacity.append({'Category': cat, 'Capacity': row['Capacity'] / len(cats)})
                    else:
                        category_capacity.append({'Category': str(row['Category']), 'Capacity': row['Capacity']})
            
            if category_capacity:
                cap_df = pd.DataFrame(category_capacity)
                cap_summary = cap_df.groupby('Category')['Capacity'].sum().sort_values(ascending=False)
                
                fig_cap = px.bar(
                    x=cap_summary.index,
                    y=cap_summary.values,
                    title="Total Capacity by Category (MT/Year)",
                    labels={'x': 'Category', 'y': 'Capacity (MT/Year)'},
                    color=cap_summary.values,
                    color_continuous_scale='Plasma'
                )
                fig_cap.update_layout(height=400)
                st.plotly_chart(fig_cap, use_container_width=True)
        with tab4:
            st.markdown("### 📋 EPR Status Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # EPR Status Distribution Pie Chart
                epr_counts = filtered_df['EPR Certified'].value_counts()
                if not epr_counts.empty:
                    # Define better colors for EPR status
                    epr_colors = {
                        'Certified': '#28a745',      # Green
                        'Not Certified': '#dc3545',  # Red
                        'Ready To Certify': '#ffc107', # Yellow
                        'In Process': '#17a2b8',     # Blue
                        'Not Specified': '#6c757d'   # Gray
                    }
                    colors_list = [epr_colors.get(status, '#6c757d') for status in epr_counts.index]
                    
                    fig_epr_pie = px.pie(
                        values=epr_counts.values,
                        names=epr_counts.index,
                        title="📊 EPR Certification Status Distribution",
                        color_discrete_sequence=colors_list
                    )
                    fig_epr_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont_size=12,
                        pull=[0.1 if x == 'Certified' else 0 for x in epr_counts.index]  # Highlight certified
                    )
                    fig_epr_pie.update_layout(
                        height=500,
                        font=dict(size=12),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    st.plotly_chart(fig_epr_pie, use_container_width=True)
            
            with col2:
                # Document Status Distribution
                doc_counts = filtered_df['Documents'].value_counts()
                if not doc_counts.empty:
                    doc_colors = {
                        'With Documents': '#28a745',     # Green
                        'Without Documents': '#dc3545', # Red
                        'Not Sure': '#ffc107',          # Yellow
                        'Not Specified': '#6c757d'      # Gray
                    }
                    doc_colors_list = [doc_colors.get(status, '#6c757d') for status in doc_counts.index]
                    
                    fig_doc_pie = px.pie(
                        values=doc_counts.values,
                        names=doc_counts.index,
                        title="📄 Document Status Distribution",
                        color_discrete_sequence=doc_colors_list
                    )
                    fig_doc_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont_size=12,
                        pull=[0.1 if x == 'With Documents' else 0 for x in doc_counts.index]
                    )
                    fig_doc_pie.update_layout(
                        height=500,
                        font=dict(size=12),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    st.plotly_chart(fig_doc_pie, use_container_width=True)
            
            # Enhanced State-wise EPR Analysis
            st.markdown("### 🗺️ State-wise EPR Certification Analysis")
            
            # Create a better state vs EPR analysis
            state_epr_df = filtered_df.groupby(['States', 'EPR Certified']).size().reset_index(name='Count')
            
            if not state_epr_df.empty:
                # Get top 15 states by total companies
                top_states = filtered_df['States'].value_counts().head(15).index
                state_epr_filtered = state_epr_df[state_epr_df['States'].isin(top_states)]
                
                fig_state_epr = px.bar(
                    state_epr_filtered,
                    x='States',
                    y='Count',
                    color='EPR Certified',
                    title="EPR Certification Status by Top 15 States",
                    labels={'Count': 'Number of Companies', 'States': 'State'},
                    color_discrete_map={
                        'Certified': '#28a745',
                        'Not Certified': '#dc3545',
                        'Ready To Certify': '#ffc107',
                        'In Process': '#17a2b8',
                        'Not Specified': '#6c757d'
                    }
                )
                fig_state_epr.update_layout(
                    height=600,
                    xaxis_tickangle=-45,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    font=dict(size=11)
                )
                st.plotly_chart(fig_state_epr, use_container_width=True)
            
            # Summary Statistics Table
            st.markdown("### 📊 EPR & Document Summary by State")
            
            state_summary = filtered_df.groupby('States').agg({
                'Company': 'count',
                'EPR Certified': lambda x: sum(x == 'Certified'),
                'Documents': lambda x: sum(x == 'With Documents')
            }).round(0)
            
            state_summary.columns = ['Total Companies', 'EPR Certified', 'With Documents']
            state_summary['EPR Rate (%)'] = (state_summary['EPR Certified'] / state_summary['Total Companies'] * 100).round(1)
            state_summary['Doc Rate (%)'] = (state_summary['With Documents'] / state_summary['Total Companies'] * 100).round(1)
            
            # Sort by total companies and show top 15
            state_summary = state_summary.sort_values('Total Companies', ascending=False).head(15)
            
            # Style the dataframe
            def highlight_high_performance(row):
                styles = [''] * len(row)
                if row['EPR Rate (%)'] >= 50:
                    styles[3] = 'background-color: #d4edda; font-weight: bold'  # Light green
                elif row['EPR Rate (%)'] >= 25:
                    styles[3] = 'background-color: #fff3cd; font-weight: bold'  # Light yellow
                else:
                    styles[3] = 'background-color: #f8d7da'  # Light red
                    
                if row['Doc Rate (%)'] >= 50:
                    styles[4] = 'background-color: #d4edda; font-weight: bold'
                elif row['Doc Rate (%)'] >= 25:
                    styles[4] = 'background-color: #fff3cd; font-weight: bold'
                else:
                    styles[4] = 'background-color: #f8d7da'
                return styles
            
            styled_summary = state_summary.style.apply(highlight_high_performance, axis=1)
            st.dataframe(styled_summary, use_container_width=True)
    
    with tab5:
        st.markdown("### 👥 Team Performance Analysis")
        
        if 'Owner' in filtered_df.columns:
            owner_stats = filtered_df.groupby('Owner').agg({
                'Company': 'count',
                'EPR Certified': lambda x: sum(x == 'Certified'),
                'Data_Quality_Score': 'mean',
                'Capacity': 'sum'
            }).round(2)
            
            owner_stats.columns = ['Total Contacts', 'Certified Companies', 'Avg Data Quality (%)', 'Total Capacity (MT)']
            owner_stats['Certification Rate (%)'] = (owner_stats['Certified Companies'] / owner_stats['Total Contacts'] * 100).round(1)
            
            st.dataframe(owner_stats.sort_values('Total Contacts', ascending=False), use_container_width=True)
            
            # Team performance visualization
            fig_team = px.scatter(
                owner_stats.reset_index(),
                x='Total Contacts',
                y='Certification Rate (%)',
                size='Total Capacity (MT)',
                color='Avg Data Quality (%)',
                hover_name='Owner',
                title="Team Performance: Contacts vs Certification Success Rate",
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_team, use_container_width=True)


    # Data Table
    st.markdown("## 📋 Detailed Data Table")

    # Remove empty rows before displaying
    display_df = filtered_df.dropna(how='all')  # Remove completely empty rows
    display_df = display_df[display_df['Company'] != 'Unknown Company']  # Remove unknown companies

    # Column selection for display
    all_columns = ['Date', 'Company', 'States', 'Contact No.', 'Email',
                'EPR Certified', 'Documents', 'Category','Capacity', 'Owner', 'Type', 'Remarks',
                'Data_Quality_Score']

    available_columns = [col for col in all_columns if col in display_df.columns]

    display_columns = st.multiselect(
        "🎯 Select columns to display:",
        available_columns,
        default=['Date','Company', 'States', 'Contact No.', 'EPR Certified', 'Category', 'Capacity', 'Data_Quality_Score'],
        help="Choose which columns you want to see in the table"
    )

    if display_columns and len(display_df) > 0:
        # Show row count
        st.info(f"📊 Showing {len(display_df)} companies out of {len(filtered_df)} total entries")
        
        # Enhanced row coloring based on data quality and EPR status
        def highlight_rows(row):
            styles = [''] * len(row)
            
            # Data Quality coloring
            if 'Data_Quality_Score' in row.index:
                quality_score = row.get('Data_Quality_Score', 0)
                if quality_score >= 70:
                    base_color = '#d4edda'  # Light green
                elif quality_score >= 40:
                    base_color = '#fff3cd'  # Light yellow
                else:
                    base_color = '#f8d7da'  # Light red
            else:
                base_color = '#ffffff'  # White
            
            # EPR Status highlighting
            if 'EPR Certified' in row.index:
                epr_status = row.get('EPR Certified', '')
                if epr_status == 'Certified':
                    epr_color = '#c3e6cb'  # Green highlight
                elif epr_status == 'Ready To Certify':
                    epr_color = '#ffeaa7'  # Yellow highlight
                elif epr_status == 'In Process':
                    epr_color = '#b3d4fc'  # Blue highlight
                else:
                    epr_color = base_color
            else:
                epr_color = base_color
            
            # Apply styling
            for i in range(len(styles)):
                if display_columns[i] == 'EPR Certified':
                    styles[i] = f'background-color: {epr_color}; font-weight: bold'
                elif display_columns[i] == 'Data_Quality_Score':
                    styles[i] = f'background-color: {base_color}; font-weight: bold'
                else:
                    styles[i] = f'background-color: {base_color}'
            
            return styles
        
        # Format specific columns for better display
        display_data = display_df[display_columns].copy()
        
        # Format capacity column
        if 'Capacity' in display_columns:
            display_data['Capacity'] = display_data['Capacity'].apply(
                lambda x: f"{x:,.0f} MT" if pd.notna(x) and x > 0 else "Not Specified"
            )
        
        # Format data quality score
        if 'Data_Quality_Score' in display_columns:
            display_data['Data_Quality_Score'] = display_data['Data_Quality_Score'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Format contact numbers
        if 'Contact No.' in display_columns:
            display_data['Contact No.'] = display_data['Contact No.'].apply(
                lambda x: str(x) if pd.notna(x) and str(x) != '' else "Not Available"
            )
        
        # Apply styling and display
        try:
            styled_df = display_data.style.apply(highlight_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=500)
        except:
            # Fallback to regular dataframe if styling fails
            st.dataframe(display_data, use_container_width=True, height=500)
        
        # Add legend for color coding
        st.markdown("""
        **🎨 Color Legend:**
        - 🟢 **Green**: High data quality (70%+) or EPR Certified
        - 🟡 **Yellow**: Medium data quality (40-69%) or Ready to Certify
        - 🔵 **Blue**: EPR In Process
        - 🔴 **Red**: Low data quality (<40%) or issues
        """)
        
        
        # Quick stats about displayed data - FIXED to use original data
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            certified_count = len(display_df[display_df['EPR Certified'] == 'Certified'])
            st.metric("✅ EPR Certified", certified_count)

        with col2:
            with_docs = len(display_df[display_df['Documents'] == 'With Documents'])
            st.metric("📄 With Documents", with_docs)

        with col3:
            with_email = len(display_df[display_df['Email'].str.contains('@', na=False)])
            st.metric("📧 Email Available", with_email)

        with col4:
            positive_leads_bottom = len(display_df[
                (display_df['EPR Certified'] == 'Certified') & 
                (display_df['Documents'] == 'With Documents')
            ])


    else:
        st.warning("⚠️ No data to display. Please adjust your filters or select columns to show.")
        st.info("💡 Tip: Try reducing the data quality threshold or clearing some filters to see more results.") 
    
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; padding: 1rem;'>
    <small>Enhanced Plastic Waste Recyclers Dashboard | Data Analysis & Visualization Tool</small>
</div>
""", unsafe_allow_html=True)
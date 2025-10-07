import requests, io
import certifi
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

# Google Sheets CSV URLs
recyclers_url ="https://docs.google.com/spreadsheets/d/1yRg1dZQwxP-Uz81JaFSXCkyPxwChN_ot605kC-1tc1g/export?format=csv&gid=0"
positive_url = "https://docs.google.com/spreadsheets/d/1yRg1dZQwxP-Uz81JaFSXCkyPxwChN_ot605kC-1tc1g/export?format=csv&gid=1813673668"

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
    try:
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
    except Exception as e:
        return None

def clean_state_name(state):
    """Normalize only exact state/UT names; others become 'Unknown'."""
    try:
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
    except Exception as e:
        return "Unknown"

# FIXED CATEGORY HANDLING FUNCTIONS
def clean_category_name(cat):
    """Parse all categories and return a comma-separated string of standardized categories"""
    try:
        if pd.isna(cat) or not str(cat).strip():
            return "Unknown"
        
        c = str(cat).upper()
        categories = []
        
        # Split by common separators: comma, semicolon, slash, ampersand, plus
        parts = re.split(r'[,;/&+]', c)
        
        for part in parts:
            part = part.strip()
            if re.search(r'CAT[- ]?1|CATEGORY[- ]?1|\b1\b', part):
                if "CAT-1" not in categories:
                    categories.append("CAT-1")
            elif re.search(r'CAT[- ]?2|CATEGORY[- ]?2|\b2\b', part):
                if "CAT-2" not in categories:
                    categories.append("CAT-2")
            elif re.search(r'CAT[- ]?3|CATEGORY[- ]?3|\b3\b', part):
                if "CAT-3" not in categories:
                    categories.append("CAT-3")
            elif re.search(r'CAT[- ]?4|CATEGORY[- ]?4|\b4\b', part):
                if "CAT-4" not in categories:
                    categories.append("CAT-4")
            elif re.search(r'CAT[- ]?5|CATEGORY[- ]?5|\b5\b', part):
                if "CAT-5" not in categories:
                    categories.append("CAT-5")
        
        return ", ".join(categories) if categories else "Unknown"
    except Exception as e:
        return "Unknown"

# HELPER FUNCTION FOR CATEGORY PARSING
def parse_categories(cat):
    """Parse categories and return as a list"""
    try:
        if pd.isna(cat) or not str(cat).strip():
            return ["Unknown"]
        
        c = str(cat).upper()
        categories = []
        
        # Split by common separators
        parts = re.split(r'[,;/&+]', c)
        
        for part in parts:
            part = part.strip()
            if re.search(r'CAT[- ]?1|CATEGORY[- ]?1|\b1\b', part):
                if "CAT-1" not in categories:
                    categories.append("CAT-1")
            elif re.search(r'CAT[- ]?2|CATEGORY[- ]?2|\b2\b', part):
                if "CAT-2" not in categories:
                    categories.append("CAT-2")
            elif re.search(r'CAT[- ]?3|CATEGORY[- ]?3|\b3\b', part):
                if "CAT-3" not in categories:
                    categories.append("CAT-3")
            elif re.search(r'CAT[- ]?4|CATEGORY[- ]?4|\b4\b', part):
                if "CAT-4" not in categories:
                    categories.append("CAT-4")
            elif re.search(r'CAT[- ]?5|CATEGORY[- ]?5|\b5\b', part):
                if "CAT-5" not in categories:
                    categories.append("CAT-5")
        
        return categories if categories else ["Unknown"]
    except Exception as e:
        return ["Unknown"]

# FIXED FUNCTION TO GET UNIQUE INDIVIDUAL CATEGORIES FOR FILTER
def get_unique_categories(df):
    """Get unique individual categories for the filter dropdown (not combinations), including Unknown"""
    try:
        unique_cats = set()
        
        for cat_string in df['Category'].dropna().unique():
            if cat_string:
                # Parse the individual categories from each string
                parsed_cats = parse_categories(cat_string)
                unique_cats.update(parsed_cats)
        
        # Include 'Unknown' as requested
        return sorted(list(unique_cats))
    except Exception as e:
        return ["Unknown"]

# CRITICAL FIX: Function to calculate distributed capacity per category
def get_distributed_capacity(row):
    """
    FIXED: Calculate the capacity distributed among categories for this company.
    If a company has CAT-1, CAT-2, CAT-3 and 300MT capacity,
    each category gets 300/3 = 100MT
    """
    try:
        if pd.isna(row['Category']) or pd.isna(row['Capacity']) or row['Capacity'] <= 0:
            return 0
        
        categories = parse_categories(row['Category'])
        # Remove 'Unknown' for distribution calculation
        valid_categories = [cat for cat in categories if cat != 'Unknown']
        
        if not valid_categories:
            return 0
        
        # Distribute capacity equally among valid categories
        return row['Capacity'] / len(valid_categories)
    except Exception as e:
        return 0

def clean_company_name(company):
    """Enhanced company name cleaning"""
    try:
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
    except Exception as e:
        return "Unknown Company"

def clean_capacity(capacity):
    """Enhanced capacity cleaning"""
    try:
        if pd.isna(capacity):
            return 0
        
        capacity_str = str(capacity).strip().upper()
        
        # Handle scientific notation and very large numbers
        if 'E+' in capacity_str or len(capacity_str) > 15:
            try:
                # This is likely a scientific notation or corrupted data
                float_val = float(capacity_str)
                # If it's unreasonably large (over 1 million MT), it's likely corrupted
                if float_val > 1000000:
                    return 0
                return float_val
            except:
                return 0
        
        # Remove common units and symbols
        capacity_clean = re.sub(r'[^\d.-]', '', capacity_str)
        
        try:
            return float(capacity_clean) if capacity_clean else 0
        except:
            return 0
    except Exception as e:
        return 0

def clean_contact_number(contact):
    """Clean and standardize contact numbers"""
    try:
        if pd.isna(contact):
            return ""
        
        contact_str = str(contact)
        
        # Handle scientific notation in contact numbers
        if 'e+' in contact_str.lower() or 'E+' in contact_str:
            try:
                contact_str = f"{float(contact_str):.0f}"
            except:
                pass
        
        # Clean the contact number
        contact_clean = re.sub(r'[^\d,+\-\s()]', '', contact_str)
        
        return contact_clean.strip()
    except Exception as e:
        return ""

def clean_epr_status(status):
    """Clean EPR certification status"""
    try:
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
    except Exception as e:
        return 'Not Specified'

def clean_documents_status(status):
    """Clean document status"""
    try:
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
    except Exception as e:
        return 'Not Specified'

def remove_duplicates(df):
    """Remove duplicate entries based on company name and contact"""
    try:
        if len(df) == 0:
            return df
            
        # Create a composite key for duplicate detection
        df['duplicate_key'] = df['Company'].fillna('').str.upper() + '|' + df['Contact No.'].fillna('').str.replace(r'[^\d]', '', regex=True)
        
        # Keep first occurrence of each duplicate
        df_deduped = df.drop_duplicates(subset=['duplicate_key'], keep='first')
        df_deduped = df_deduped.drop('duplicate_key', axis=1)
        
        return df_deduped
    except Exception as e:
        return df

def validate_contact_number(contact):
    """Enhanced contact number validation"""
    try:
        if pd.isna(contact) or str(contact).strip() == "":
            return False
        
        contact_str = str(contact).strip()
        
        # Remove all non-digits
        digits_only = re.sub(r'[^\d]', '', contact_str)
        
        # Check if it's a valid Indian mobile number
        if len(digits_only) == 10 and digits_only.startswith(('6', '7', '8', '9')):
            return True
        elif len(digits_only) == 11 and digits_only.startswith('0'):
            return True
        elif len(digits_only) == 12 and digits_only.startswith('91'):
            return True
        elif len(digits_only) >= 10 and len(digits_only) <= 15:  # International formats
            return True
        
        return False
    except Exception as e:
        return False

def validate_email(email):
    """Enhanced email validation"""
    try:
        if pd.isna(email):
            return False
        
        email_str = str(email).strip().lower()
        
        # Basic email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        return bool(re.match(pattern, email_str))
    except Exception as e:
        return False

def calculate_data_quality_score(df):
    """Enhanced data quality score calculation"""
    try:
        if len(df) == 0:
            return []
            
        scores = []
        
        for _, row in df.iterrows():
            try:
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
            except Exception as e:
                scores.append(0)
        
        return scores
    except Exception as e:
        return [0] * len(df)

# FIXED: Function to get accurate category-wise capacity for filtering
def get_category_wise_capacity_data(df):
    """
    CRITICAL FIX: Create a proper category-wise dataset where capacity is distributed
    If a company has 300MT for CAT-1,CAT-2,CAT-3, each category gets 100MT
    """
    try:
        category_records = []
        
        for _, row in df.iterrows():
            try:
                if pd.notna(row['Category']) and row['Category'] != 'Unknown':
                    categories = parse_categories(row['Category'])
                    valid_categories = [cat for cat in categories if cat != 'Unknown']
                    
                    if valid_categories:
                        distributed_capacity = row['Capacity'] / len(valid_categories) if row['Capacity'] > 0 else 0
                        
                        for category in valid_categories:
                            category_records.append({
                                'Company': row['Company'],
                                'States': row['States'],
                                'Contact No.': row['Contact No.'],
                                'Email': row['Email'],
                                'EPR Certified': row['EPR Certified'],
                                'Documents': row['Documents'],
                                'Category': category,  # Single category
                                'Original_Categories': row['Category'],  # Keep original for reference
                                'Total_Capacity': row['Capacity'],  # Original total capacity
                                'Capacity': distributed_capacity,  # Distributed capacity for this category
                                'Date': row['Date'],
                                'Owner': row['Owner'],
                                'Type': row['Type'],
                                'Remarks': row['Remarks'],
                                'Data_Quality_Score': row['Data_Quality_Score'],
                                'Valid_Contact': row['Valid_Contact'],
                                'Valid_Email': row['Valid_Email'],
                                'Dataset': row['Dataset']
                            })
            except Exception as e:
                continue
        
        return pd.DataFrame(category_records)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_and_clean_data():
    try:
        import requests, io, certifi
        
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

        # Securely fetch recyclers
        try:
            resp = requests.get(recyclers_url, verify=certifi.where(), timeout=30)
            resp.raise_for_status()
            recyclers_df = pd.read_csv(io.StringIO(resp.text), header=1)
            
            # Ensure required columns exist
            required_columns = ['Date', 'Column 2', 'Name', 'Contact No.', 'Email',
                              'EPR Certified', 'Documents', 'States', 'Category',
                              'Capacity (MT/Annum)', 'Owner', 'Type', 'Remarks']
            
            existing_columns = recyclers_df.columns.tolist()
            available_columns = [col for col in required_columns if col in existing_columns]
            
            recyclers_df = recyclers_df[available_columns].copy()
            
            # Handle missing columns
            if 'Column 2' in recyclers_df.columns:
                recyclers_df.rename(columns={'Column 2': 'Company'}, inplace=True)
            if 'Capacity (MT/Annum)' in recyclers_df.columns:
                recyclers_df.rename(columns={'Capacity (MT/Annum)': 'Capacity'}, inplace=True)
                
            st.success(f"✅ Loaded recyclers data: {len(recyclers_df)} entries")
        except Exception as e:
            st.error(f"❌ Error loading recyclers data: {str(e)}")
            return None, None

        # Securely fetch positive leads
        try:
            resp2 = requests.get(positive_url, verify=certifi.where(), timeout=30)
            resp2.raise_for_status()
            positive_df = pd.read_csv(io.StringIO(resp2.text))
            
            if 'Capacity(Annum)' in positive_df.columns:
                positive_df.rename(columns={'Capacity(Annum)': 'Capacity'}, inplace=True)
            
            st.success(f"✅ Loaded positive leads data: {len(positive_df)} entries")
        except Exception as e:
            st.error(f"❌ Error loading positive leads data: {str(e)}")
            return None, None
      
        # FIXED: Clean datasets with correct variable names
        datasets = {'All Recyclers': recyclers_df, 'Positive Leads': positive_df}
        cleaned_datasets = {}

        for name, df in datasets.items():
            try:
                df_clean = df.copy()
                
                # Handle missing columns gracefully
                if 'Date' in df_clean.columns:
                    df_clean['Date'] = df_clean['Date'].apply(clean_date)
                else:
                    df_clean['Date'] = None
                    
                if 'Company' in df_clean.columns:
                    df_clean['Company'] = df_clean['Company'].apply(clean_company_name)
                else:
                    df_clean['Company'] = 'Unknown Company'
                    
                if 'States' in df_clean.columns:
                    df_clean['States'] = df_clean['States'].apply(clean_state_name)
                else:
                    df_clean['States'] = 'Unknown'
                    
                if 'Category' in df_clean.columns:
                    df_clean['Category'] = df_clean['Category'].apply(clean_category_name)
                else:
                    df_clean['Category'] = 'Unknown'
                    
                if 'Capacity' in df_clean.columns:
                    df_clean['Capacity'] = df_clean['Capacity'].apply(clean_capacity)
                else:
                    df_clean['Capacity'] = 0
                    
                if 'Contact No.' in df_clean.columns:
                    df_clean['Contact No.'] = df_clean['Contact No.'].apply(clean_contact_number)
                else:
                    df_clean['Contact No.'] = ''
                    
                if 'EPR Certified' in df_clean.columns:
                    df_clean['EPR Certified'] = df_clean['EPR Certified'].apply(clean_epr_status)
                else:
                    df_clean['EPR Certified'] = 'Not Specified'
                    
                if 'Documents' in df_clean.columns:
                    df_clean['Documents'] = df_clean['Documents'].apply(clean_documents_status)
                else:
                    df_clean['Documents'] = 'Not Specified'
                    
                if 'Email' not in df_clean.columns:
                    df_clean['Email'] = ''
                    
                if 'Owner' not in df_clean.columns:
                    df_clean['Owner'] = 'Unknown'
                    
                if 'Type' not in df_clean.columns:
                    df_clean['Type'] = 'Unknown'
                    
                if 'Remarks' not in df_clean.columns:
                    df_clean['Remarks'] = ''
                
                df_clean = remove_duplicates(df_clean)
                df_clean['Data_Quality_Score'] = calculate_data_quality_score(df_clean)
                df_clean['Dataset'] = name
                
                # CRITICAL FIX: Add distributed capacity per category
                df_clean['Distributed_Capacity'] = df_clean.apply(get_distributed_capacity, axis=1)
                
                # Add validation columns
                df_clean['Valid_Contact'] = df_clean['Contact No.'].apply(validate_contact_number)
                df_clean['Valid_Email'] = df_clean['Email'].apply(validate_email)
                
                cleaned_datasets[name] = df_clean
            except Exception as e:
                st.error(f"Error cleaning dataset {name}: {str(e)}")
                continue

        return cleaned_datasets.get('All Recyclers'), cleaned_datasets.get('Positive Leads')
    except Exception as e:
        st.error(f"Critical error in load_and_clean_data: {str(e)}")
        return None, None

# Streamlit App Configuration
st.set_page_config(
    page_title="🏭 Enhanced Plastic Waste Recyclers Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Enhanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .filter-container {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .data-quality-good { color: #28a745; font-weight: bold; }
    .data-quality-medium { color: #ffc107; font-weight: bold; }
    .data-quality-poor { color: #dc3545; font-weight: bold; }
    .success-highlight { 
        background-color: #d4edda; 
        border: 2px solid #28a745; 
        border-radius: 10px; 
        padding: 10px; 
        margin: 10px 0; 
    }
    .warning-highlight { 
        background-color: #fff3cd; 
        border: 2px solid #ffc107; 
        border-radius: 10px; 
        padding: 10px; 
        margin: 10px 0; 
    }
    .sidebar .stButton > button {
        width: 100%;
        margin: 2px 0;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border: 1px solid #dee2e6;
        color: #495057;
        font-weight: 500;
    }
    .sidebar .stButton > button:hover {
        background: linear-gradient(145deg, #e2e6ea, #dae0e5);
        border: 1px solid #adb5bd;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🏭 Enhanced Plastic Waste Recyclers Dashboard</h1>
    <p>Comprehensive analysis of plastic waste recycling companies across India</p>
    <small>Advanced Data Analytics & Business Intelligence Platform</small>
</div>
""", unsafe_allow_html=True)

# Load data with progress indicator
with st.spinner("🔄 Loading and processing data..."):
    recyclers_data, positive_data = load_and_clean_data()

if recyclers_data is not None and positive_data is not None:
    try:
        # Sidebar Configuration with better organization
        st.sidebar.markdown("### 🎛️ Dashboard Controls")
        
        # Dataset selection with better descriptions
        dataset_choice = st.sidebar.selectbox(
            "📊 Select Dataset",
            ["All Recyclers", "Positive Leads", "Combined View"],
            help="• All Recyclers: Complete database\n• Positive Leads: Pre-qualified companies\n• Combined View: Merged analysis"
        )
        
        # Determine which data to use and show proper counts
        if dataset_choice == "All Recyclers":
            df_to_use = recyclers_data
        elif dataset_choice == "Positive Leads":
            df_to_use = positive_data
        else:  # Combined View
            # FIXED: Properly combine data to ensure all entries show up
            df_to_use = pd.concat([recyclers_data, positive_data], ignore_index=True)
        
        # CRITICAL FIX: Create category-wise data for accurate filtering and visualization
        category_wise_df = get_category_wise_capacity_data(df_to_use)
        
        # Filters Section with enhanced organization
        st.sidebar.markdown("### 🔍 Smart Filters")
        
        # FIXED: Quick filter presets IN SIDEBAR with proper layout and working functionality
        st.sidebar.markdown("#### ⚡ Quick Presets")
        
        # Initialize session state for filters if not exists
        if 'preset_active' not in st.session_state:
            st.session_state['preset_active'] = None
        
        # Create 2x2 grid layout for buttons in sidebar
        preset_col1, preset_col2 = st.sidebar.columns(2)
        
        with preset_col1:
            if st.button("🏆 Top Quality", help="Companies with high data quality scores", key="preset_top_quality", use_container_width=True):
                st.session_state['preset_active'] = 'top_quality'
                st.rerun()
                
            if st.button("✅ Certified Only", help="EPR certified companies only", key="preset_certified", use_container_width=True):
                st.session_state['preset_active'] = 'certified_only'
                st.rerun()
        
        with preset_col2:
            if st.button("📄 With Docs", help="Companies with required documents", key="preset_with_docs", use_container_width=True):
                st.session_state['preset_active'] = 'with_docs'
                st.rerun()
                
            if st.button("🔄 Reset All", help="Clear all filters", key="preset_reset", use_container_width=True):
                st.session_state['preset_active'] = 'reset_all'
                st.rerun()
        
        # ACCESSIBILITY FIX: Company search with proper label visibility
        st.sidebar.markdown("#### 🏢 Company Search")
        company_search = st.sidebar.text_input(
            "Company Search",
            placeholder="Search company names...",
            help="Type to search for specific companies (case-insensitive)",
            key="company_search_key",
            value="",
            label_visibility="hidden"  # FIXED: Hide label instead of empty string
        )
        
        # State filter
        st.sidebar.markdown("#### 🗺️ Geographic Filters")
        available_states = sorted([s for s in df_to_use['States'].unique() if s != 'Unknown'])
        
        # Apply preset filtering for states if needed
        state_default = []
        if st.session_state.get('preset_active') == 'reset_all':
            state_default = []
        
        state_filter = st.sidebar.multiselect(
            "Select States/UTs",
            available_states,
            default=state_default,
            help="Select one or more states for regional analysis",
            key="state_multiselect"
        )
        
        # FIXED CATEGORY FILTER - Show individual categories only, including Unknown as requested
        st.sidebar.markdown("#### 📦 Category Filters")
        available_categories = get_unique_categories(df_to_use)  # Use the fixed function
        
        # Apply preset filtering for categories if needed
        category_default = []
        if st.session_state.get('preset_active') == 'reset_all':
            category_default = []
            
        category_filter = st.sidebar.multiselect(
            "Select Waste Categories",
            available_categories,
            default=category_default,
            help="Choose specific waste categories (CAT-1: PET, CAT-2: HDPE, CAT-3: PVC, etc.) or Unknown",
            key="category_multiselect"
        )
        
        # Business filters
        st.sidebar.markdown("#### 💼 Business Criteria")
        
        # EPR Status filter with better descriptions and preset handling
        epr_statuses = sorted(df_to_use['EPR Certified'].unique())
        
        # Handle presets for EPR filter
        epr_default = []
        if st.session_state.get('preset_active') == 'certified_only':
            epr_default = ['Certified']
        elif st.session_state.get('preset_active') == 'reset_all':
            epr_default = []
        
        epr_filter = st.sidebar.multiselect(
            "EPR Certification Status",
            epr_statuses,
            default=epr_default,
            help="• Certified: EPR certificate obtained\n• Ready To Certify: Documentation complete\n• In Process: Application submitted\n• Not Certified: No certification",
            key="epr_multiselect"
        )
        
        # Document Status filter with preset handling
        doc_statuses = sorted(df_to_use['Documents'].unique())
        
        # Handle presets for doc filter
        doc_default = []
        if st.session_state.get('preset_active') == 'with_docs':
            doc_default = ['With Documents']
        elif st.session_state.get('preset_active') == 'reset_all':
            doc_default = []
        
        doc_filter = st.sidebar.multiselect(
            "Document Availability",
            doc_statuses,
            default=doc_default,
            help="Filter by availability of required business documents",
            key="doc_multiselect"
        )
        
        # Owner/Team filter
        owners = sorted([o for o in df_to_use['Owner'].unique() if pd.notna(o)])
        
        # Apply preset filtering for owners if needed
        owner_default = []
        if st.session_state.get('preset_active') == 'reset_all':
            owner_default = []
            
        owner_filter = st.sidebar.multiselect(
            "👤 Data Owner/Team",
            owners,
            default=owner_default,
            help="Filter by who collected/owns this data",
            key="owner_multiselect"
        )
        
        # Time Filters (moved above Advanced Filters as requested)
        st.sidebar.markdown("#### 📅 Time Filters")
        if "Date" in df_to_use.columns:
            df_to_use["Date"] = pd.to_datetime(df_to_use["Date"], errors='coerce')
            min_date = df_to_use["Date"].min()
            max_date = df_to_use["Date"].max()
            if pd.isna(min_date) or pd.isna(max_date):
                import datetime
                min_date = max_date = datetime.date.today()
            date_range = st.sidebar.date_input(
                "Select Date Range",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
                help="Filter entries by data collection date",
                key="date_range_key"
            )
        else:
            date_range = None
        
        # Advanced numeric filters
        st.sidebar.markdown("#### 📊 Advanced Filters")
        
        # Capacity filter with better range display
        if df_to_use['Capacity'].max() > 0:
            max_capacity = int(df_to_use['Capacity'].max())
            # Cap unreasonable maximum values
            if max_capacity > 1000000:  # More than 1000k MT is likely data error
                max_capacity = 500000
            
            capacity_range = st.sidebar.slider(
                "⚖️ Processing Capacity (MT/Year)",
                min_value=0,
                max_value=max_capacity,
                value=(0, max_capacity),
                format="%d MT",
                help=f"Filter companies by their processing capacity\nRange: 0 to {max_capacity:,} MT/year",
                key="capacity_slider"
            )
        else:
            capacity_range = (0, 0)
        
        # Data Quality filter with preset handling
        quality_default = 0
        if st.session_state.get('preset_active') == 'top_quality':
            quality_default = 70
        elif st.session_state.get('preset_active') == 'reset_all':
            quality_default = 0
            
        quality_threshold = st.sidebar.slider(
            "📈 Minimum Data Quality Score",
            min_value=0,
            max_value=100,
            value=quality_default,
            format="%d%%",
            help="Filter by data completeness and quality score\n• 70%+: High quality\n• 40-69%: Medium quality\n• <40%: Low quality",
            key="quality_slider"
        )
        
        # Advanced Options with more features - FIXED DEFAULT FOR EXCLUDE UNKNOWN LOCATIONS
        with st.sidebar.expander("⚙️ Advanced Options"):
            show_duplicates = st.checkbox(
                "🔍 Highlight Potential Duplicates", 
                help="Identify companies with similar names/contacts"
            )
            show_contact_verified = st.checkbox(
                "📞 Valid Contacts Only", 
                help="Only show entries with verified contact numbers"
            )
            show_email_available = st.checkbox(
                "📧 Email Available Only", 
                help="Only show entries with valid email addresses"
            )
            high_capacity_only = st.checkbox(
                "🏭 High Capacity Only (>1000 MT)", 
                help="Show only large-scale processing facilities"
            )
            # FIXED: Default to checked as requested
            exclude_unknown_states = st.checkbox(
                "🗺️ Exclude Unknown Locations", 
                value=False,  # CHANGED: Default to unchecked as user requested to keep it unchecked by default
                help="Hide entries with unspecified locations"
            )
        
        # Clear preset state after applying
        if st.session_state.get('preset_active'):
            st.session_state['preset_active'] = None
        
        # Apply all filters with progress tracking
        filtered_df = df_to_use.copy()
        filter_steps = []
        
        # Track filtering steps
        original_count = len(filtered_df)
        
        if company_search:
            filtered_df = filtered_df[filtered_df['Company'].str.contains(company_search, case=False, na=False)]
            filter_steps.append(f"Company search: {len(filtered_df)} entries")
        
        if state_filter:
            filtered_df = filtered_df[filtered_df['States'].isin(state_filter)]
            filter_steps.append(f"State filter: {len(filtered_df)} entries")
        
        # FIXED CATEGORY FILTERING LOGIC with accurate results
        if category_filter:
            def row_contains_any_category(category_string):
                try:
                    if pd.isna(category_string):
                        return False
                    
                    # Parse all categories in this row
                    row_categories = parse_categories(category_string)
                    
                    # Check if any of the filter categories exist in this row's categories
                    return any(filter_cat in row_categories for filter_cat in category_filter)
                except Exception as e:
                    return False
            
            category_mask = filtered_df['Category'].apply(row_contains_any_category)
            filtered_df = filtered_df[category_mask]
            filter_steps.append(f"Category filter: {len(filtered_df)} entries")
        
        if epr_filter:
            filtered_df = filtered_df[filtered_df['EPR Certified'].isin(epr_filter)]
            filter_steps.append(f"EPR filter: {len(filtered_df)} entries")
        
        if doc_filter:
            filtered_df = filtered_df[filtered_df['Documents'].isin(doc_filter)]
            filter_steps.append(f"Document filter: {len(filtered_df)} entries")
        
        if owner_filter:
            filtered_df = filtered_df[filtered_df['Owner'].isin(owner_filter)]
            filter_steps.append(f"Owner filter: {len(filtered_df)} entries")
        
        if capacity_range[1] > 0:
            filtered_df = filtered_df[
                (filtered_df['Capacity'] >= capacity_range[0]) & 
                (filtered_df['Capacity'] <= capacity_range[1])
            ]
            filter_steps.append(f"Capacity filter: {len(filtered_df)} entries")
        
        if quality_threshold > 0:
            filtered_df = filtered_df[filtered_df['Data_Quality_Score'] >= quality_threshold]
            filter_steps.append(f"Quality filter: {len(filtered_df)} entries")
        
        # Apply date filter
        if date_range and len(date_range) == 2 and "Date" in filtered_df.columns:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)
            ]
            filter_steps.append(f"Date filter: {len(filtered_df)} entries")
        
        if show_contact_verified and 'Valid_Contact' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Valid_Contact'] == True]
            filter_steps.append(f"Valid contact filter: {len(filtered_df)} entries")
        
        if show_email_available and 'Valid_Email' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Valid_Email'] == True]
            filter_steps.append(f"Valid email filter: {len(filtered_df)} entries")
        
        if high_capacity_only:
            filtered_df = filtered_df[filtered_df['Capacity'] > 1000]
            filter_steps.append(f"High capacity filter: {len(filtered_df)} entries")
        
        if exclude_unknown_states:
            filtered_df = filtered_df[filtered_df['States'] != 'Unknown']
            filter_steps.append(f"Known states filter: {len(filtered_df)} entries")
        
        # Enhanced Sorting options
        st.sidebar.markdown("### 🔄 Sorting & Display")
        sort_columns = [col for col in filtered_df.columns if col not in ['Dataset']]
        sort_column = st.sidebar.selectbox(
            "Sort by", 
            sort_columns,
            index=sort_columns.index('Data_Quality_Score') if 'Data_Quality_Score' in sort_columns else 0
        )
        sort_order = st.sidebar.selectbox("Sort Order", ["Descending", "Ascending"])
        
        # Apply sorting
        filtered_df = filtered_df.sort_values(
            by=sort_column,
            ascending=(sort_order == "Ascending")
        )
        
        # Show filter summary
        if filter_steps:
            with st.sidebar.expander("📊 Filter Summary", expanded=False):
                st.write(f"**Started with:** {original_count} entries")
                for step in filter_steps:
                    st.write(f"• {step}")
                st.write(f"**Final result:** {len(filtered_df)} entries")
                reduction_pct = ((original_count - len(filtered_df)) / original_count * 100) if original_count > 0 else 0
                st.write(f"**Filtered out:** {reduction_pct:.1f}%")
        
        # Main Dashboard Content with Enhanced Metrics
        
        # Alert system for filtering results
        if len(filtered_df) == 0:
            st.error("⚠️ No companies match your current filter criteria. Try adjusting your filters.")
            st.info("💡 **Suggestions:** Lower the data quality threshold, expand state selection, or clear some filters.")
            st.stop()
        elif len(filtered_df) < 10:
            st.warning(f"⚠️ Only {len(filtered_df)} companies match your filters. Consider broadening your criteria for better insights.")
        
        # Enhanced Key Metrics with better formatting
        st.markdown("## 📊 Key Performance Indicators")
        
        # Primary metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_companies = len(filtered_df)
            total_change = len(filtered_df) - len(df_to_use)
            st.metric(
                "🏢 Total Companies", 
                f"{total_companies:,}",
                delta=f"{total_change:+,} from total",
                help=f"Showing {total_companies} out of {len(df_to_use):,} total companies"
            )
        
        with col2:
            unique_states = filtered_df['States'].nunique()
            total_states_available = df_to_use['States'].nunique()
            st.metric(
                "🗺️ States/UTs Covered", 
                f"{unique_states}",
                delta=f"of {total_states_available} total",
                help="Geographic distribution across Indian states and union territories"
            )
        
        with col3:
            certified_companies = len(filtered_df[filtered_df['EPR Certified'] == 'Certified'])
            certification_rate = (certified_companies / total_companies * 100) if total_companies > 0 else 0
            st.metric(
                "📋 EPR Certified", 
                f"{certified_companies}",
                delta=f"{certification_rate:.1f}% rate",
                help="Companies with valid EPR (Extended Producer Responsibility) certification"
            )
        
        with col4:
            total_capacity = filtered_df['Capacity'].sum()
            avg_capacity = filtered_df['Capacity'].mean() if len(filtered_df) > 0 else 0
            st.metric(
                "⚖️ Total Capacity", 
                f"{total_capacity:,.0f} MT/year",
                delta=f"Avg: {avg_capacity:.0f} MT",
                help="Combined annual processing capacity of all selected companies"
            )
        
        # Secondary metrics row
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            avg_quality = filtered_df['Data_Quality_Score'].mean()
            quality_color = "🟢" if avg_quality >= 70 else "🟡" if avg_quality >= 40 else "🔴"
            quality_trend = "Excellent" if avg_quality >= 80 else "Good" if avg_quality >= 60 else "Fair" if avg_quality >= 40 else "Poor"
            st.metric(
                f"{quality_color} Data Quality",
                f"{avg_quality:.1f}%",
                delta=f"{quality_trend}",
                help="Average data completeness and accuracy score"
            )
        
        with col6:
            with_documents = len(filtered_df[filtered_df['Documents'] == 'With Documents'])
            doc_rate = (with_documents / total_companies * 100) if total_companies > 0 else 0
            st.metric(
                "📄 Documentation Ready",
                f"{with_documents}",
                delta=f"{doc_rate:.1f}% complete",
                help="Companies with required business documentation"
            )
        
        with col7:
            if 'Valid_Email' in filtered_df.columns:
                with_email = len(filtered_df[filtered_df['Valid_Email'] == True])
            else:
                with_email = len(filtered_df[filtered_df['Email'].str.contains('@', na=False)])
            email_rate = (with_email / total_companies * 100) if total_companies > 0 else 0
            st.metric(
                "📧 Email Contacts",
                f"{with_email}",
                delta=f"{email_rate:.1f}% reachable",
                help="Companies with verified email addresses for communication"
            )
        
        with col8:
            positive_leads = len(filtered_df[
                (filtered_df['EPR Certified'] == 'Certified') & 
                (filtered_df['Documents'] == 'With Documents')
            ])
            lead_rate = (positive_leads / total_companies * 100) if total_companies > 0 else 0
            st.metric(
                "✅ Qualified Leads",
                f"{positive_leads}",
                delta=f"{lead_rate:.1f}% ready",
                help="Companies with both EPR certification AND complete documentation"
            )
        
        # Business intelligence insights
        if total_companies > 0:
            st.markdown("### 💡 Business Intelligence Insights")
            
            insights_col1, insights_col2, insights_col3 = st.columns(3)
            
            with insights_col1:
                if certification_rate > 50:
                    st.markdown('<div class="success-highlight">🎯 <strong>High Certification Rate</strong><br>Over 50% of companies are EPR certified - excellent for compliance partnerships.</div>', unsafe_allow_html=True)
                elif certification_rate > 25:
                    st.markdown('<div class="warning-highlight">⚠️ <strong>Moderate Certification Rate</strong><br>25-50% certified - focus on supporting companies through certification process.</div>', unsafe_allow_html=True)
                else:
                    st.info("📈 **Growth Opportunity**: Low certification rate presents opportunity for EPR consulting services.")
            
            with insights_col2:
                if avg_quality > 70:
                    st.success("📊 **High Data Quality**: Reliable dataset for decision-making and analysis.")
                elif avg_quality > 40:
                    st.warning("🔧 **Data Enhancement Needed**: Consider data enrichment initiatives.")
                else:
                    st.error("❗ **Data Quality Alert**: Significant data gaps require attention.")
            
            with insights_col3:
                if len(filtered_df) > 0:
                    top_capacity_state = filtered_df.groupby('States')['Capacity'].sum().sort_values(ascending=False).index[0] if len(filtered_df) > 0 else "N/A"
                    st.info(f"🏭 **Capacity Leader**: {top_capacity_state} has the highest total processing capacity in your selection.")
        
        # Enhanced Visualizations
        st.markdown("## 📈 Advanced Analytics Dashboard")
        
        # Create tabs for different analysis views with better organization
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Executive Summary", "🗺️ Geographic Analysis", "📦 Category Intelligence", 
            "📋 Compliance Status", "👥 Team Performance", "🔍 Data Quality"
        ])
        
        with tab1:
            st.markdown("### 📊 Executive Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Enhanced Companies by State visualization
                state_counts = filtered_df['States'].value_counts().head(15)
                if not state_counts.empty:
                    fig_bar = px.bar(
                        x=state_counts.values,
                        y=state_counts.index,
                        orientation='h',
                        title="🏆 Top 15 States by Company Count",
                        labels={'x': 'Number of Companies', 'y': 'State/UT'},
                        color=state_counts.values,
                        color_continuous_scale='viridis',
                        text=state_counts.values
                    )
                    fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
                    fig_bar.update_layout(
                        height=500, 
                        showlegend=False,
                        font=dict(size=12),
                        title_font_size=16
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No state data available for visualization")
            
            with col2:
                # Enhanced EPR Certification Status with better colors
                epr_counts = filtered_df['EPR Certified'].value_counts()
                if not epr_counts.empty:
                    # Custom color mapping for better visual distinction
                    epr_color_map = {
                        'Certified': '#28a745',
                        'Not Certified': '#dc3545', 
                        'Ready To Certify': '#ffc107',
                        'In Process': '#17a2b8',
                        'Not Specified': '#6c757d'
                    }
                    colors = [epr_color_map.get(status, '#6c757d') for status in epr_counts.index]
                    
                    fig_pie = px.pie(
                        values=epr_counts.values,
                        names=epr_counts.index,
                        title="🏅 EPR Certification Status Distribution",
                        color_discrete_sequence=colors
                    )
                    fig_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont_size=12,
                        pull=[0.1 if x == 'Certified' else 0 for x in epr_counts.index]
                    )
                    fig_pie.update_layout(
                        height=500,
                        title_font_size=16,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            # FIXED: Business Summary Table with accurate distributed capacity
            st.markdown("### 📋 Business Summary by Category (Fixed Capacity Distribution)")
            if len(filtered_df) > 0:
                # Use category-wise data for accurate calculations
                filtered_category_df = get_category_wise_capacity_data(filtered_df)
                
                if len(filtered_category_df) > 0:
                    business_summary = []
                    for category in get_unique_categories(filtered_df):
                        if category != 'Unknown':  # Skip unknown for summary
                            cat_records = filtered_category_df[filtered_category_df['Category'] == category]
                            if len(cat_records) > 0:
                                business_summary.append({
                                    'Category': category,
                                    'Companies': len(cat_records),
                                    'EPR Certified': len(cat_records[cat_records['EPR Certified'] == 'Certified']),
                                    'With Documents': len(cat_records[cat_records['Documents'] == 'With Documents']),
                                    'Distributed Capacity (MT)': cat_records['Capacity'].sum(),  # This is now correctly distributed
                                    'Avg Quality Score': cat_records['Data_Quality_Score'].mean(),
                                    'Qualified Leads': len(cat_records[
                                        (cat_records['EPR Certified'] == 'Certified') & 
                                        (cat_records['Documents'] == 'With Documents')
                                    ])
                                })
                    
                    if business_summary:
                        summary_df = pd.DataFrame(business_summary)
                        summary_df['EPR Rate (%)'] = (summary_df['EPR Certified'] / summary_df['Companies'] * 100).round(1)
                        summary_df['Doc Rate (%)'] = (summary_df['With Documents'] / summary_df['Companies'] * 100).round(1)
                        summary_df['Lead Rate (%)'] = (summary_df['Qualified Leads'] / summary_df['Companies'] * 100).round(1)
                        
                        # Format for better display
                        summary_df['Distributed Capacity (MT)'] = summary_df['Distributed Capacity (MT)'].round(0).astype(int)
                        summary_df['Avg Quality Score'] = summary_df['Avg Quality Score'].round(1)
                        
                        st.dataframe(summary_df, use_container_width=True)
                        
                        # Show note about distributed capacity
                        st.info("💡 **Note**: Capacity is correctly distributed among categories. If a company processes 300MT for CAT-1, CAT-2, CAT-3, each category shows 100MT.")
        
        with tab2:
            st.markdown("### 🗺️ Geographic Intelligence")
            
            # Enhanced map visualization
            if len(filtered_df) > 0:
                map_data = filtered_df.copy()
                
                # Add coordinates for mapping
                map_data['lat'] = map_data['States'].map(
                    lambda x: STATE_COORDS.get(x, [20.0, 78.0])[0] if x in STATE_COORDS else 20.0
                )
                map_data['lon'] = map_data['States'].map(
                    lambda x: STATE_COORDS.get(x, [20.0, 78.0])[1] if x in STATE_COORDS else 78.0
                )
                
                # Add jitter to avoid overlapping points
                np.random.seed(42)
                map_data['lat'] += np.random.uniform(-0.3, 0.3, len(map_data))
                map_data['lon'] += np.random.uniform(-0.3, 0.3, len(map_data))
                
                # Filter valid coordinates
                valid_map_data = map_data[
                    (map_data['lat'] != 20.0) | (map_data['lon'] != 78.0)
                ]
                
                if len(valid_map_data) > 0:
                    st.markdown("#### 🗺️ Company Locations Across India")
                    st.map(valid_map_data[['lat', 'lon']], zoom=4)
                    st.info(f"📍 Showing {len(valid_map_data)} companies with valid geographic coordinates")
                else:
                    st.warning("No valid geographic coordinates available for mapping")
                
                # State-wise business intelligence
                st.markdown("### 📊 State-wise Business Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Capacity analysis by state
                    capacity_by_state = filtered_df.groupby('States').agg({
                        'Capacity': ['count', 'sum', 'mean'],
                        'EPR Certified': lambda x: sum(x == 'Certified'),
                        'Data_Quality_Score': 'mean'
                    }).round(2)
                    
                    capacity_by_state.columns = [
                        'Companies', 'Total Capacity (MT)', 'Avg Capacity (MT)', 
                        'EPR Certified', 'Avg Quality (%)'
                    ]
                    
                    # Add rates
                    capacity_by_state['EPR Rate (%)'] = (
                        capacity_by_state['EPR Certified'] / capacity_by_state['Companies'] * 100
                    ).round(1)
                    
                    # Filter and sort
                    capacity_by_state = capacity_by_state[
                        capacity_by_state['Total Capacity (MT)'] > 0
                    ].sort_values('Total Capacity (MT)', ascending=False).head(10)
                    
                    if not capacity_by_state.empty:
                        st.markdown("**🏭 Top 10 States by Processing Capacity**")
                        st.dataframe(capacity_by_state, use_container_width=True)
                
                with col2:
                    # EPR certification heatmap by state
                    if len(filtered_df) > 10:  # Only show if enough data
                        state_epr_pivot = filtered_df.groupby(['States', 'EPR Certified']).size().unstack(fill_value=0)
                        if not state_epr_pivot.empty and len(state_epr_pivot) > 3:
                            fig_heatmap = px.imshow(
                                state_epr_pivot.values,
                                labels=dict(x="EPR Status", y="States", color="Count"),
                                y=state_epr_pivot.index,
                                x=state_epr_pivot.columns,
                                title="🔥 EPR Certification Heatmap by State",
                                color_continuous_scale="RdYlGn"
                            )
                            fig_heatmap.update_layout(height=400)
                            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab3:
            st.markdown("### 📦 Category Intelligence Dashboard")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # FIXED CATEGORY DISTRIBUTION with accurate parsing
                filtered_category_df = get_category_wise_capacity_data(filtered_df)
                
                if len(filtered_category_df) > 0:
                    cat_counts = filtered_category_df['Category'].value_counts()
                    # Remove 'Unknown' categories for cleaner visualization unless specifically selected
                    if 'Unknown' not in category_filter:
                        cat_counts = cat_counts[cat_counts.index != 'Unknown']
                    
                    if not cat_counts.empty:
                        fig_cat = px.bar(
                            x=cat_counts.index,
                            y=cat_counts.values,
                            title="📊 Waste Category Distribution (Company-Category Entries)",
                            labels={'x': 'Waste Category', 'y': 'Number of Company-Category Entries'},
                            color=cat_counts.values,
                            color_continuous_scale='viridis',
                            text=cat_counts.values
                        )
                        fig_cat.update_traces(texttemplate='%{text}', textposition='outside')
                        fig_cat.update_layout(
                            height=400,
                            showlegend=False,
                            title_font_size=16
                        )
                        st.plotly_chart(fig_cat, use_container_width=True)
                    else:
                        st.info("No category data available for visualization")
                else:
                    st.info("No category data available for visualization")

            with col2:
                # FIXED CAPACITY BY CATEGORY with proper distributed calculation
                if len(filtered_category_df) > 0:
                    cap_summary = filtered_category_df.groupby('Category')['Capacity'].sum().sort_values(ascending=False)
                    # Remove 'Unknown' categories unless specifically selected
                    if 'Unknown' not in category_filter:
                        cap_summary = cap_summary[cap_summary.index != 'Unknown']
                    
                    if not cap_summary.empty:
                        fig_cap = px.bar(
                            x=cap_summary.index,
                            y=cap_summary.values,
                            title="⚖️ Distributed Processing Capacity by Category",
                            labels={'x': 'Waste Category', 'y': 'Distributed Capacity (MT/Year)'},
                            color=cap_summary.values,
                            color_continuous_scale='plasma',
                            text=cap_summary.values.round(0).astype(int)
                        )
                        fig_cap.update_traces(texttemplate='%{text} MT', textposition='outside')
                        fig_cap.update_layout(
                            height=400,
                            showlegend=False,
                            title_font_size=16
                        )
                        st.plotly_chart(fig_cap, use_container_width=True)
                        
                        st.info("💡 **Note**: This shows the correctly distributed capacity. A company with 300MT handling CAT-1,CAT-2,CAT-3 contributes 100MT to each category.")
                    else:
                        st.info("No capacity data available by category")
                else:
                    st.info("No capacity data available by category")
            
            # FIXED: Category-wise business metrics table with accurate distributed data
            st.markdown("### 📋 Detailed Category Analysis (Fixed Capacity Distribution)")
            
            if len(filtered_category_df) > 0:
                category_analysis = []
                for category in get_unique_categories(filtered_df):
                    # Find company-category records for this specific category
                    cat_records = filtered_category_df[filtered_category_df['Category'] == category]
                    
                    if len(cat_records) > 0:
                        # Get unique companies for this category
                        unique_companies = cat_records['Company'].nunique()
                        
                        category_analysis.append({
                            'Category': category,
                            'Unique Companies': unique_companies,
                            'Total Records': len(cat_records),
                            'EPR Certified': len(cat_records[cat_records['EPR Certified'] == 'Certified']),
                            'With Documents': len(cat_records[cat_records['Documents'] == 'With Documents']),
                            'Distributed Capacity (MT/Year)': cat_records['Capacity'].sum(),
                            'Avg Distributed Capacity (MT/Year)': cat_records['Capacity'].mean(),
                            'States Covered': cat_records['States'].nunique(),
                            'Avg Quality Score (%)': cat_records['Data_Quality_Score'].mean(),
                            'Business Ready': len(cat_records[
                                (cat_records['EPR Certified'] == 'Certified') & 
                                (cat_records['Documents'] == 'With Documents')
                            ])
                        })
                
                if category_analysis:
                    analysis_df = pd.DataFrame(category_analysis)
                    
                    # Calculate rates based on unique companies
                    analysis_df['EPR Rate (%)'] = (
                        analysis_df['EPR Certified'] / analysis_df['Total Records'] * 100
                    ).round(1)
                    analysis_df['Doc Rate (%)'] = (
                        analysis_df['With Documents'] / analysis_df['Total Records'] * 100
                    ).round(1)
                    analysis_df['Business Ready Rate (%)'] = (
                        analysis_df['Business Ready'] / analysis_df['Total Records'] * 100
                    ).round(1)
                    
                    # Format numeric columns
                    for col in ['Distributed Capacity (MT/Year)', 'Avg Distributed Capacity (MT/Year)']:
                        analysis_df[col] = analysis_df[col].round(0).astype(int)
                    analysis_df['Avg Quality Score (%)'] = analysis_df['Avg Quality Score (%)'].round(1)
                    
                    # Sort by distributed capacity
                    analysis_df = analysis_df.sort_values('Distributed Capacity (MT/Year)', ascending=False)
                    
                    st.dataframe(analysis_df, use_container_width=True)
                    
                    # Category insights with fixed data
                    if len(analysis_df) > 0:
                        top_category = analysis_df.iloc[0]['Category']
                        top_capacity = analysis_df.iloc[0]['Distributed Capacity (MT/Year)']
                        
                        st.info(f"🏆 **Top Category by Distributed Capacity**: {top_category} with {top_capacity:,} MT/year of correctly distributed processing capacity")

        with tab4:
            st.markdown("### 📋 Compliance & Documentation Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Enhanced EPR Status Analysis
                epr_counts = filtered_df['EPR Certified'].value_counts()
                if not epr_counts.empty:
                    # Custom colors for better business intelligence
                    epr_colors = {
                        'Certified': '#28a745',      # Success green
                        'Not Certified': '#dc3545',  # Danger red
                        'Ready To Certify': '#ffc107', # Warning yellow
                        'In Process': '#17a2b8',     # Info blue
                        'Not Specified': '#6c757d'   # Secondary gray
                    }
                    colors_list = [epr_colors.get(status, '#6c757d') for status in epr_counts.index]
                    
                    fig_epr_pie = px.pie(
                        values=epr_counts.values,
                        names=epr_counts.index,
                        title="🏅 EPR Certification Status Breakdown",
                        color_discrete_sequence=colors_list
                    )
                    fig_epr_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label+value',
                        textfont_size=11,
                        pull=[0.15 if x == 'Certified' else 0.05 if x in ['Ready To Certify', 'In Process'] else 0 for x in epr_counts.index]
                    )
                    fig_epr_pie.update_layout(
                        height=500,
                        font=dict(size=12),
                        title_font_size=16,
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
                    )
                    st.plotly_chart(fig_epr_pie, use_container_width=True)
            
            with col2:
                # Enhanced Document Status Analysis
                doc_counts = filtered_df['Documents'].value_counts()
                if not doc_counts.empty:
                    doc_colors = {
                        'With Documents': '#28a745',     # Success green
                        'Without Documents': '#dc3545', # Danger red
                        'Not Sure': '#ffc107',          # Warning yellow
                        'Not Specified': '#6c757d'      # Secondary gray
                    }
                    doc_colors_list = [doc_colors.get(status, '#6c757d') for status in doc_counts.index]
                    
                    fig_doc_pie = px.pie(
                        values=doc_counts.values,
                        names=doc_counts.index,
                        title="📄 Documentation Status Overview",
                        color_discrete_sequence=doc_colors_list
                    )
                    fig_doc_pie.update_traces(
                        textposition='inside', 
                        textinfo='percent+label+value',
                        textfont_size=11,
                        pull=[0.15 if x == 'With Documents' else 0.05 if x == 'Not Sure' else 0 for x in doc_counts.index]
                    )
                    fig_doc_pie.update_layout(
                        height=500,
                        font=dict(size=12),
                        title_font_size=16,
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
                    )
                    st.plotly_chart(fig_doc_pie, use_container_width=True)
            
            # Compliance readiness matrix
            st.markdown("### 📊 Business Readiness Matrix")
            
            if len(filtered_df) > 0:
                # Create compliance matrix
                compliance_matrix = pd.crosstab(
                    filtered_df['EPR Certified'], 
                    filtered_df['Documents'], 
                    margins=True, 
                    margins_name="Total"
                )
                
                st.markdown("**🎯 EPR Certification vs Documentation Status**")
                st.dataframe(compliance_matrix, use_container_width=True)
                
                # Business insights
                ready_companies = len(filtered_df[
                    (filtered_df['EPR Certified'] == 'Certified') & 
                    (filtered_df['Documents'] == 'With Documents')
                ])
                
                potential_companies = len(filtered_df[
                    (filtered_df['EPR Certified'] == 'Ready To Certify') & 
                    (filtered_df['Documents'] == 'With Documents')
                ])
                
                in_process = len(filtered_df[
                    (filtered_df['EPR Certified'] == 'In Process')
                ])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.success(f"✅ **Business Ready**: {ready_companies} companies\n\n*Fully compliant and ready for partnerships*")
                
                with col2:
                    st.warning(f"🟡 **High Potential**: {potential_companies} companies\n\n*Documentation ready, certification pending*")
                
                with col3:
                    st.info(f"🔄 **In Progress**: {in_process} companies\n\n*Active certification applications*")
            
            # State-wise compliance analysis
            st.markdown("### 🗺️ State-wise Compliance Performance")
            
            if len(filtered_df) > 10:  # Only if sufficient data
                state_compliance = filtered_df.groupby('States').agg({
                    'Company': 'count',
                    'EPR Certified': lambda x: sum(x == 'Certified'),
                    'Documents': lambda x: sum(x == 'With Documents')
                }).round(0)
                
                state_compliance.columns = ['Total Companies', 'EPR Certified', 'With Documents']
                state_compliance['EPR Rate (%)'] = (
                    state_compliance['EPR Certified'] / state_compliance['Total Companies'] * 100
                ).round(1)
                state_compliance['Doc Rate (%)'] = (
                    state_compliance['With Documents'] / state_compliance['Total Companies'] * 100
                ).round(1)
                
                # Calculate combined readiness score
                state_compliance['Readiness Score'] = (
                    (state_compliance['EPR Rate (%)'] + state_compliance['Doc Rate (%)']) / 2
                ).round(1)
                
                # Show top performing states
                top_states = state_compliance[
                    state_compliance['Total Companies'] >= 3  # Minimum threshold
                ].sort_values('Readiness Score', ascending=False).head(10)
                
                if not top_states.empty:
                    # Style the dataframe based on performance
                    def highlight_performance(row):
                        styles = [''] * len(row)
                        readiness = row['Readiness Score']
                        
                        if readiness >= 70:
                            color = 'background-color: #d4edda'  # Light green
                        elif readiness >= 50:
                            color = 'background-color: #fff3cd'  # Light yellow
                        else:
                            color = 'background-color: #f8d7da'  # Light red
                        
                        # Apply to readiness score column
                        styles[-1] = color + '; font-weight: bold'
                        return styles
                    
                    try:
                        styled_states = top_states.style.apply(highlight_performance, axis=1)
                        st.dataframe(styled_states, use_container_width=True)
                    except:
                        st.dataframe(top_states, use_container_width=True)

        with tab5:
            st.markdown("### 👥 Team Performance & Data Ownership Analysis")
            
            if 'Owner' in filtered_df.columns and filtered_df['Owner'].notna().any():
                # Enhanced team performance metrics
                owner_stats = filtered_df.groupby('Owner').agg({
                    'Company': 'count',
                    'EPR Certified': lambda x: sum(x == 'Certified'),
                    'Documents': lambda x: sum(x == 'With Documents'),
                    'Data_Quality_Score': ['mean', 'std'],
                    'Capacity': 'sum',
                    'States': 'nunique'
                }).round(2)
                
                # Flatten column names
                owner_stats.columns = [
                    'Total Contacts', 'EPR Certified', 'With Documents', 
                    'Avg Quality (%)', 'Quality Std Dev', 'Total Capacity (MT)', 'States Covered'
                ]
                
                # Calculate performance rates
                owner_stats['EPR Success Rate (%)'] = (
                    owner_stats['EPR Certified'] / owner_stats['Total Contacts'] * 100
                ).round(1)
                owner_stats['Doc Success Rate (%)'] = (
                    owner_stats['With Documents'] / owner_stats['Total Contacts'] * 100
                ).round(1)
                
                # Calculate business ready companies
                business_ready_by_owner = filtered_df[
                    (filtered_df['EPR Certified'] == 'Certified') & 
                    (filtered_df['Documents'] == 'With Documents')
                ].groupby('Owner').size().to_dict()
                
                owner_stats['Business Ready'] = owner_stats.index.map(
                    lambda x: business_ready_by_owner.get(x, 0)
                )
                owner_stats['Business Ready Rate (%)'] = (
                    owner_stats['Business Ready'] / owner_stats['Total Contacts'] * 100
                ).round(1)
                
                # Calculate overall performance score
                owner_stats['Performance Score'] = (
                    (owner_stats['EPR Success Rate (%)'] * 0.4) + 
                    (owner_stats['Doc Success Rate (%)'] * 0.3) + 
                    (owner_stats['Avg Quality (%)'] * 0.3)
                ).round(1)
                
                # Sort by performance score
                owner_stats_display = owner_stats.sort_values('Performance Score', ascending=False)
                
                st.markdown("### 📊 Team Performance Leaderboard")
                st.dataframe(owner_stats_display, use_container_width=True)
                
                # Team performance visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Performance scatter plot
                    if len(owner_stats) > 1:
                        fig_team_scatter = px.scatter(
                            owner_stats.reset_index(),
                            x='Total Contacts',
                            y='EPR Success Rate (%)',
                            size='Total Capacity (MT)',
                            color='Performance Score',
                            hover_name='Owner',
                            title="🎯 Team Performance: Volume vs Success Rate",
                            color_continuous_scale='viridis'
                        )
                        fig_team_scatter.update_layout(height=400)
                        st.plotly_chart(fig_team_scatter, use_container_width=True)
                
                with col2:
                    # Performance ranking bar chart
                    if len(owner_stats) > 1:
                        top_performers = owner_stats_display.head(10)
                        fig_team_bar = px.bar(
                            x=top_performers['Performance Score'],
                            y=top_performers.index,
                            orientation='h',
                            title="🏆 Top 10 Team Performance Scores",
                            labels={'x': 'Performance Score', 'y': 'Team Member'},
                            color=top_performers['Performance Score'],
                            color_continuous_scale='RdYlGn'
                        )
                        fig_team_bar.update_layout(height=400)
                        st.plotly_chart(fig_team_bar, use_container_width=True)
                
                # Team insights
                if len(owner_stats) > 0:
                    best_performer = owner_stats_display.index[0]
                    best_score = owner_stats_display.iloc[0]['Performance Score']
                    
                    most_productive = owner_stats['Total Contacts'].idxmax()
                    most_contacts = owner_stats.loc[most_productive, 'Total Contacts']
                    
                    highest_quality = owner_stats['Avg Quality (%)'].idxmax()
                    quality_score = owner_stats.loc[highest_quality, 'Avg Quality (%)']
                    
                    st.markdown("### 🌟 Team Recognition")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.success(f"🏆 **Top Performer**\n\n{best_performer}\n\nScore: {best_score:.1f}/100")
                    
                    with col2:
                        st.info(f"📊 **Most Productive**\n\n{most_productive}\n\nContacts: {int(most_contacts)}")
                    
                    with col3:
                        st.warning(f"💎 **Quality Leader**\n\n{highest_quality}\n\nQuality: {quality_score:.1f}%")
            else:
                st.info("No team/owner data available for performance analysis.")

        with tab6:
            st.markdown("### 🔍 Data Quality & Integrity Analysis")
            
            if len(filtered_df) > 0:
                # Data quality distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    # Quality score histogram
                    fig_quality_hist = px.histogram(
                        filtered_df,
                        x='Data_Quality_Score',
                        nbins=20,
                        title="📊 Data Quality Score Distribution",
                        labels={'x': 'Data Quality Score (%)', 'y': 'Number of Companies'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig_quality_hist.add_vline(
                        x=filtered_df['Data_Quality_Score'].mean(), 
                        line_dash="dash", 
                        annotation_text=f"Average: {filtered_df['Data_Quality_Score'].mean():.1f}%"
                    )
                    fig_quality_hist.update_layout(height=400)
                    st.plotly_chart(fig_quality_hist, use_container_width=True)
                
                with col2:
                    # Quality categories pie chart
                    def quality_category(score):
                        if score >= 80:
                            return 'Excellent (80%+)'
                        elif score >= 60:
                            return 'Good (60-79%)'
                        elif score >= 40:
                            return 'Fair (40-59%)'
                        else:
                            return 'Poor (<40%)'
                    
                    filtered_df['Quality_Category'] = filtered_df['Data_Quality_Score'].apply(quality_category)
                    quality_counts = filtered_df['Quality_Category'].value_counts()
                    
                    fig_quality_pie = px.pie(
                        values=quality_counts.values,
                        names=quality_counts.index,
                        title="🎯 Data Quality Categories",
                        color_discrete_map={
                            'Excellent (80%+)': '#28a745',
                            'Good (60-79%)': '#17a2b8',
                            'Fair (40-59%)': '#ffc107',
                            'Poor (<40%)': '#dc3545'
                        }
                    )
                    fig_quality_pie.update_layout(height=400)
                    st.plotly_chart(fig_quality_pie, use_container_width=True)
                
                # Field completeness analysis
                st.markdown("### 📋 Field Completeness Analysis")
                
                important_fields = ['Company', 'States', 'Contact No.', 'Email', 'EPR Certified', 'Documents', 'Category', 'Capacity']
                completeness_data = []
                
                for field in important_fields:
                    if field in filtered_df.columns:
                        total_entries = len(filtered_df)
                        if field in ['Company', 'States', 'EPR Certified', 'Documents', 'Category']:
                            valid_entries = len(filtered_df[
                                (filtered_df[field].notna()) & 
                                (filtered_df[field] != 'Unknown') & 
                                (filtered_df[field] != 'Not Specified') &
                                (filtered_df[field] != '')
                            ])
                        elif field == 'Contact No.':
                            if 'Valid_Contact' in filtered_df.columns:
                                valid_entries = len(filtered_df[filtered_df['Valid_Contact'] == True])
                            else:
                                valid_entries = len(filtered_df[filtered_df[field].str.len() >= 10])
                        elif field == 'Email':
                            if 'Valid_Email' in filtered_df.columns:
                                valid_entries = len(filtered_df[filtered_df['Valid_Email'] == True])
                            else:
                                valid_entries = len(filtered_df[filtered_df[field].str.contains('@', na=False)])
                        elif field == 'Capacity':
                            valid_entries = len(filtered_df[filtered_df[field] > 0])
                        else:
                            valid_entries = len(filtered_df[filtered_df[field].notna()])
                        
                        completeness_pct = (valid_entries / total_entries * 100) if total_entries > 0 else 0
                        
                        completeness_data.append({
                            'Field': field,
                            'Valid Entries': valid_entries,
                            'Total Entries': total_entries,
                            'Completeness (%)': completeness_pct,
                            'Missing': total_entries - valid_entries
                        })
                
                if completeness_data:
                    completeness_df = pd.DataFrame(completeness_data)
                    completeness_df = completeness_df.sort_values('Completeness (%)', ascending=False)
                    
                    # Create completeness visualization
                    fig_completeness = px.bar(
                        completeness_df,
                        x='Field',
                        y='Completeness (%)',
                        title="📊 Data Field Completeness Analysis",
                        color='Completeness (%)',
                        color_continuous_scale='RdYlGn',
                        text='Completeness (%)'
                    )
                    fig_completeness.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_completeness.update_layout(height=400)
                    st.plotly_chart(fig_completeness, use_container_width=True)
                    
                    # Show completeness table
                    st.dataframe(completeness_df, use_container_width=True)
                    
                    # Data quality insights
                    st.markdown("### 💡 Data Quality Insights")
                    
                    avg_completeness = completeness_df['Completeness (%)'].mean()
                    lowest_field = completeness_df.iloc[-1]
                    highest_field = completeness_df.iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if avg_completeness >= 80:
                            st.success(f"✅ **Overall Quality: Excellent**\n\nAverage completeness: {avg_completeness:.1f}%\n\nData is highly reliable for analysis.")
                        elif avg_completeness >= 60:
                            st.warning(f"⚠️ **Overall Quality: Good**\n\nAverage completeness: {avg_completeness:.1f}%\n\nSome fields need attention.")
                        else:
                            st.error(f"❌ **Overall Quality: Needs Improvement**\n\nAverage completeness: {avg_completeness:.1f}%\n\nSignificant data gaps present.")
                    
                    with col2:
                        st.info(f"🎯 **Strongest Field**\n\n{highest_field['Field']}\n\n{highest_field['Completeness (%)']:.1f}% complete\n\n{highest_field['Valid Entries']}/{highest_field['Total Entries']} entries")
                    
                    with col3:
                        st.warning(f"🔧 **Needs Attention**\n\n{lowest_field['Field']}\n\n{lowest_field['Completeness (%)']:.1f}% complete\n\n{lowest_field['Missing']} missing entries")
        
        # Enhanced Data Table with better functionality
        st.markdown("## 📋 Detailed Company Database")

        # Remove empty rows before displaying
        display_df = filtered_df.dropna(how='all')
        display_df = display_df[display_df['Company'] != 'Unknown Company']
        
        if len(display_df) > 0:
            # FIXED: Show distributed capacity in the table display
            st.markdown("#### 🎯 Customize Table Display")
            st.info("💡 **Note**: The capacity shown in the table is the ORIGINAL total capacity per company. For category-specific distributed capacity, refer to the Category Intelligence tab.")
            
            # Enhanced column selection with better organization
            essential_columns = ['Company', 'States', 'Contact No.', 'EPR Certified', 'Category']
            business_columns = ['Email', 'Documents', 'Capacity', 'Data_Quality_Score']
            admin_columns = ['Date', 'Owner', 'Type', 'Remarks']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Essential Fields**")
                essential_selected = []
                for col in essential_columns:
                    if col in display_df.columns:
                        if st.checkbox(col, value=True, key=f"essential_{col}"):
                            essential_selected.append(col)
            
            with col2:
                st.markdown("**Business Fields**")
                business_selected = []
                for col in business_columns:
                    if col in display_df.columns:
                        default_value = col in ['Email', 'Capacity', 'Data_Quality_Score']
                        if st.checkbox(col, value=default_value, key=f"business_{col}"):
                            business_selected.append(col)
            
            with col3:
                st.markdown("**Administrative Fields**")
                admin_selected = []
                for col in admin_columns:
                    if col in display_df.columns:
                        default_value = col == 'Date'
                        if st.checkbox(col, value=default_value, key=f"admin_{col}"):
                            admin_selected.append(col)
            
            # Combine selected columns
            display_columns = essential_selected + business_selected + admin_selected
            
            if display_columns:
                # Show entry count and filtering info
                st.markdown(f"#### 📊 Showing {len(display_df):,} companies")
                
                if len(filtered_df) != len(df_to_use):
                    reduction = len(df_to_use) - len(filtered_df)
                    st.info(f"🔍 Filtered out {reduction:,} companies ({(reduction/len(df_to_use)*100):.1f}%) based on your criteria")
                
                # Export functionality
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📊 Export to CSV", help="Download current view as CSV file"):
                        csv_data = display_df[display_columns].to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name=f"recyclers_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    show_only_qualified = st.checkbox("✅ Qualified Leads Only", help="Show only companies with EPR certification AND documents")
                
                with col3:
                    show_high_capacity = st.checkbox("🏭 High Capacity Only", help="Show only companies with >500 MT capacity")
                
                with col4:
                    show_contact_available = st.checkbox("📞 Contact Available", help="Show only companies with valid contact info")
                
                # Apply additional display filters
                if show_only_qualified:
                    display_df = display_df[
                        (display_df['EPR Certified'] == 'Certified') & 
                        (display_df['Documents'] == 'With Documents')
                    ]
                
                if show_high_capacity:
                    display_df = display_df[display_df['Capacity'] > 500]
                
                if show_contact_available:
                    if 'Valid_Contact' in display_df.columns:
                        display_df = display_df[display_df['Valid_Contact'] == True]
                    else:
                        display_df = display_df[display_df['Contact No.'].str.len() >= 10]
                
                # Format data for better display
                display_data = display_df[display_columns].copy()
                
                # Format specific columns
                if 'Capacity' in display_columns:
                    display_data['Capacity'] = display_data['Capacity'].apply(
                        lambda x: f"{x:,.0f} MT/year (Total)" if pd.notna(x) and x > 0 else "Not Specified"
                    )
                
                if 'Data_Quality_Score' in display_columns:
                    display_data['Data_Quality_Score'] = display_data['Data_Quality_Score'].apply(
                        lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
                    )
                
                if 'Contact No.' in display_columns:
                    display_data['Contact No.'] = display_data['Contact No.'].apply(
                        lambda x: str(x) if pd.notna(x) and str(x).strip() != '' else "Not Available"
                    )
                
                if 'Date' in display_columns:
                    display_data['Date'] = pd.to_datetime(display_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                    display_data['Date'] = display_data['Date'].fillna('Not Specified')
                
                # Display the enhanced table
                if len(display_data) > 0:
                    st.dataframe(display_data, use_container_width=True, height=600)
                    
                    # Enhanced legend
                    st.markdown("""
                    **🎨 Table Color Guide:**
                    - 🟢 **Green rows**: Excellent data quality (80%+) | 🟢 **Green EPR**: Certified
                    - 🔵 **Blue rows**: Good data quality (60-79%) | 🔵 **Blue EPR**: In Process  
                    - 🟡 **Yellow rows**: Fair data quality (40-59%) | 🟡 **Yellow EPR**: Ready to Certify
                    - 🔴 **Red rows**: Poor data quality (<40%)
                    """)
                    
                    # FIXED: Enhanced summary statistics with proper data source
                    st.markdown("### 📊 Selection Summary")
                    
                    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

                    with summary_col1:
                        # FIXED: Use display_df (not display_data which is formatted) for accurate counts
                        certified_count = len(display_df[display_df['EPR Certified'] == 'Certified']) if 'EPR Certified' in display_df.columns else 0
                        st.metric("✅ EPR Certified", certified_count)

                    with summary_col2:
                        # FIXED: Use display_df (not display_data which is formatted) for accurate counts  
                        with_docs = len(display_df[display_df['Documents'] == 'With Documents']) if 'Documents' in display_df.columns else 0
                        st.metric("📄 With Documents", with_docs)

                    with summary_col3:
                        # FIXED: Use display_df for accurate email count
                        if 'Valid_Email' in display_df.columns:
                            with_email = len(display_df[display_df['Valid_Email'] == True])
                        else:
                            with_email = len(display_df[display_df['Email'].str.contains('@', na=False)]) if 'Email' in display_df.columns else 0
                        st.metric("📧 Email Available", with_email)

                    with summary_col4:
                        if 'Capacity' in display_df.columns:
                            # FIXED: Extract numeric values from original data, not formatted display_data
                            numeric_capacity = display_df['Capacity'].sum()
                            st.metric("⚖️ Total Capacity", f"{numeric_capacity:,.0f} MT/year")
                        else:
                            st.metric("📋 Total Entries", len(display_data))
                    
                else:
                    st.warning("⚠️ No companies match your display criteria.")
                    st.info("💡 Try adjusting the additional display filters above.")
            else:
                st.warning("⚠️ Please select at least one column to display.")
        else:
            st.error("⚠️ No data available for display. Please check your filters.")

    except Exception as e:
        st.error(f"❌ Critical error in main dashboard: {str(e)}")
        st.info("🔄 Please refresh the page and try again.")

else:
    st.error("❌ Unable to load data. Please check your internet connection and try again.")
    st.info("🔄 If the issue persists, the Google Sheets might be temporarily unavailable.")

# Enhanced Footer with additional information
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #6c757d; padding: 1.5rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 10px; margin-top: 2rem;'>
    <h4 style='color: #495057; margin-bottom: 1rem;'>🏭 Enhanced Plastic Waste Recyclers Dashboard</h4>
    <p><strong>Advanced Business Intelligence Platform for EPR Compliance & Waste Management</strong></p>
    <p>Real-time data analysis • Comprehensive filtering • Export capabilities • Quality scoring</p>
    <small>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</small><br>
    <small>Developed with ❤️ for Tidy Rabbit</small>
</div>
""", unsafe_allow_html=True)

# Debug information (can be removed in production)
if st.sidebar.checkbox("🔧 Show Debug Info", help="Display technical information for debugging"):
    with st.sidebar.expander("🔍 Debug Information"):
        st.write(f"**Data Load Time:** {datetime.now()}")
        st.write(f"**Total Memory Usage:** {len(df_to_use) if 'df_to_use' in locals() else 0} rows")
        st.write(f"**Active Filters:** {len([x for x in [company_search, state_filter, category_filter, epr_filter, doc_filter] if x])}")
        st.write(f"**Session State Keys:** {len(st.session_state)}")
        st.write(f"**Dataset Choice:** {dataset_choice}")
        st.write(f"**Recyclers Data:** {len(recyclers_data) if recyclers_data is not None else 0}")
        st.write(f"**Positive Data:** {len(positive_data) if positive_data is not None else 0}")
        if 'df_to_use' in locals():
            st.write(f"**Combined Data:** {len(df_to_use)}")
            st.write(f"**Filtered Data:** {len(filtered_df) if 'filtered_df' in locals() else 0}")

# Optional: Add performance monitoring
if st.sidebar.checkbox("📊 Performance Monitor", help="Show app performance metrics"):
    try:
        import psutil
        import time
        
        with st.sidebar.expander("⚡ Performance Metrics"):
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            st.metric("CPU Usage", f"{cpu_usage:.1f}%")
            st.metric("Memory Usage", f"{memory_usage:.1f}%")
            st.write(f"**Render Time:** {time.time():.2f}s")
    except ImportError:
        st.sidebar.info("📊 Performance monitoring requires psutil. Add 'psutil' to requirements.txt")

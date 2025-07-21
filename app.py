import streamlit as st
import json
import pandas as pd
from datetime import datetime
import requests
import time
import re
import io
import xlsxwriter
import warnings
import plotly.express as px
import plotly.graph_objects as go
warnings.filterwarnings('ignore')

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="31-Grafa Rasmiy Tahlil Tizimi",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    .main-header {
        color: #1E3A8A !important;
        text-align: center;
        font-size: 3.5rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .sub-header {
        text-align: center;
        color: #059669;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        margin-bottom: 1.5rem;
    }
    
    .grafa-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.8rem 0;
        border-left: 4px solid #1E3A8A;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .filled-section {
        border-left-color: #059669 !important;
        background: #ecfdf5 !important;
    }
    
    .missing-section {
        border-left-color: #DC2626 !important;
        background: #fef2f2 !important;
    }
    
    .required-badge {
        background: #DC2626;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    
    .optional-badge {
        background: #6B7280;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    
    .section-number {
        background: #1E3A8A;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        margin-right: 8px;
        display: inline-block;
        min-width: 30px;
        text-align: center;
    }
    
    .success-message {
        background: linear-gradient(90deg, #059669, #047857);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: linear-gradient(90deg, #D97706, #B45309);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(90deg, #DC2626, #B91C1C);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Rasmiy 31-grafa bo'limlari (Adliya vazirligi 2773-son yo'riqnomasiga asosan)
GRAFA_31_SECTIONS = {
    "1_tovar_tavsifi": {
        "name": "1. Tovar tavsifi (nomi, markalari, modellari, standartlari)",
        "description": "Tovarning nomi, tovar belgilari, markalari, modellari, artikullari, navlari, standartlari va texnik tavsiflari, energiya samaradorligi klassi",
        "json_fields": [
            "наименование_товара", "товарный_знак", "название_бренда", "модель", 
            "артикул", "стандарт", "технические_характеристики", "класс_энергоэффективности",
            "состав_качества", "материал"
        ],
        "keywords": ["наименование", "товар", "марка", "модель", "бренд", "характеристики"],
        "required": True,
        "critical": True
    },
    "2_oram_malumotlari": {
        "name": "2. O'ram ma'lumotlari (turi va miqdori)",
        "description": "Tovar o'rami turi va o'ramlar miqdori, yuk joylari soni",
        "json_fields": ["количество", "единица_измерения", "упаковка", "тип_упаковки"],
        "keywords": ["упаковка", "количество", "штук", "коробка", "тара"],
        "required": True,
        "critical": True
    },
    "3_konteyner_raqamlari": {
        "name": "3. Konteyner raqamlari",
        "description": "Konteynerlarda tashiladigan tovarlar uchun konteyner raqamlari",
        "json_fields": ["контейнер", "номер_контейнера", "контейнер_номер"],
        "keywords": ["контейнер", "номер"],
        "required": False,
        "critical": False
    },
    "4_aksiz_markalari": {
        "name": "4. Aksiz markalari",
        "description": "Aksiz markalar seriyalari, raqamlari va miqdori",
        "json_fields": ["акциз", "марка", "акцизная_марка"],
        "keywords": ["акциз", "марка"],
        "required": False,
        "critical": False
    },
    "5_yetkazib_berish": {
        "name": "5. Yetkazib berish muddati",
        "description": "Quvur transporti va elektr uzatish liniyalari uchun yetkazib berish muddati",
        "json_fields": ["доставка", "период", "срок_поставки"],
        "keywords": ["доставка", "период", "срок"],
        "required": False,
        "critical": False
    },
    "6_import_kodi": {
        "name": "6. Agregatsiyalangan import kodi",
        "description": "Tovarlarning agregatsiyalangan import kodi",
        "json_fields": ["импорт_код", "код_импорта"],
        "keywords": ["импорт", "код"],
        "required": False,
        "critical": False
    },
    "7_yaroqlilik_muddati": {
        "name": "7. Yaroqlilik muddati",
        "description": "Oziq-ovqat mahsulotlari va dori vositalarining yaroqlilik muddati",
        "json_fields": ["срок_годности", "дата_истечения", "срок_действия"],
        "keywords": ["срок", "годность", "истечение", "дата"],
        "required": False,
        "critical": False
    },
    "8_investitsiya_kodi": {
        "name": "8. Investitsiya dasturi kodi",
        "description": "Investitsiya dasturi loyihalari uchun kodlar (101, 102, 103, 201-203, 301, 000)",
        "json_fields": ["инвестиция", "проект_код", "код_проекта"],
        "keywords": ["инвестиция", "проект", "код"],
        "required": False,
        "critical": False
    },
    "9_soha_kodi": {
        "name": "9. Texnologik asbob-uskunalar soha kodi",
        "description": "TIF TN 8401-9033 pozitsiyalari uchun soha kodi",
        "json_fields": ["отрасль", "сфера", "код_отрасли"],
        "keywords": ["отрасль", "сфера", "оборудование"],
        "required": False,
        "critical": False
    },
    "10_ishlab_chiqarilgan_yili": {
        "name": "10. Ishlab chiqarilgan yili va texnik tasnifi",
        "description": "Texnologik asbob-uskunalarning ishlab chiqarilgan yili va texnik tasnifi",
        "json_fields": ["дата_изготовления", "год_производства", "техническая_классификация"],
        "keywords": ["дата", "год", "изготовления", "производства", "классификация"],
        "required": True,
        "critical": True
    },
    "11_davlat_xaridlari": {
        "name": "11. Davlat xaridlari kodi",
        "description": "Davlat xaridlari kodi: 01 - davlat xaridlari, 02 - davlat xaridlari emas",
        "json_fields": ["государственные_закупки", "код_закупки"],
        "keywords": ["государственные", "закупки"],
        "required": False,
        "critical": False
    }
}

# Maydonlar moslik jadvali
FIELD_MAPPING = {
    # 1. Tovar tavsifi
    "наименование_товара": "1_tovar_tavsifi",
    "товарный_знак": "1_tovar_tavsifi",
    "название_бренда": "1_tovar_tavsifi", 
    "модель": "1_tovar_tavsifi",
    "артикул": "1_tovar_tavsifi",
    "стандарт": "1_tovar_tavsifi",
    "технические_характеристики": "1_tovar_tavsifi",
    "класс_энергоэффективности": "1_tovar_tavsifi",
    "состав_качества": "1_tovar_tavsifi",
    "материал": "1_tovar_tavsifi",
    
    # 2. O'ram ma'lumotlari
    "количество": "2_oram_malumotlari",
    "единица_измерения": "2_oram_malumotlari",
    "упаковка": "2_oram_malumotlari",
    "тип_упаковки": "2_oram_malumotlari",
    
    # 3. Konteyner
    "контейнер": "3_konteyner_raqamlari",
    "номер_контейнера": "3_konteyner_raqamlari",
    
    # 4. Aksiz
    "акциз": "4_aksiz_markalari",
    "марка": "4_aksiz_markalari",
    
    # 5. Yetkazib berish
    "доставка": "5_yetkazib_berish",
    "период": "5_yetkazib_berish",
    "срок_поставки": "5_yetkazib_berish",
    
    # 7. Yaroqlilik
    "срок_годности": "7_yaroqlilik_muddati",
    "дата_истечения": "7_yaroqlilik_muddati",
    
    # 10. Ishlab chiqarilgan yili
    "дата_изготовления": "10_ishlab_chiqarilgan_yili",
    "год_производства": "10_ishlab_chiqarilgan_yili"
}

# Serper API konfiguratsiyasi
SERPER_API_KEYS = [
    "f73aaf81a1604fc9270c38b7b7f47b9ad9e90fca",
    "4f13f583cdbb95a1771adcd2f091ab3ec1bc49b8"
]
SERPER_URL = "https://google.serper.dev/search"

class SerperAPIClient:
    def __init__(self):
        self.api_keys = SERPER_API_KEYS
        self.current_key_index = 0
        self.base_url = SERPER_URL
        
    def get_next_api_key(self):
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def search_information(self, query, max_results=3):
        headers = {
            "X-API-KEY": self.get_next_api_key(),
            "Content-Type": "application/json"
        }
        
        data = {"q": query, "num": max_results}
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            snippets = []
            for result in results.get("organic", []):
                snippet = result.get("snippet", "")
                if snippet and len(snippet) > 20:
                    snippets.append(snippet)
            
            return " ".join(snippets[:2]) if snippets else "ma'lumot topilmadi"
            
        except Exception as e:
            return f"xato: {str(e)}"

class Grafa31OfficialProcessor:
    """Rasmiy 31-Grafa bo'yicha ma'lumotlarni qayta ishlash"""
    
    def __init__(self):
        self.api_client = SerperAPIClient()
    
    def extract_product_basic_info(self, product):
        """Mahsulotning asosiy ma'lumotlarini ajratish"""
        name = product.get('наименование_товара', '')
        brand = product.get('название_бренда', product.get('товарный_знак', ''))
        model = product.get('модель', '')
        
        full_name = f"{name} {brand} {model}".strip()
        
        return {
            'name': str(name).strip(),
            'brand': str(brand).strip() if brand else '',
            'model': str(model).strip() if model else '',
            'full_name': full_name
        }
    
    def map_fields_to_grafa31(self, product):
        """JSON maydonlarini 31-grafa bo'limlariga moslashtirish"""
        grafa_data = {}
        
        for field_name, value in product.items():
            if not value or str(value).strip().lower() in ['', 'not specified', 'не указано', 'не указан']:
                continue
                
            if field_name in FIELD_MAPPING:
                grafa_section = FIELD_MAPPING[field_name]
                if grafa_section not in grafa_data:
                    grafa_data[grafa_section] = []
                grafa_data[grafa_section].append(str(value).strip())
        
        # Ma'lumotlarni birlashtirish
        for section_key in grafa_data:
            grafa_data[section_key] = "; ".join(grafa_data[section_key])
            
        return grafa_data
    
    def find_missing_sections(self, grafa_data):
        """Yetishmayotgan bo'limlarni topish"""
        missing_required = []
        missing_optional = []
        
        for section_key, section_info in GRAFA_31_SECTIONS.items():
            if section_key not in grafa_data:
                if section_info.get('required', False):
                    missing_required.append(section_key)
                else:
                    missing_optional.append(section_key)
        
        return {
            'required': missing_required,
            'optional': missing_optional,
            'all': missing_required + missing_optional
        }
    
    def calculate_completion_rate(self, grafa_data):
        """To'ldirilish foizini hisoblash"""
        total_sections = len(GRAFA_31_SECTIONS)
        filled_sections = len(grafa_data)
        
        required_sections = [k for k, v in GRAFA_31_SECTIONS.items() if v.get('required', False)]
        filled_required = sum(1 for section in required_sections if section in grafa_data)
        
        # Umumiy to'ldirilish foizi
        general_completion = (filled_sections / total_sections) * 100
        
        # Majburiy bo'limlar to'ldirilish foizi
        required_completion = (filled_required / len(required_sections)) * 100 if required_sections else 100
        
        return {
            'general': general_completion,
            'required': required_completion,
            'total_sections': total_sections,
            'filled_sections': filled_sections,
            'required_sections': len(required_sections),
            'filled_required': filled_required
        }
    
    def create_search_query(self, product_info, section_key):
        """Bo'lim uchun qidiruv so'rovini yaratish"""
        section_info = GRAFA_31_SECTIONS[section_key]
        keywords = section_info.get('keywords', [])
        
        base_query = product_info['full_name']
        if keywords:
            query = f"{base_query} {' '.join(keywords[:2])}"
        else:
            query = base_query
            
        return query.strip()
    
    def fill_missing_section(self, product_info, section_key, progress_container=None):
        """Yetishmayotgan bo'limni to'ldirish"""
        query = self.create_search_query(product_info, section_key)
        
        if progress_container:
            progress_container.write(f"🔍 Qidirilmoqda: {query}")
        
        result = self.api_client.search_information(query)
        
        if result and "ma'lumot topilmadi" not in result and "xato" not in result:
            if len(result) > 200:
                result = result[:200] + "..."
                
            if progress_container:
                progress_container.write(f"✅ Topildi: {result[:100]}...")
            return result
        else:
            section_name = GRAFA_31_SECTIONS[section_key]['name']
            if progress_container:
                progress_container.write(f"❌ Topilmadi: {section_name}")
            return "ma'lumot topilmadi"
    
    def process_single_product(self, product):
        """Bitta mahsulotni qayta ishlash"""
        try:
            product_info = self.extract_product_basic_info(product)
            grafa_data = self.map_fields_to_grafa31(product)
            missing_sections = self.find_missing_sections(grafa_data)
            completion_rates = self.calculate_completion_rate(grafa_data)
            
            return {
                'original_product': product,
                'product_info': product_info,
                'grafa_data': grafa_data,
                'missing_sections': missing_sections,
                'completion_rates': completion_rates
            }
        except Exception as e:
            # Xato yuz berganda standart qiymatlar qaytarish
            return {
                'original_product': product,
                'product_info': {'name': 'Xato', 'brand': '', 'model': '', 'full_name': 'Xato'},
                'grafa_data': {},
                'missing_sections': {'required': [], 'optional': [], 'all': []},
                'completion_rates': {
                    'general': 0,
                    'required': 0,
                    'total_sections': 11,
                    'filled_sections': 0,
                    'required_sections': 5,
                    'filled_required': 0
                }
            }

def read_uploaded_file(uploaded_file):
    """Yuklangan faylni o'qish"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'json':
            json_data = json.load(uploaded_file)
            return json_data, 'json'
        else:
            st.error(f"Faqat JSON formatlar qo'llab-quvvatlanadi")
            return None, None
    except Exception as e:
        st.error(f"Faylni o'qishda xatolik: {str(e)}")
        return None, None

def create_completion_chart(processed_data):
    """To'ldirilish foizi diagrammasi"""
    if not processed_data:
        return None
    
    general_rates = [item.get('completion_rates', {}).get('general', 0) for item in processed_data]
    required_rates = [item.get('completion_rates', {}).get('required', 0) for item in processed_data]
    product_names = [item.get('product_info', {}).get('name', 'Noma\'lum')[:25] + '...' 
                    if len(item.get('product_info', {}).get('name', '')) > 25 
                    else item.get('product_info', {}).get('name', 'Noma\'lum') for item in processed_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Umumiy To\'ldirilish',
        x=product_names,
        y=general_rates,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Majburiy Bo\'limlar',
        x=product_names,
        y=required_rates,
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='31-Grafa To\'ldirilish Foizi',
        xaxis_title='Tovarlar',
        yaxis_title='To\'ldirilish Foizi (%)',
        barmode='group',
        xaxis_tickangle=-45,
        height=500
    )
    
    return fig

def create_sections_stats_chart(processed_data):
    """Bo'limlar statistikasi diagrammasi"""
    if not processed_data:
        return None
    
    section_stats = {}
    total_products = len(processed_data)
    
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        filled_count = sum(1 for item in processed_data if section_key in item.get('grafa_data', {}))
        section_stats[section_info['name'][:30]] = {
            'filled': filled_count,
            'percentage': (filled_count / total_products) * 100,
            'required': section_info.get('required', False)
        }
    
    section_names = list(section_stats.keys())
    percentages = [section_stats[name]['percentage'] for name in section_names]
    colors = ['red' if section_stats[name]['required'] else 'blue' for name in section_names]
    
    fig = px.bar(
        x=section_names,
        y=percentages,
        title='31-Grafa Bo\'limlari To\'ldirilish Statistikasi',
        labels={'x': 'Bo\'limlar', 'y': 'To\'ldirilish Foizi (%)'},
        color=colors,
        color_discrete_map={'red': '#DC2626', 'blue': '#1E3A8A'}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        showlegend=False
    )
    
    return fig

def export_to_excel(processed_data):
    """Excel formatga eksport qilish"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_data = []
            
            for idx, item in enumerate(processed_data):
                product_info = item.get('product_info', {})
                completion_rates = item.get('completion_rates', {})
                
                row = {
                    'ID': idx + 1,
                    'Tovar_Nomi': product_info.get('name', ''),
                    'Brend': product_info.get('brand', ''),
                    'Model': product_info.get('model', ''),
                    'Umumiy_Toldirilish_%': f"{completion_rates.get('general', 0):.1f}%",
                    'Majburiy_Toldirilish_%': f"{completion_rates.get('required', 0):.1f}%",
                    'Toldirilgan_Bolimlar': completion_rates.get('filled_sections', 0),
                    'Jami_Bolimlar': completion_rates.get('total_sections', 0)
                }
                
                # 31-Grafa bo'limlarini qo'shish
                grafa_data = item.get('grafa_data', {})
                for section_key, section_info in GRAFA_31_SECTIONS.items():
                    column_name = f"Grafa_{section_key.split('_')[0]}"
                    row[column_name] = grafa_data.get(section_key, '')
                
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            df.to_excel(writer, sheet_name='31-Grafa Rasmiy Tahlil', index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        st.error(f"Excel eksport xatosi: {str(e)}")
        return None

def main():
    # Session state ni boshlash
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = []
    if 'processor' not in st.session_state:
        st.session_state.processor = Grafa31OfficialProcessor()

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">📋 31-Grafa Rasmiy Tahlil Tizimi</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Adliya vazirligi 2773-son yo\'riqnomasiga muvofiq</p>', unsafe_allow_html=True)

    # Sidebar navigatsiyasi
    st.sidebar.markdown("## 🧭 Navigatsiya")
    
    nav_options = {
        'upload': '📁 1. Ma\'lumot Yuklash',
        'analysis': '🔍 2. Rasmiy Tahlil',
        'search': '🌐 3. Web Search',
        'report': '📄 4. Rasmiy Hisobot'
    }
    
    for key, label in nav_options.items():
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
    
    # Rasmiy 31-grafa ma'lumotlari
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📋 31-Grafa Bo'limlari")
    
    required_count = sum(1 for v in GRAFA_31_SECTIONS.values() if v.get('required', False))
    optional_count = len(GRAFA_31_SECTIONS) - required_count
    
    st.sidebar.metric("Majburiy bo'limlar", required_count)
    st.sidebar.metric("Ixtiyoriy bo'limlar", optional_count)
    st.sidebar.metric("Jami bo'limlar", len(GRAFA_31_SECTIONS))
    
    # Joriy holat
    if st.session_state.json_data:
        if 'results' in st.session_state.json_data:
            total_products = len(st.session_state.json_data['results'])
            st.sidebar.metric("Yuklangan tovarlar", total_products)
        if st.session_state.processed_data:
            st.sidebar.metric("Tahlil qilingan", len(st.session_state.processed_data))
    else:
        st.sidebar.info("JSON fayl yuklanmagan")
    
    # Ma'lumotlarni tozalash tugmasi
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Ma'lumotlarni Tozalash", help="Barcha yuklangan ma'lumotlarni tozalash"):
        st.session_state.json_data = None
        st.session_state.processed_data = []
        st.session_state.current_page = 'upload'
        st.rerun()

    # Sahifalar
    if st.session_state.current_page == 'upload':
        show_upload_page()
    elif st.session_state.current_page == 'analysis':
        show_analysis_page()
    elif st.session_state.current_page == 'search':
        show_search_page()
    elif st.session_state.current_page == 'report':
        show_report_page()

def show_upload_page():
    """Ma'lumot yuklash sahifasi"""
    st.markdown("# 📁 JSON Fayl Yuklash")
    st.markdown("---")
    
    # Rasmiy ma'lumot
    st.markdown("""
    ### 📖 31-Grafa Rasmiy Tahlil Tizimi
    
    Bu tizim **O'zbekiston Respublikasi Adliya vazirligining 2773-son yo'riqnomasining 31-grafasi** 
    bo'yicha tovar ma'lumotlarini rasmiy talablarga muvofiq tahlil qiladi.
    
    **31-Grafa: "Yuk joylari va tovar tavsifi"** - "Markirovka va miqdor — konteynerlar raqami — tovar tavsifi"
    """)
    
    # 31-grafa bo'limlarini ko'rsatish
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⭐ Majburiy Bo'limlar")
        for section_key, section_info in GRAFA_31_SECTIONS.items():
            if section_info.get('required', False):
                st.markdown(f"""
                <div class="grafa-section">
                    <span class="section-number">{section_key.split('_')[0]}</span>
                    <strong>{section_info['name']}</strong>
                    <span class="required-badge">Majburiy</span>
                    <br><small>{section_info['description']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 Ixtiyoriy Bo'limlar")
        for section_key, section_info in GRAFA_31_SECTIONS.items():
            if not section_info.get('required', False):
                st.markdown(f"""
                <div class="grafa-section">
                    <span class="section-number">{section_key.split('_')[0]}</span>
                    <strong>{section_info['name']}</strong>
                    <span class="optional-badge">Ixtiyoriy</span>
                    <br><small>{section_info['description']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Fayl yuklash
    uploaded_file = st.file_uploader(
        "JSON faylni tanlang:",
        type=['json'],
        help="Tovarlar ro'yxati bilan JSON fayl yuklang"
    )
    
    if uploaded_file is not None:
        with st.spinner("JSON fayl o'qilmoqda..."):
            data, file_type = read_uploaded_file(uploaded_file)
            
            if data is not None:
                st.markdown('<div class="success-message">✅ JSON fayl muvaffaqiyatli yuklandi!</div>', unsafe_allow_html=True)
                
                if isinstance(data, dict) and 'results' in data:
                    st.session_state.json_data = data
                    
                    # Metadata
                    if 'metadata' in data:
                        metadata = data['metadata']
                        st.markdown("### 📊 Metadata")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Jami tovarlar", metadata.get('total_items', 0))
                        with col2:
                            st.metric("Muvaffaqiyatli", metadata.get('successful_items', 0))
                        with col3:
                            st.metric("Muvaffaqiyatsiz", metadata.get('failed_items', 0))
                        with col4:
                            if 'processed_at' in metadata:
                                st.metric("Qayta ishlangan", metadata['processed_at'][:10])
                    
                    # Tovarlar ro'yxati
                    products = data['results']
                    st.info(f"📦 **{len(products)} ta tovar topildi**")
                    
                    # Birinchi 3 ta tovarni ko'rsatish
                    st.markdown("### 📋 Birinchi 3 ta Tovar (Namuna)")
                    for i in range(min(3, len(products))):
                        with st.expander(f"Tovar {i+1}: {products[i].get('наименование_товара', 'Noma\'lum')}"):
                            st.json(products[i])
                    
                    # Tahlil tugmasi
                    if st.button("🔍 31-Grafa Rasmiy Tahlil Qilish", type="primary", use_container_width=True):
                        st.session_state.current_page = 'analysis'
                        st.rerun()
                        
                else:
                    st.error("JSON fayl noto'g'ri formatda! 'results' maydoni bo'lishi kerak.")

def show_analysis_page():
    """Tahlil sahifasi"""
    st.markdown("# 🔍 31-Grafa Rasmiy Tahlil")
    st.markdown("---")
    
    if not st.session_state.json_data:
        st.warning("⚠️ Avval JSON fayl yuklang!")
        if st.button("📁 Fayl Yuklash Sahifasiga O'tish"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    products = st.session_state.json_data['results']
    
    # Tahlil jarayoni
    if not st.session_state.processed_data:
        st.markdown("### 🔄 31-Grafa Bo'yicha Rasmiy Tahlil")
        
        with st.spinner("Tovarlar 31-grafa rasmiy talablariga muvofiq tahlilanmoqda..."):
            processed_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, product in enumerate(products):
                product_info = st.session_state.processor.extract_product_basic_info(product)
                status_text.text(f"Tahlil: {idx + 1}/{len(products)} - {product_info['name'][:30]}...")
                
                result = st.session_state.processor.process_single_product(product)
                processed_results.append(result)
                
                progress_bar.progress((idx + 1) / len(products))
            
            st.session_state.processed_data = processed_results
            status_text.text("✅ Rasmiy tahlil yakunlandi!")
    
    # Natijalarni ko'rsatish
    st.markdown("### 📊 Rasmiy Tahlil Natijalari")
    
    results = st.session_state.processed_data
    
    # Ma'lumotlar strukturasini tekshirish va tuzatish
    for item in results:
        if 'completion_rates' not in item:
            old_rate = item.get('completion_rate', 0)
            item['completion_rates'] = {
                'general': old_rate,
                'required': old_rate,
                'total_sections': item.get('total_sections', 11),
                'filled_sections': item.get('filled_sections', 0),
                'required_sections': 5,
                'filled_required': int(old_rate / 20)
            }
    
    # Umumiy statistika - xavfsiz kirish
    total_products = len(results)
    avg_general = sum(item.get('completion_rates', {}).get('general', 0) for item in results) / total_products if total_products > 0 else 0
    avg_required = sum(item.get('completion_rates', {}).get('required', 0) for item in results) / total_products if total_products > 0 else 0
    full_required = sum(1 for item in results if item.get('completion_rates', {}).get('required', 0) >= 100)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jami Tovarlar", total_products)
    with col2:
        st.metric("O'rtacha Umumiy", f"{avg_general:.1f}%")
    with col3:
        st.metric("O'rtacha Majburiy", f"{avg_required:.1f}%")
    with col4:
        st.metric("To'liq Majburiy", full_required)
    
    # Vizualizatsiyalar
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = create_completion_chart(results)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = create_sections_stats_chart(results)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
    
    # Batafsil ma'lumotlar
    st.markdown("### 📋 Batafsil Tahlil")
    
    for idx, item in enumerate(results[:5]):  # Birinchi 5 ta
        completion_rates = item.get('completion_rates', {})
        general_rate = completion_rates.get('general', 0)
        required_rate = completion_rates.get('required', 0)
        
        completion_color = "🟢" if required_rate >= 100 else "🟡" if required_rate >= 80 else "🔴"
        
        product_info = item.get('product_info', {})
        product_name = product_info.get('name', 'Noma\'lum')
        
        with st.expander(f"{completion_color} {idx+1}. {product_name} (Majburiy: {required_rate:.1f}%, Umumiy: {general_rate:.1f}%)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ To'ldirilgan bo'limlar:**")
                grafa_data = item.get('grafa_data', {})
                for section_key, content in grafa_data.items():
                    section_info = GRAFA_31_SECTIONS[section_key]
                    required_badge = "⭐" if section_info.get('required', False) else ""
                    st.markdown(f"""
                    <div class="grafa-section filled-section">
                        <span class="section-number">{section_key.split('_')[0]}</span>
                        <b>{section_info['name']}</b> {required_badge}
                        <br>{str(content)[:150]}...
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**❌ Yetishmayotgan bo'limlar:**")
                missing_sections = item.get('missing_sections', {})
                
                # Majburiy yetishmayotgan bo'limlar
                if missing_sections.get('required', []):
                    st.markdown("**🔴 Majburiy:**")
                    for section_key in missing_sections['required']:
                        section_info = GRAFA_31_SECTIONS[section_key]
                        st.markdown(f"""
                        <div class="grafa-section missing-section">
                            <span class="section-number">{section_key.split('_')[0]}</span>
                            {section_info['name']}
                            <span class="required-badge">Majburiy</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Ixtiyoriy yetishmayotgan bo'limlar
                if missing_sections.get('optional', []):
                    st.markdown("**🔵 Ixtiyoriy:**")
                    for section_key in missing_sections['optional'][:3]:  # Faqat birinchi 3 ta
                        section_info = GRAFA_31_SECTIONS[section_key]
                        st.markdown(f"""
                        <div class="grafa-section missing-section">
                            <span class="section-number">{section_key.split('_')[0]}</span>
                            {section_info['name']}
                            <span class="optional-badge">Ixtiyoriy</span>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Keyingi sahifaga o'tish
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌐 Web Search", use_container_width=True):
            st.session_state.current_page = 'search'
            st.rerun()
    
    with col2:
        if st.button("📄 Rasmiy Hisobot", use_container_width=True):
            st.session_state.current_page = 'report'
            st.rerun()

def show_search_page():
    """Web Search sahifasi"""
    st.markdown("# 🌐 Web Search - Yetishmayotgan Ma'lumotlarni To'ldirish")
    st.markdown("---")
    
    if not st.session_state.processed_data:
        st.warning("⚠️ Avval tovarlarni tahlil qiling!")
        if st.button("🔍 Tahlil Sahifasiga O'tish"):
            st.session_state.current_page = 'analysis'
            st.rerun()
        return
    
    # Missing sections statistikasi
    results = st.session_state.processed_data
    
    total_missing_required = sum(len(item.get('missing_sections', {}).get('required', [])) for item in results)
    total_missing_optional = sum(len(item.get('missing_sections', {}).get('optional', [])) for item in results)
    products_with_missing_required = sum(1 for item in results if item.get('missing_sections', {}).get('required', []))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Majburiy Yetishmayotgan", total_missing_required)
    with col2:
        st.metric("Ixtiyoriy Yetishmayotgan", total_missing_optional)
    with col3:
        st.metric("Majburiy Yetishmagan Tovarlar", products_with_missing_required)
    
    if total_missing_required == 0:
        st.success("🎉 Barcha majburiy bo'limlar to'ldirilgan!")
        if total_missing_optional > 0:
            st.info(f"💡 {total_missing_optional} ta ixtiyoriy bo'lim to'ldirilishi mumkin")
    
    # Web Search tugmasi
    if st.button("🚀 Web Search Boshlash", type="primary", use_container_width=True):
        progress_container = st.container()
        progress_container.markdown('<div class="success-message">🔍 Web Search jarayoni boshlandi...</div>', unsafe_allow_html=True)
        
        filled_count = 0
        total_attempts = 0
        
        with st.spinner("Yetishmayotgan ma'lumotlar qidirilmoqda..."):
            for idx, item in enumerate(results):
                missing_sections = item.get('missing_sections', {})
                all_missing = missing_sections.get('required', []) + missing_sections.get('optional', [])
                
                if not all_missing:
                    continue
                
                product_info = item.get('product_info', {})
                product_name = product_info.get('name', 'Noma\'lum')
                progress_container.write(f"\n📦 **{idx + 1}. {product_name}**")
                
                # Avval majburiy bo'limlarni to'ldirish
                priority_missing = missing_sections.get('required', []) + missing_sections.get('optional', [])[:2]
                
                for section_key in priority_missing:
                    section_info = GRAFA_31_SECTIONS[section_key]
                    section_name = section_info['name']
                    is_required = section_info.get('required', False)
                    priority_label = "🔴 MAJBURIY" if is_required else "🔵 Ixtiyoriy"
                    
                    total_attempts += 1
                    
                    try:
                        filled_info = st.session_state.processor.fill_missing_section(
                            product_info, section_key, progress_container
                        )
                        
                        if filled_info and "ma'lumot topilmadi" not in filled_info and "xato" not in filled_info:
                            if 'grafa_data' not in item:
                                item['grafa_data'] = {}
                            item['grafa_data'][section_key] = filled_info
                            
                            # Missing sections dan olib tashlash
                            if section_key in missing_sections.get('required', []):
                                missing_sections['required'].remove(section_key)
                            elif section_key in missing_sections.get('optional', []):
                                missing_sections['optional'].remove(section_key)
                            
                            filled_count += 1
                            progress_container.write(f"  ✅ **{priority_label} {section_name}**: to'ldirildi")
                        else:
                            progress_container.write(f"  ❌ **{priority_label} {section_name}**: topilmadi")
                        
                        time.sleep(1.2)  # Rate limiting
                        
                    except Exception as e:
                        progress_container.write(f"  ⚠️ **{section_name}**: xato - {str(e)}")
                
                # Completion rate ni qayta hisoblash
                item['completion_rates'] = st.session_state.processor.calculate_completion_rate(item.get('grafa_data', {}))
                item['missing_sections'] = missing_sections
        
        success_rate = (filled_count / total_attempts) * 100 if total_attempts > 0 else 0
        st.markdown(f'<div class="success-message">🎉 Web Search yakunlandi! {filled_count}/{total_attempts} ta bo\'lim to\'ldirildi ({success_rate:.1f}%)</div>', unsafe_allow_html=True)
    
    # Keyingi sahifaga o'tish
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Tahlilni Qayta Qilish", use_container_width=True):
            st.session_state.current_page = 'analysis'
            st.rerun()
    
    with col2:
        if st.button("📄 Rasmiy Hisobot Ko'rish", use_container_width=True):
            st.session_state.current_page = 'report'
            st.rerun()

def show_report_page():
    """Rasmiy hisobot sahifasi"""
    st.markdown("# 📄 31-Grafa Rasmiy Hisobot")
    st.markdown("---")
    
    if not st.session_state.processed_data:
        st.warning("⚠️ Avval tovarlarni tahlil qiling!")
        return
    
    results = st.session_state.processed_data
    
    # Ma'lumotlar strukturasini tekshirish va tuzatish
    for item in results:
        if 'completion_rates' not in item:
            # Eski struktura uchun yangi struktura yaratish
            old_rate = item.get('completion_rate', 0)
            item['completion_rates'] = {
                'general': old_rate,
                'required': old_rate,
                'total_sections': item.get('total_sections', 11),
                'filled_sections': item.get('filled_sections', 0),
                'required_sections': 5,  # Default majburiy bo'limlar soni
                'filled_required': int(old_rate / 20)  # Taxminiy hisoblash
            }
    
    # Umumiy statistika - xavfsiz kirish
    total_products = len(results)
    avg_general = sum(item.get('completion_rates', {}).get('general', 0) for item in results) / total_products if total_products > 0 else 0
    avg_required = sum(item.get('completion_rates', {}).get('required', 0) for item in results) / total_products if total_products > 0 else 0
    
    # Header metrikalari
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jami Tovarlar", total_products)
    with col2:
        st.metric("O'rtacha Umumiy", f"{avg_general:.1f}%")
    with col3:
        st.metric("O'rtacha Majburiy", f"{avg_required:.1f}%")
    with col4:
        compliance_count = sum(1 for item in results if item.get('completion_rates', {}).get('required', 0) >= 100)
        st.metric("To'liq Muvofiq", compliance_count)
    
    # Hisobot kategoriyalari
    tab1, tab2, tab3, tab4 = st.tabs(["📋 To'liq Hisobot", "📊 Statistika", "⚖️ Muvofiqlik", "💾 Eksport"])
    
    with tab1:
        st.markdown("### 📋 Har bir Tovar uchun 31-Grafa Rasmiy Tahlili")
        
        for idx, item in enumerate(results):
            # Xavfsiz ma'lumot kirish
            completion_rates = item.get('completion_rates', {})
            general_rate = completion_rates.get('general', 0)
            required_rate = completion_rates.get('required', 0)
            
            # Muvofiqlik darajasi
            if required_rate >= 100:
                compliance_status = "🟢 TO'LIQ MUVOFIQ"
                compliance_color = "success"
            elif required_rate >= 80:
                compliance_status = "🟡 QISMAN MUVOFIQ"
                compliance_color = "warning"
            else:
                compliance_status = "🔴 NOMUVOFIQ"
                compliance_color = "error"
            
            product_info = item.get('product_info', {})
            product_name = product_info.get('name', 'Noma\'lum')
            
            with st.expander(f"{idx+1}. {product_name} - {compliance_status} (Majburiy: {required_rate:.1f}%)"):
                
                # Asosiy ma'lumotlar
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Tovar nomi:** {product_name}")
                with col2:
                    st.write(f"**Brend:** {product_info.get('brand', 'Noma\'lum')}")
                with col3:
                    st.write(f"**Model:** {product_info.get('model', 'Noma\'lum')}")
                
                # Muvofiqlik ma'lumotlari
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Majburiy Bo'limlar", f"{required_rate:.1f}%")
                with col2:
                    st.metric("Umumiy Bo'limlar", f"{general_rate:.1f}%")
                with col3:
                    st.metric("To'ldirilgan", completion_rates.get('filled_sections', 0))
                with col4:
                    st.metric("Jami", completion_rates.get('total_sections', 11))
                
                st.markdown("---")
                
                # 31-Grafa bo'limlari
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**✅ To'ldirilgan bo'limlar:**")
                    grafa_data = item.get('grafa_data', {})
                    for section_key, content in grafa_data.items():
                        section_info = GRAFA_31_SECTIONS[section_key]
                        required_badge = "⭐" if section_info.get('required', False) else "📋"
                        st.markdown(f"""
                        <div class="grafa-section filled-section">
                            <span class="section-number">{section_key.split('_')[0]}</span>
                            <b>{section_info['name']}</b> {required_badge}
                            <br><small>{str(content)}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**❌ Yetishmayotgan bo'limlar:**")
                    missing_sections = item.get('missing_sections', {})
                    
                    # Majburiy
                    if missing_sections.get('required', []):
                        st.markdown("**🔴 Majburiy (KRITIK):**")
                        for section_key in missing_sections['required']:
                            section_info = GRAFA_31_SECTIONS[section_key]
                            st.markdown(f"""
                            <div class="grafa-section missing-section">
                                <span class="section-number">{section_key.split('_')[0]}</span>
                                {section_info['name']}
                                <span class="required-badge">KRITIK</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Ixtiyoriy
                    if missing_sections.get('optional', []):
                        st.markdown("**🔵 Ixtiyoriy:**")
                        for section_key in missing_sections['optional']:
                            section_info = GRAFA_31_SECTIONS[section_key]
                            st.markdown(f"""
                            <div class="grafa-section missing-section">
                                <span class="section-number">{section_key.split('_')[0]}</span>
                                {section_info['name']}
                                <span class="optional-badge">Ixtiyoriy</span>
                            </div>
                            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📊 31-Grafa Bo'limlari Statistikasi")
        
        # Vizualizatsiyalar
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_completion_chart(results)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = create_sections_stats_chart(results)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
        
        # Bo'limlar statistikasi jadvali
        section_stats = {}
        for section_key, section_info in GRAFA_31_SECTIONS.items():
            filled_count = sum(1 for item in results if section_key in item.get('grafa_data', {}))
            section_stats[section_info['name']] = {
                'filled': filled_count,
                'missing': total_products - filled_count,
                'percentage': (filled_count / total_products) * 100,
                'required': '⭐ Majburiy' if section_info.get('required', False) else '📋 Ixtiyoriy'
            }
        
        st.markdown("### 📈 Bo'limlar bo'yicha Batafsil Jadval")
        
        stats_data = []
        for section_name, stats in section_stats.items():
            stats_data.append({
                'Bo\'lim': section_name,
                'Turi': stats['required'],
                'To\'ldirilgan': stats['filled'],
                'Yetishmayotgan': stats['missing'],
                'Foiz': f"{stats['percentage']:.1f}%"
            })
        
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True)
    
    with tab3:
        st.markdown("### ⚖️ Yo'riqnomaga Muvofiqlik Tahlili")
        
        # Muvofiqlik kategoriyalari
        compliant = [item for item in results if item.get('completion_rates', {}).get('required', 0) >= 100]
        partial = [item for item in results if 80 <= item.get('completion_rates', {}).get('required', 0) < 100]
        non_compliant = [item for item in results if item.get('completion_rates', {}).get('required', 0) < 80]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="grafa-section filled-section">
                <h4>🟢 TO'LIQ MUVOFIQ</h4>
                <p><strong>{len(compliant)} ta tovar</strong></p>
                <p>Barcha majburiy bo'limlar to'ldirilgan</p>
            </div>
            """, unsafe_allow_html=True)
            
            if compliant:
                for item in compliant[:3]:
                    name = item.get('product_info', {}).get('name', 'Noma\'lum')[:30]
                    rate = item.get('completion_rates', {}).get('required', 0)
                    st.write(f"• {name}... ({rate:.1f}%)")
        
        with col2:
            st.markdown(f"""
            <div class="grafa-section" style="background: #fef3c7; border-left-color: #D97706;">
                <h4>🟡 QISMAN MUVOFIQ</h4>
                <p><strong>{len(partial)} ta tovar</strong></p>
                <p>80-99% majburiy bo'limlar to'ldirilgan</p>
            </div>
            """, unsafe_allow_html=True)
            
            if partial:
                for item in partial[:3]:
                    name = item.get('product_info', {}).get('name', 'Noma\'lum')[:30]
                    rate = item.get('completion_rates', {}).get('required', 0)
                    st.write(f"• {name}... ({rate:.1f}%)")
        
        with col3:
            st.markdown(f"""
            <div class="grafa-section missing-section">
                <h4>🔴 NOMUVOFIQ</h4>
                <p><strong>{len(non_compliant)} ta tovar</strong></p>
                <p>80% dan kam majburiy bo'limlar</p>
            </div>
            """, unsafe_allow_html=True)
            
            if non_compliant:
                for item in non_compliant[:3]:
                    name = item.get('product_info', {}).get('name', 'Noma\'lum')[:30]
                    rate = item.get('completion_rates', {}).get('required', 0)
                    st.write(f"• {name}... ({rate:.1f}%)")
        
        # Tavsiyalar
        st.markdown("### 💡 Rasmiy Tavsiyalar")
        
        if len(non_compliant) > 0:
            st.markdown(f"""
            <div class="error-message">
                🚨 <strong>DIQQAT:</strong> {len(non_compliant)} ta tovar yo'riqnoma talablariga to'liq javob bermaydi!
                <br>Bojxona rasmiylashtirishdan oldin majburiy bo'limlarni to'ldirish talab etiladi.
            </div>
            """, unsafe_allow_html=True)
        
        if len(compliant) == total_products:
            st.markdown("""
            <div class="success-message">
                ✅ <strong>MUVAFFAQIYAT:</strong> Barcha tovarlar yo'riqnoma talablariga to'liq muvofiq!
                <br>Deklaratsiya uchun tayyor.
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 💾 Rasmiy Eksport va Yuklab Olish")
        
        # Excel eksport
        excel_buffer = export_to_excel(results)
        
        if excel_buffer:
            st.download_button(
                label="📊 Rasmiy Excel Hisobot",
                data=excel_buffer,
                file_name=f"31_grafa_rasmiy_hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        
        # JSON eksport
        export_data = {
            "report_date": datetime.now().isoformat(),
            "regulation_reference": "O'zbekiston Respublikasi Adliya vazirligi 2773-son yo'riqnomasi",
            "grafa_31_analysis": {
                "total_products": total_products,
                "average_general_completion": avg_general,
                "average_required_completion": avg_required,
                "compliance_summary": {
                    "fully_compliant": len(compliant),
                    "partially_compliant": len(partial),
                    "non_compliant": len(non_compliant)
                }
            },
            "detailed_results": results,
            "sections_mapping": GRAFA_31_SECTIONS
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 Rasmiy JSON Hisobot",
            data=json_str.encode('utf-8'),
            file_name=f"31_grafa_rasmiy_hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Yakuniy xulosalar
        st.markdown("### 📋 Rasmiy Yakuniy Xulosa")
        
        compliance_rate = (len(compliant) / total_products) * 100 if total_products > 0 else 0
        
        if compliance_rate >= 100:
            st.markdown(f"""
            <div class="success-message">
                ✅ <strong>TO'LIQ MUVOFIQLIK:</strong> Barcha tovarlar yo'riqnoma talablariga muvofiq!
                <br>📋 Deklaratsiya uchun tayyor
                <br>⚖️ Bojxona rasmiylashtirishda muammo bo'lmaydi
            </div>
            """, unsafe_allow_html=True)
        elif compliance_rate >= 80:
            st.markdown(f"""
            <div class="warning-message">
                ⚠️ <strong>QISMAN MUVOFIQLIK:</strong> {compliance_rate:.1f}% tovarlar muvofiq
                <br>🔧 {len(non_compliant) + len(partial)} ta tovarni to'ldirish kerak
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-message">
                🚨 <strong>KRITIK HOLAT:</strong> {compliance_rate:.1f}% tovarlar muvofiq
                <br>⛔ Bojxona rasmiylashtirishdan oldin majburiy tuzatishlar kerak
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        **Rasmiy tahlil xulosasi (Adliya vazirligi 2773-son yo'riqnomasiga asosan):**
        - **{total_products} ta tovar** tahlil qilindi
        - **{len(compliant)} ta tovar** to'liq muvofiq (majburiy bo'limlar 100%)
        - **{len(partial)} ta tovar** qisman muvofiq (majburiy bo'limlar 80-99%)
        - **{len(non_compliant)} ta tovar** nomuvofiq (majburiy bo'limlar 80% dan kam)
        """)

if __name__ == "__main__":
    main()

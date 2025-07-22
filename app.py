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
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from functools import lru_cache
import asyncio

warnings.filterwarnings('ignore')

# Logging konfiguratsiyasi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants va konfiguratsiya
class Config:
    """Tizim konfiguratsiyasi"""
    SERPER_API_KEYS = [
        "f73aaf81a1604fc9270c38b7b7f47b9ad9e90fca",
        "4f13f583cdbb95a1771adcd2f091ab3ec1bc49b8"
    ]
    SERPER_URL = "https://google.serper.dev/search"
    MAX_SEARCH_RESULTS = 3
    SEARCH_TIMEOUT = 10
    RATE_LIMIT_DELAY = 1.2
    MAX_CONTENT_LENGTH = 200
    MAX_PRODUCTS_TO_SHOW = 5

class ComplianceLevel(Enum):
    """Muvofiqlik darajalari"""
    FULL_COMPLIANT = "TOLIQ_MUVOFIQ"
    PARTIAL_COMPLIANT = "QISMAN_MUVOFIQ"  
    NON_COMPLIANT = "NOMUVOFIQ"

@dataclass
class CompletionRates:
    """To'ldirilish foizlari ma'lumotlari"""
    general: float = 0.0
    required: float = 0.0
    total_sections: int = 11
    filled_sections: int = 0
    required_sections: int = 5
    filled_required: int = 0

@dataclass
class ProductInfo:
    """Mahsulot asosiy ma'lumotlari"""
    name: str = ""
    brand: str = ""
    model: str = ""
    full_name: str = ""

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="31-Grafa Rasmiy Tahlil Tizimi",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling (unchanged but improved organization)
def load_css():
    """CSS stillarni yuklash"""
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
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

# Rasmiy 31-grafa bo'limlari (Optimized with validation)
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
        "critical": True,
        "min_length": 5
    },
    "2_oram_malumotlari": {
        "name": "2. O'ram ma'lumotlari (turi va miqdori)",
        "description": "Tovar o'rami turi va o'ramlar miqdori, yuk joylari soni",
        "json_fields": ["количество", "единица_измерения", "упаковка", "тип_упаковки"],
        "keywords": ["упаковка", "количество", "штук", "коробка", "тара"],
        "required": True,
        "critical": True,
        "min_length": 3
    },
    "3_konteyner_raqamlari": {
        "name": "3. Konteyner raqamlari",
        "description": "Konteynerlarda tashiladigan tovarlar uchun konteyner raqamlari",
        "json_fields": ["контейнер", "номер_контейнера", "контейнер_номер"],
        "keywords": ["контейнер", "номер"],
        "required": False,
        "critical": False,
        "min_length": 4
    },
    "4_aksiz_markalari": {
        "name": "4. Aksiz markalari",
        "description": "Aksiz markalar seriyalari, raqamlari va miqdori",
        "json_fields": ["акциз", "марка", "акцизная_марка"],
        "keywords": ["акциз", "марка"],
        "required": False,
        "critical": False,
        "min_length": 3
    },
    "5_yetkazib_berish": {
        "name": "5. Yetkazib berish muddati",
        "description": "Quvur transporti va elektr uzatish liniyalari uchun yetkazib berish muddati",
        "json_fields": ["доставка", "период", "срок_поставки"],
        "keywords": ["доставка", "период", "срок"],
        "required": False,
        "critical": False,
        "min_length": 3
    },
    "6_import_kodi": {
        "name": "6. Agregatsiyalangan import kodi",
        "description": "Tovarlarning agregatsiyalangan import kodi",
        "json_fields": ["импорт_код", "код_импорта"],
        "keywords": ["импорт", "код"],
        "required": False,
        "critical": False,
        "min_length": 3
    },
    "7_yaroqlilik_muddati": {
        "name": "7. Yaroqlilik muddati",
        "description": "Oziq-ovqat mahsulotlari va dori vositalarining yaroqlilik muddati",
        "json_fields": ["срок_годности", "дата_истечения", "срок_действия"],
        "keywords": ["срок", "годность", "истечение", "дата"],
        "required": False,
        "critical": False,
        "min_length": 5
    },
    "8_investitsiya_kodi": {
        "name": "8. Investitsiya dasturi kodi",
        "description": "Investitsiya dasturi loyihalari uchun kodlar (101, 102, 103, 201-203, 301, 000)",
        "json_fields": ["инвестиция", "проект_код", "код_проекта"],
        "keywords": ["инвестиция", "проект", "код"],
        "required": False,
        "critical": False,
        "min_length": 3
    },
    "9_soha_kodi": {
        "name": "9. Texnologik asbob-uskunalar soha kodi",
        "description": "TIF TN 8401-9033 pozitsiyalari uchun soha kodi",
        "json_fields": ["отрасль", "сфера", "код_отрасли"],
        "keywords": ["отрасль", "сфера", "оборудование"],
        "required": False,
        "critical": False,
        "min_length": 3
    },
    "10_ishlab_chiqarilgan_yili": {
        "name": "10. Ishlab chiqarilgan yili va texnik tasnifi",
        "description": "Texnologik asbob-uskunalarning ishlab chiqarilgan yili va texnik tasnifi",
        "json_fields": ["дата_изготовления", "год_производства", "техническая_классификация"],
        "keywords": ["дата", "год", "изготовления", "производства", "классификация"],
        "required": True,
        "critical": True,
        "min_length": 4
    },
    "11_davlat_xaridlari": {
        "name": "11. Davlat xaridlari kodi",
        "description": "Davlat xaridlari kodi: 01 - davlat xaridlari, 02 - davlat xaridlari emas",
        "json_fields": ["государственные_закупки", "код_закупки"],
        "keywords": ["государственные", "закупки"],
        "required": False,
        "critical": False,
        "min_length": 2
    }
}

# Optimized field mapping with validation
@lru_cache(maxsize=128)
def get_field_mapping() -> Dict[str, str]:
    """Field mapping ni cache bilan qaytarish"""
    mapping = {}
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        for field in section_info.get("json_fields", []):
            mapping[field] = section_key
    return mapping

FIELD_MAPPING = get_field_mapping()

class DataValidator:
    """Ma'lumotlarni validatsiya qilish"""
    
    @staticmethod
    def validate_json_data(data: Any) -> Tuple[bool, str]:
        """JSON ma'lumotlarini validatsiya qilish"""
        try:
            if not isinstance(data, dict):
                return False, "JSON fayl dict formatida bo'lishi kerak"
            
            if 'results' not in data:
                return False, "'results' maydoni topilmadi"
            
            if not isinstance(data['results'], list):
                return False, "'results' maydoni list bo'lishi kerak"
            
            if len(data['results']) == 0:
                return False, "Tovarlar ro'yxati bo'sh"
            
            # Birinchi tovarni tekshirish
            first_product = data['results'][0]
            if not isinstance(first_product, dict):
                return False, "Tovar ma'lumotlari dict formatida bo'lishi kerak"
            
            return True, "Validatsiya muvaffaqiyatli"
            
        except Exception as e:
            return False, f"Validatsiya xatosi: {str(e)}"
    
    @staticmethod
    def validate_product_data(product: Dict) -> Tuple[bool, List[str]]:
        """Tovar ma'lumotlarini validatsiya qilish"""
        warnings = []
        
        # Asosiy maydonlarni tekshirish
        required_fields = ["наименование_товара"]
        for field in required_fields:
            if not product.get(field) or str(product[field]).strip() == "":
                warnings.append(f"Majburiy maydon yetishmaydi: {field}")
        
        # Ma'lumotlar uzunligini tekshirish
        for field, value in product.items():
            if value and len(str(value)) > 1000:
                warnings.append(f"Juda uzun ma'lumot: {field}")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings

class EnhancedSerperAPIClient:
    """Yaxshilangan Serper API mijozi"""
    
    def __init__(self):
        self.api_keys = Config.SERPER_API_KEYS
        self.current_key_index = 0
        self.base_url = Config.SERPER_URL
        self.request_count = 0
        self.last_request_time = 0
        
    def get_next_api_key(self) -> str:
        """Keyingi API kalitini olish"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def _apply_rate_limiting(self):
        """Rate limiting qo'llash"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < Config.RATE_LIMIT_DELAY:
            sleep_time = Config.RATE_LIMIT_DELAY - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_information(self, query: str, max_results: int = None) -> Tuple[str, bool]:
        """Ma'lumotlarni qidirish (yaxshilangan)"""
        if not query or len(query.strip()) < 2:
            return "Qidiruv so'rovi juda qisqa", False
        
        max_results = max_results or Config.MAX_SEARCH_RESULTS
        self._apply_rate_limiting()
        
        headers = {
            "X-API-KEY": self.get_next_api_key(),
            "Content-Type": "application/json",
            "User-Agent": "31-Grafa-Analysis-System/1.0"
        }
        
        # Query ni optimallashtirish
        optimized_query = self._optimize_query(query)
        data = {
            "q": optimized_query, 
            "num": max_results,
            "gl": "uz",  # Uzbekistan geo
            "hl": "ru"   # Russian language for better results
        }
        
        try:
            logger.info(f"API so'rovi: {optimized_query}")
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=data, 
                timeout=Config.SEARCH_TIMEOUT
            )
            response.raise_for_status()
            results = response.json()
            
            self.request_count += 1
            
            # Natijalarni qayta ishlash
            processed_result = self._process_search_results(results)
            success = len(processed_result) > 20  # Minimal content length
            
            return processed_result, success
            
        except requests.exceptions.Timeout:
            logger.warning(f"API timeout: {query}")
            return "So'rov vaqti tugadi", False
        except requests.exceptions.RequestException as e:
            logger.error(f"API xatosi: {str(e)}")
            return f"API xatosi: {str(e)}", False
        except Exception as e:
            logger.error(f"Kutilmagan xato: {str(e)}")
            return f"Kutilmagan xato: {str(e)}", False
    
    def _optimize_query(self, query: str) -> str:
        """Qidiruv so'rovini optimallashtirish"""
        # Maxsus belgilarni tozalash
        cleaned = re.sub(r'[^\w\s\-\+]', ' ', query)
        # Ko'p bo'shliqlarni bitta bo'shliqqa almashtirish
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Qidiruv so'rovini yaxshilash
        words = cleaned.split()
        if len(words) > 8:
            # Eng muhim 6-8 ta so'zni saqlash
            cleaned = ' '.join(words[:8])
        
        return cleaned
    
    def _process_search_results(self, results: Dict) -> str:
        """Qidiruv natijalarini qayta ishlash"""
        snippets = []
        
        # Organic natijalar
        for result in results.get("organic", []):
            snippet = result.get("snippet", "")
            if snippet and len(snippet) > 30:
                # Snippet ni tozalash
                cleaned_snippet = re.sub(r'\s+', ' ', snippet.strip())
                if len(cleaned_snippet) > Config.MAX_CONTENT_LENGTH:
                    cleaned_snippet = cleaned_snippet[:Config.MAX_CONTENT_LENGTH] + "..."
                snippets.append(cleaned_snippet)
        
        # Knowledge graph ma'lumotlari
        knowledge = results.get("knowledgeGraph", {})
        if knowledge.get("description"):
            snippets.insert(0, knowledge["description"][:Config.MAX_CONTENT_LENGTH])
        
        # Answer box ma'lumotlari
        answer_box = results.get("answerBox", {})
        if answer_box.get("snippet"):
            snippets.insert(0, answer_box["snippet"][:Config.MAX_CONTENT_LENGTH])
        
        final_result = " ".join(snippets[:3]) if snippets else "Ma'lumot topilmadi"
        
        # Xavfsizlik uchun kontentni tozalash
        final_result = re.sub(r'[^\w\s\-\+\.,;:()%°/]', '', final_result)
        
        return final_result

class AdvancedGrafa31Processor:
    """Yaxshilangan 31-Grafa protsessor"""
    
    def __init__(self):
        self.api_client = EnhancedSerperAPIClient()
        self.validator = DataValidator()
        self.processing_stats = {
            'processed_count': 0,
            'error_count': 0,
            'search_requests': 0,
            'successful_searches': 0
        }
    
    def extract_product_basic_info(self, product: Dict) -> ProductInfo:
        """Mahsulotning asosiy ma'lumotlarini ajratish (optimized)"""
        name = self._clean_text(product.get('наименование_товара', ''))
        brand = self._clean_text(product.get('название_бренда', 
                                           product.get('товарный_знак', '')))
        model = self._clean_text(product.get('модель', ''))
        
        # Full name ni aqlli tarzda yaratish
        parts = [part for part in [name, brand, model] if part]
        full_name = ' '.join(parts[:3])  # Maksimal 3 ta qism
        
        return ProductInfo(
            name=name,
            brand=brand,
            model=model,
            full_name=full_name
        )
    
    def _clean_text(self, text: Any) -> str:
        """Matnni tozalash"""
        if not text:
            return ""
        
        text_str = str(text).strip()
        
        # Maxsus holatlar
        if text_str.lower() in ['', 'not specified', 'не указано', 'не указан', 'null', 'none']:
            return ""
        
        # Matn uzunligini cheklash
        if len(text_str) > 200:
            text_str = text_str[:200] + "..."
        
        return text_str
    
    def map_fields_to_grafa31(self, product: Dict) -> Dict[str, str]:
        """JSON maydonlarini 31-grafa bo'limlariga moslashtirish (optimized)"""
        grafa_data = {}
        
        for field_name, value in product.items():
            cleaned_value = self._clean_text(value)
            if not cleaned_value:
                continue
            
            # Field mapping
            if field_name in FIELD_MAPPING:
                grafa_section = FIELD_MAPPING[field_name]
                
                # Quality validation
                section_info = GRAFA_31_SECTIONS[grafa_section]
                min_length = section_info.get('min_length', 1)
                
                if len(cleaned_value) >= min_length:
                    if grafa_section not in grafa_data:
                        grafa_data[grafa_section] = []
                    grafa_data[grafa_section].append(cleaned_value)
        
        # Combine values for each section
        for section_key in grafa_data:
            unique_values = list(dict.fromkeys(grafa_data[section_key]))  # Remove duplicates
            grafa_data[section_key] = "; ".join(unique_values)
            
        return grafa_data
    
    def find_missing_sections(self, grafa_data: Dict) -> Dict[str, List[str]]:
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
    
    def calculate_completion_rate(self, grafa_data: Dict) -> CompletionRates:
        """To'ldirilish foizini hisoblash (optimized)"""
        total_sections = len(GRAFA_31_SECTIONS)
        filled_sections = len(grafa_data)
        
        required_sections = [k for k, v in GRAFA_31_SECTIONS.items() if v.get('required', False)]
        filled_required = sum(1 for section in required_sections if section in grafa_data)
        
        # Calculations with safety checks
        general_completion = (filled_sections / total_sections * 100) if total_sections > 0 else 0
        required_completion = (filled_required / len(required_sections) * 100) if required_sections else 100
        
        return CompletionRates(
            general=general_completion,
            required=required_completion,
            total_sections=total_sections,
            filled_sections=filled_sections,
            required_sections=len(required_sections),
            filled_required=filled_required
        )
    
    def get_compliance_level(self, completion_rates: CompletionRates) -> ComplianceLevel:
        """Muvofiqlik darajasini aniqlash"""
        if completion_rates.required >= 100:
            return ComplianceLevel.FULL_COMPLIANT
        elif completion_rates.required >= 80:
            return ComplianceLevel.PARTIAL_COMPLIANT
        else:
            return ComplianceLevel.NON_COMPLIANT
    
    def create_smart_search_query(self, product_info: ProductInfo, section_key: str) -> str:
        """Aqlli qidiruv so'rovini yaratish"""
        section_info = GRAFA_31_SECTIONS[section_key]
        keywords = section_info.get('keywords', [])
        
        # Base query components
        query_parts = []
        
        if product_info.name:
            query_parts.append(product_info.name[:50])  # Limit length
        
        if product_info.brand and product_info.brand != product_info.name:
            query_parts.append(product_info.brand[:30])
        
        # Add relevant keywords based on product type and section
        if keywords:
            # Choose most relevant keywords
            relevant_keywords = keywords[:2]  # Top 2 keywords
            query_parts.extend(relevant_keywords)
        
        query = ' '.join(query_parts)
        
        # Final optimization
        return self.api_client._optimize_query(query)
    
    def should_skip_section_search(self, product_info: ProductInfo, section_key: str) -> bool:
        """Ma'lum bo'limlarni qidirishni o'tkazib yuborish kerakligini aniqlash"""
        product_name = product_info.name.lower()
        
        # Aksiz markalari faqat tegishli mahsulotlar uchun
        if section_key == "4_aksiz_markalari":
            # Aksiz markalari kerak bo'lgan mahsulotlar ro'yxati
            excise_products = [
                'алкоголь', 'водка', 'вино', 'пиво', 'коньяк', 'виски', 'ликер',
                'сигарет', 'табак', 'папирос', 'сигар',
                'бензин', 'дизель', 'керосин', 'мазут', 'топливо',
                'драгоценн', 'золот', 'серебр', 'платин', 'бриллиант'
            ]
            
            # Avtomobillarda aksiz markalari yo'q
            auto_keywords = ['автомобиль', 'машин', 'авто', 'car', 'vehicle', 'легков']
            if any(keyword in product_name for keyword in auto_keywords):
                return True  # Skip search for cars
            
            # Agar mahsulot aksiz mahsulotlari ro'yxatida bo'lmasa, o'tkazib yuborish
            if not any(keyword in product_name for keyword in excise_products):
                return True
        
        # Konteyner raqamlari faqat konteynerda tashiladigan tovarlar uchun
        if section_key == "3_konteyner_raqamlari":
            # Odatda konteynerda tashilmaydigan mahsulotlar
            non_container_products = [
                'газ', 'нефть', 'электроэнерг', 'услуг', 'работ'
            ]
            
            if any(keyword in product_name for keyword in non_container_products):
                return True
            
            # Kichik mahsulotlar odatda alohida konteynerda tashilmaydi
            small_items = ['ручк', 'карандаш', 'бумаг', 'канцтовар']
            if any(keyword in product_name for keyword in small_items):
                return True
        
        # Yetkazib berish muddati faqat maxsus tovarlar uchun
        if section_key == "5_yetkazib_berish":
            # Quvur transporti va elektr uzatish liniyalari
            pipeline_products = ['газ', 'нефть', 'электроэнерг', 'трубопровод']
            if not any(keyword in product_name for keyword in pipeline_products):
                return True
        
        # Investitsiya kodi faqat investitsiya loyihalari uchun
        if section_key == "8_investitsiya_kodi":
            investment_keywords = ['оборудован', 'станок', 'машин', 'завод', 'техник', 'промышлен']
            if not any(keyword in product_name for keyword in investment_keywords):
                return True
        
        # Soha kodi faqat texnologik asbob-uskunalar uchun
        if section_key == "9_soha_kodi":
            tech_keywords = ['оборудован', 'станок', 'машин', 'аппарат', 'устройств', 'прибор']
            if not any(keyword in product_name for keyword in tech_keywords):
                return True
        
        return False  # Continue with search
    
    def fill_missing_section(self, product_info: ProductInfo, section_key: str, 
                           progress_container=None) -> Tuple[str, bool]:
        """Yetishmayotgan bo'limni to'ldirish (enhanced)"""
        
        # Birinchi navbatda qidirishni o'tkazib yuborish kerakligini tekshirish
        if self.should_skip_section_search(product_info, section_key):
            section_info = GRAFA_31_SECTIONS[section_key]
            section_name = section_info['name']
            
            # Sabab asosida xabar berish
            if section_key == "4_aksiz_markalari":
                if any(keyword in product_info.name.lower() for keyword in ['автомобиль', 'машин', 'авто', 'car', 'vehicle', 'легков']):
                    reason = "Avtomobillarga aksiz markalari talab etilmaydi"
                else:
                    reason = "Bu tovar turi uchun aksiz markalari talab etilmaydi"
            elif section_key == "3_konteyner_raqamlari":
                reason = "Bu tovar turi odatda alohida konteynerda tashilmaydi"
            elif section_key == "5_yetkazib_berish":
                reason = "Bu bo'lim faqat quvur transporti va elektr uzatish uchun"
            elif section_key == "8_investitsiya_kodi":
                reason = "Bu tovar investitsiya loyihasi hisoblanmaydi"
            elif section_key == "9_soha_kodi":
                reason = "Bu bo'lim faqat texnologik asbob-uskunalar uchun"
            else:
                reason = "Bu tovar turi uchun tegishli emas"
            
            if progress_container:
                progress_container.write(f"⏭️ **{section_name}**: {reason}")
            
            return f"Bu tovar turi uchun tegishli emas: {reason}", False
        
        query = self.create_smart_search_query(product_info, section_key)
        
        if progress_container:
            progress_container.write(f"🔍 Qidirilmoqda: {query[:80]}...")
        
        self.processing_stats['search_requests'] += 1
        
        try:
            result, success = self.api_client.search_information(query)
            
            if success:
                self.processing_stats['successful_searches'] += 1
                if progress_container:
                    progress_container.write(f"✅ Topildi: {result[:100]}...")
                return result, True
            else:
                section_name = GRAFA_31_SECTIONS[section_key]['name']
                if progress_container:
                    progress_container.write(f"❌ Topilmadi: {section_name}")
                return "Ma'lumot topilmadi", False
                
        except Exception as e:
            logger.error(f"Search error for {section_key}: {str(e)}")
            if progress_container:
                progress_container.write(f"⚠️ Xato: {str(e)}")
            return f"Xato: {str(e)}", False
    
    def process_single_product(self, product: Dict) -> Dict:
        """Bitta mahsulotni qayta ishlash (enhanced with error handling)"""
        try:
            self.processing_stats['processed_count'] += 1
            
            # Validation
            is_valid, warnings = self.validator.validate_product_data(product)
            
            # Extract info
            product_info = self.extract_product_basic_info(product)
            grafa_data = self.map_fields_to_grafa31(product)
            missing_sections = self.find_missing_sections(grafa_data)
            completion_rates = self.calculate_completion_rate(grafa_data)
            compliance_level = self.get_compliance_level(completion_rates)
            
            return {
                'original_product': product,
                'product_info': product_info,
                'grafa_data': grafa_data,
                'missing_sections': missing_sections,
                'completion_rates': completion_rates,
                'compliance_level': compliance_level,
                'is_valid': is_valid,
                'validation_warnings': warnings,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.processing_stats['error_count'] += 1
            logger.error(f"Error processing product: {str(e)}")
            
            # Return safe default
            return {
                'original_product': product,
                'product_info': ProductInfo(name='Xato', brand='', model='', full_name='Xato'),
                'grafa_data': {},
                'missing_sections': {'required': [], 'optional': [], 'all': []},
                'completion_rates': CompletionRates(),
                'compliance_level': ComplianceLevel.NON_COMPLIANT,
                'is_valid': False,
                'validation_warnings': [f"Processing error: {str(e)}"],
                'processed_at': datetime.now().isoformat()
            }
    
    def get_processing_stats(self) -> Dict:
        """Jarayon statistikasini olish"""
        return {
            **self.processing_stats,
            'success_rate': (self.processing_stats['processed_count'] - self.processing_stats['error_count']) / 
                          max(self.processing_stats['processed_count'], 1) * 100,
            'search_success_rate': self.processing_stats['successful_searches'] / 
                                 max(self.processing_stats['search_requests'], 1) * 100
        }

def read_uploaded_file(uploaded_file) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
    """Yuklangan faylni o'qish (enhanced)"""
    try:
        if not uploaded_file:
            return None, None, "Fayl tanlanmagan"
        
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension != 'json':
            return None, None, f"Noto'g'ri fayl turi. JSON fayl kutilmoqda, {file_extension} berildi"
        
        # File size check
        file_size = uploaded_file.size
        max_size = 50 * 1024 * 1024  # 50MB
        
        if file_size > max_size:
            return None, None, f"Fayl hajmi juda katta ({file_size/1024/1024:.1f}MB). Maksimal: 50MB"
        
        # Read and validate JSON
        try:
            json_data = json.load(uploaded_file)
        except json.JSONDecodeError as e:
            return None, None, f"JSON format xatosi: {str(e)}"
        
        # Validate data structure
        validator = DataValidator()
        is_valid, message = validator.validate_json_data(json_data)
        
        if not is_valid:
            return None, None, f"Ma'lumotlar strukturasi xatosi: {message}"
        
        logger.info(f"Fayl muvaffaqiyatli yuklandi: {uploaded_file.name} ({file_size} bytes)")
        return json_data, 'json', None
        
    except Exception as e:
        error_msg = f"Faylni o'qishda kutilmagan xato: {str(e)}"
        logger.error(error_msg)
        return None, None, error_msg

# Visualization functions (enhanced)
def create_enhanced_completion_chart(processed_data: List[Dict]) -> Optional[go.Figure]:
    """Yaxshilangan to'ldirilish diagrammasi"""
    if not processed_data:
        return None
    
    try:
        # Extract data safely
        general_rates = []
        required_rates = []
        product_names = []
        compliance_colors = []
        
        for item in processed_data:
            completion_rates = item.get('completion_rates')
            if isinstance(completion_rates, CompletionRates):
                general_rates.append(completion_rates.general)
                required_rates.append(completion_rates.required)
            else:
                # Fallback for old format
                rates = item.get('completion_rates', {})
                general_rates.append(rates.get('general', 0))
                required_rates.append(rates.get('required', 0))
            
            # Product name formatting
            product_info = item.get('product_info')
            if isinstance(product_info, ProductInfo):
                name = product_info.name
            else:
                name = item.get('product_info', {}).get('name', 'Noma\'lum')
            
            # Truncate long names
            if len(name) > 25:
                name = name[:25] + '...'
            product_names.append(name)
            
            # Color based on compliance
            compliance = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
            if compliance == ComplianceLevel.FULL_COMPLIANT:
                compliance_colors.append('#059669')
            elif compliance == ComplianceLevel.PARTIAL_COMPLIANT:
                compliance_colors.append('#D97706')
            else:
                compliance_colors.append('#DC2626')
        
        fig = go.Figure()
        
        # General completion bars
        fig.add_trace(go.Bar(
            name='Umumiy To\'ldirilish',
            x=product_names,
            y=general_rates,
            marker_color='lightblue',
            opacity=0.7,
            text=[f"{rate:.1f}%" for rate in general_rates],
            textposition='outside'
        ))
        
        # Required completion bars
        fig.add_trace(go.Bar(
            name='Majburiy Bo\'limlar',
            x=product_names,
            y=required_rates,
            marker_color=compliance_colors,
            text=[f"{rate:.1f}%" for rate in required_rates],
            textposition='outside'
        ))
        
        # Layout optimization
        fig.update_layout(
            title={
                'text': '31-Grafa To\'ldirilish Foizi va Muvofiqlik Darajasi',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Tovarlar',
            yaxis_title='To\'ldirilish Foizi (%)',
            barmode='group',
            xaxis_tickangle=-45,
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(range=[0, 105])
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Chart creation error: {str(e)}")
        return None

def create_sections_stats_chart(processed_data: List[Dict]) -> Optional[go.Figure]:
    """Bo'limlar statistikasi diagrammasi (enhanced)"""
    if not processed_data:
        return None
    
    try:
        section_stats = {}
        total_products = len(processed_data)
        
        for section_key, section_info in GRAFA_31_SECTIONS.items():
            filled_count = sum(1 for item in processed_data 
                             if section_key in item.get('grafa_data', {}))
            
            section_name = section_info['name'][:40]  # Truncate long names
            if len(section_info['name']) > 40:
                section_name += '...'
            
            section_stats[section_name] = {
                'filled': filled_count,
                'percentage': (filled_count / total_products) * 100,
                'required': section_info.get('required', False),
                'section_key': section_key
            }
        
        section_names = list(section_stats.keys())
        percentages = [section_stats[name]['percentage'] for name in section_names]
        colors = ['#DC2626' if section_stats[name]['required'] else '#1E3A8A' 
                 for name in section_names]
        
        # Custom hover text
        hover_texts = []
        for name in section_names:
            stats = section_stats[name]
            hover_text = f"{name}<br>To'ldirilgan: {stats['filled']}<br>Foiz: {stats['percentage']:.1f}%<br>Turi: {'Majburiy' if stats['required'] else 'Ixtiyoriy'}"
            hover_texts.append(hover_text)
        
        fig = go.Figure(data=[
            go.Bar(
                x=section_names,
                y=percentages,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='outside',
                hovertext=hover_texts,
                hoverinfo='text'
            )
        ])
        
        fig.update_layout(
            title={
                'text': '31-Grafa Bo\'limlari To\'ldirilish Statistikasi',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Bo\'limlar',
            yaxis_title='To\'ldirilish Foizi (%)',
            xaxis_tickangle=-45,
            height=700,
            showlegend=False,
            yaxis=dict(range=[0, 105])
        )
        
        # Add annotations for required vs optional
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text='🔴 Majburiy bo\'limlar | 🔵 Ixtiyoriy bo\'limlar',
            showarrow=False,
            font=dict(size=12),
            bgcolor='white',
            bordercolor='gray',
            borderwidth=1
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Sections chart error: {str(e)}")
        return None

def export_to_enhanced_excel(processed_data: List[Dict]) -> Optional[io.BytesIO]:
    """Enhanced Excel eksport"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1E3A8A',
                'font_color': 'white',
                'border': 1
            })
            
            compliant_format = workbook.add_format({
                'bg_color': '#ecfdf5',
                'border': 1
            })
            
            partial_format = workbook.add_format({
                'bg_color': '#fef3c7',
                'border': 1
            })
            
            non_compliant_format = workbook.add_format({
                'bg_color': '#fef2f2',
                'border': 1
            })
            
            # Main data
            export_data = []
            
            for idx, item in enumerate(processed_data):
                product_info = item.get('product_info')
                completion_rates = item.get('completion_rates')
                compliance_level = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
                
                # Handle different data types
                if isinstance(product_info, ProductInfo):
                    name = product_info.name
                    brand = product_info.brand
                    model = product_info.model
                else:
                    info_dict = item.get('product_info', {})
                    name = info_dict.get('name', '')
                    brand = info_dict.get('brand', '')
                    model = info_dict.get('model', '')
                
                if isinstance(completion_rates, CompletionRates):
                    general = completion_rates.general
                    required = completion_rates.required
                    filled = completion_rates.filled_sections
                    total = completion_rates.total_sections
                else:
                    rates_dict = item.get('completion_rates', {})
                    general = rates_dict.get('general', 0)
                    required = rates_dict.get('required', 0)
                    filled = rates_dict.get('filled_sections', 0)
                    total = rates_dict.get('total_sections', 11)
                
                row = {
                    'ID': idx + 1,
                    'Tovar_Nomi': name,
                    'Brend': brand,
                    'Model': model,
                    'Muvofiqlik_Darajasi': compliance_level.value if hasattr(compliance_level, 'value') else str(compliance_level),
                    'Umumiy_Toldirilish_%': f"{general:.1f}%",
                    'Majburiy_Toldirilish_%': f"{required:.1f}%",
                    'Toldirilgan_Bolimlar': filled,
                    'Jami_Bolimlar': total,
                    'Validatsiya': 'Muvofiq' if item.get('is_valid', True) else 'Xato',
                    'Qayta_Ishlangan_Vaqt': item.get('processed_at', '')
                }
                
                # Add 31-Grafa sections
                grafa_data = item.get('grafa_data', {})
                for section_key, section_info in GRAFA_31_SECTIONS.items():
                    column_name = f"Grafa_{section_key.split('_')[0]}_{section_info['name'][:30]}"
                    row[column_name] = grafa_data.get(section_key, '')
                
                export_data.append(row)
            
            # Create DataFrame and export
            df = pd.DataFrame(export_data)
            df.to_excel(writer, sheet_name='31-Grafa Rasmiy Tahlil', index=False)
            
            # Format worksheet
            worksheet = writer.sheets['31-Grafa Rasmiy Tahlil']
            
            # Apply header formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Apply conditional formatting for compliance
            for row_num in range(1, len(df) + 1):
                compliance = df.iloc[row_num - 1]['Muvofiqlik_Darajasi']
                
                if 'TOLIQ' in str(compliance):
                    format_to_use = compliant_format
                elif 'QISMAN' in str(compliance):
                    format_to_use = partial_format
                else:
                    format_to_use = non_compliant_format
                
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num], format_to_use)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                )
                worksheet.set_column(i, i, min(max_len + 2, 50))
            
            # Add summary sheet
            summary_data = create_summary_data(processed_data)
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Xulosa', index=False)
            
            # Format summary sheet
            summary_worksheet = writer.sheets['Xulosa']
            for col_num, value in enumerate(summary_df.columns.values):
                summary_worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        logger.info("Excel eksport muvaffaqiyatli yakunlandi")
        return output
    
    except Exception as e:
        logger.error(f"Excel eksport xatosi: {str(e)}")
        st.error(f"Excel eksport xatosi: {str(e)}")
        return None

def create_summary_data(processed_data: List[Dict]) -> List[Dict]:
    """Xulosa ma'lumotlarini yaratish"""
    total_products = len(processed_data)
    
    compliant_count = sum(1 for item in processed_data 
                         if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    partial_count = sum(1 for item in processed_data 
                       if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT)
    non_compliant_count = total_products - compliant_count - partial_count
    
    return [
        {'Metrika': 'Jami Tovarlar', 'Qiymat': total_products},
        {'Metrika': 'To\'liq Muvofiq', 'Qiymat': compliant_count},
        {'Metrika': 'Qisman Muvofiq', 'Qiymat': partial_count},
        {'Metrika': 'Nomuvofiq', 'Qiymat': non_compliant_count},
        {'Metrika': 'Muvofiqlik Foizi', 'Qiymat': f"{(compliant_count/total_products*100):.1f}%"},
        {'Metrika': 'Tahlil Sanasi', 'Qiymat': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ]

# Initialize session state
def initialize_session_state():
    """Session state ni boshlash"""
    defaults = {
        'current_page': 'upload',
        'json_data': None,
        'processed_data': [],
        'processor': None,
        'processing_complete': False,
        'last_upload_time': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def main():
    """Asosiy funksiya"""
    # CSS yuklash
    load_css()
    
    # Session state ni boshlash
    initialize_session_state()
    
    # Processor ni lazy initialize qilish
    if st.session_state.processor is None:
        st.session_state.processor = AdvancedGrafa31Processor()

    # Header
    header_col1, header_col2, header_col3 = st.columns([1, 2, 1])
    
    with header_col2:
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
    
    # System info in sidebar
    show_sidebar_info()
    
    # Main page routing
    if st.session_state.current_page == 'upload':
        show_enhanced_upload_page()
    elif st.session_state.current_page == 'analysis':
        show_enhanced_analysis_page()
    elif st.session_state.current_page == 'search':
        show_enhanced_search_page()
    elif st.session_state.current_page == 'report':
        show_enhanced_report_page()

def show_sidebar_info():
    """Sidebar ma'lumotlari"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📋 31-Grafa Bo'limlari")
    
    required_count = sum(1 for v in GRAFA_31_SECTIONS.values() if v.get('required', False))
    optional_count = len(GRAFA_31_SECTIONS) - required_count
    
    sidebar_col1, sidebar_col2 = st.sidebar.columns(2)
    with sidebar_col1:
        st.metric("Majburiy", required_count)
    with sidebar_col2:
        st.metric("Ixtiyoriy", optional_count)
    
    st.sidebar.metric("Jami bo'limlar", len(GRAFA_31_SECTIONS))
    
    # Current status
    if st.session_state.json_data:
        if 'results' in st.session_state.json_data:
            total_products = len(st.session_state.json_data['results'])
            st.sidebar.metric("Yuklangan tovarlar", total_products)
        if st.session_state.processed_data:
            processed_count = len(st.session_state.processed_data)
            st.sidebar.metric("Tahlil qilingan", processed_count)
            
            # Processing stats
            if st.session_state.processor:
                stats = st.session_state.processor.get_processing_stats()
                if stats['search_requests'] > 0:
                    st.sidebar.metric("Search requests", stats['search_requests'])
                    st.sidebar.metric("Success rate", f"{stats['search_success_rate']:.1f}%")
    else:
        st.sidebar.info("JSON fayl yuklanmagan")
    
    # Clear data button
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Ma'lumotlarni Tozalash", 
                        help="Barcha yuklangan ma'lumotlarni tozalash"):
        clear_session_data()
        st.rerun()

def clear_session_data():
    """Session ma'lumotlarini tozalash"""
    st.session_state.json_data = None
    st.session_state.processed_data = []
    st.session_state.processing_complete = False
    st.session_state.current_page = 'upload'
    st.session_state.processor = None

def show_enhanced_upload_page():
    """Yaxshilangan yuklash sahifasi"""
    st.markdown("# 📁 JSON Fayl Yuklash")
    st.markdown("---")
    
    # System info
    st.markdown("""
    ### 📖 31-Grafa Rasmiy Tahlil Tizimi
    
    Bu tizim **O'zbekiston Respublikasi Adliya vazirligining 2773-son yo'riqnomasining 31-grafasi** 
    bo'yicha tovar ma'lumotlarini rasmiy talablarga muvofiq tahlil qiladi.
    
    **31-Grafa: "Yuk joylari va tovar tavsifi"** - "Markirovka va miqdor — konteynerlar raqami — tovar tavsifi"
    """)
    
    # Requirements display
    upload_col1, upload_col2 = st.columns(2)
    
    with upload_col1:
        st.markdown("### ⭐ Majburiy Bo'limlar")
        required_sections = [(k, v) for k, v in GRAFA_31_SECTIONS.items() if v.get('required', False)]
        
        for section_key, section_info in required_sections:
            st.markdown(f"""
            <div class="grafa-section">
                <span class="section-number">{section_key.split('_')[0]}</span>
                <strong>{section_info['name'][:50]}{'...' if len(section_info['name']) > 50 else ''}</strong>
                <span class="required-badge">Majburiy</span>
                <br><small>{section_info['description'][:80]}{'...' if len(section_info['description']) > 80 else ''}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with upload_col2:
        st.markdown("### 📋 Ixtiyoriy Bo'limlar")
        optional_sections = [(k, v) for k, v in GRAFA_31_SECTIONS.items() if not v.get('required', False)]
        
        for section_key, section_info in optional_sections:
            st.markdown(f"""
            <div class="grafa-section">
                <span class="section-number">{section_key.split('_')[0]}</span>
                <strong>{section_info['name'][:50]}{'...' if len(section_info['name']) > 50 else ''}</strong>
                <span class="optional-badge">Ixtiyoriy</span>
                <br><small>{section_info['description'][:80]}{'...' if len(section_info['description']) > 80 else ''}</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # File upload with enhanced validation
    uploaded_file = st.file_uploader(
        "JSON faylni tanlang:",
        type=['json'],
        help="Tovarlar ro'yxati bilan JSON fayl yuklang (Maksimal hajm: 50MB)"
    )
    
    if uploaded_file is not None:
        with st.spinner("JSON fayl tahlil qilinmoqda..."):
            data, file_type, error_message = read_uploaded_file(uploaded_file)
            
            if error_message:
                st.error(f"❌ Fayl yuklash xatosi: {error_message}")
                return
            
            if data is not None:
                st.markdown('<div class="success-message">✅ JSON fayl muvaffaqiyatli yuklandi va validatsiya qilindi!</div>', 
                           unsafe_allow_html=True)
                
                # Store data
                st.session_state.json_data = data
                st.session_state.last_upload_time = datetime.now()
                
                # Display metadata
                if 'metadata' in data:
                    display_metadata(data['metadata'])
                
                # Display products info
                products = data['results']
                display_products_preview(products)
                
                # Analysis button
                upload_btn_col1, upload_btn_col2, upload_btn_col3 = st.columns([1, 2, 1])
                with upload_btn_col2:
                    if st.button("🔍 31-Grafa Rasmiy Tahlil Qilish", 
                               type="primary", use_container_width=True):
                        st.session_state.current_page = 'analysis'
                        st.rerun()

def display_metadata(metadata):
    """Metadata ni ko'rsatish"""
    st.markdown("### 📊 Fayl Ma'lumotlari")
    
    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
    
    with meta_col1:
        st.metric("Jami tovarlar", metadata.get('total_items', 0))
    with meta_col2:
        st.metric("Muvaffaqiyatli", metadata.get('successful_items', 0))
    with meta_col3:
        st.metric("Muvaffaqiyatsiz", metadata.get('failed_items', 0))
    with meta_col4:
        if 'processed_at' in metadata:
            processed_date = metadata['processed_at'][:10]
            st.metric("Sana", processed_date)

def display_products_preview(products):
    """Tovarlar namunasini ko'rsatish"""
    st.info(f"📦 **{len(products)} ta tovar topildi**")
    
    if len(products) > 0:
        st.markdown("### 📋 Tovarlar Namunasi (Birinchi 3 ta)")
        
        preview_count = min(3, len(products))
        
        for i in range(preview_count):
            product = products[i]
            product_name = product.get('наименование_товара', f'Tovar {i+1}')
            
            # Validate product
            validator = DataValidator()
            is_valid, warnings = validator.validate_product_data(product)
            
            status_icon = "✅" if is_valid else "⚠️"
            
            with st.expander(f"{status_icon} {i+1}. {product_name}"):
                if not is_valid and warnings:
                    st.warning("⚠️ Validatsiya ogohlantirishlari:")
                    for warning in warnings:
                        st.write(f"• {warning}")
                
                # Display key fields
                preview_col1, preview_col2 = st.columns(2)
                
                with preview_col1:
                    st.write("**Asosiy ma'lumotlar:**")
                    for field in ['наименование_товара', 'название_бренда', 'модель', 'количество']:
                        value = product.get(field, 'Mavjud emas')
                        st.write(f"• **{field}**: {value}")
                
                with preview_col2:
                    st.write("**JSON strukturasi:**")
                    # Show structure without displaying all data
                    field_count = len(product)
                    non_empty_fields = sum(1 for v in product.values() if v)
                    st.write(f"• Jami maydonlar: {field_count}")
                    st.write(f"• To'ldirilgan maydonlar: {non_empty_fields}")
                    st.write(f"• To'ldirilish foizi: {(non_empty_fields/field_count*100):.1f}%")
                
                # Show JSON preview (limited)
                if st.checkbox(f"JSON ma'lumotlarini ko'rsatish {i+1}", key=f"show_json_{i}"):
                    st.json(product)

def show_enhanced_analysis_page():
    """Yaxshilangan tahlil sahifasi"""
    st.markdown("# 🔍 31-Grafa Rasmiy Tahlil")
    st.markdown("---")
    
    if not st.session_state.json_data:
        show_no_data_warning('upload')
        return
    
    products = st.session_state.json_data['results']
    
    # Analysis process
    if not st.session_state.processed_data:
        perform_analysis(products)
    
    # Display results
    display_analysis_results()
    
    # Navigation buttons
    show_analysis_navigation()

def perform_analysis(products):
    """Tahlil jarayonini amalga oshirish"""
    st.markdown("### 🔄 31-Grafa Bo'yicha Rasmiy Tahlil")
    st.info(f"📊 {len(products)} ta tovar rasmiy talablarga muvofiq tahlilanmoqda...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Analysis metrics
    metrics_container = st.container()
    
    with st.spinner("Tahlil jarayoni..."):
        processed_results = []
        
        for idx, product in enumerate(products):
            # Extract basic info for display
            product_name = product.get('наименование_товара', f'Tovar {idx+1}')
            display_name = product_name[:40] + '...' if len(product_name) > 40 else product_name
            
            status_text.text(f"Tahlil: {idx + 1}/{len(products)} - {display_name}")
            
            # Process product
            result = st.session_state.processor.process_single_product(product)
            processed_results.append(result)
            
            # Update progress
            progress_bar.progress((idx + 1) / len(products))
            
            # Show intermediate stats every 10 products
            if (idx + 1) % 10 == 0 or idx == len(products) - 1:
                show_intermediate_stats(processed_results, metrics_container)
        
        st.session_state.processed_data = processed_results
        st.session_state.processing_complete = True
        
        # Final stats
        final_stats = st.session_state.processor.get_processing_stats()
        
        status_text.success(f"✅ Rasmiy tahlil yakunlandi! "
                          f"Muvaffaqiyat darajasi: {final_stats['success_rate']:.1f}%")

def show_intermediate_stats(results, container):
    """Oraliq statistikani ko'rsatish"""
    if not results:
        return
    
    total = len(results)
    compliant = sum(1 for r in results if r.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    partial = sum(1 for r in results if r.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT)
    
    with container:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Qayta ishlangan", total)
        with col2:
            st.metric("To'liq muvofiq", compliant)
        with col3:
            st.metric("Qisman muvofiq", partial)

def display_analysis_results():
    """Tahlil natijalarini ko'rsatish"""
    results = st.session_state.processed_data
    
    if not results:
        st.warning("Tahlil natijalari topilmadi.")
        return
    
    st.markdown("### 📊 Rasmiy Tahlil Natijalari")
    
    # Overall statistics
    display_overall_statistics(results)
    
    # Visualizations
    display_analysis_charts(results)
    
    # Detailed results
    display_detailed_results(results)

def display_overall_statistics(results):
    """Umumiy statistikani ko'rsatish"""
    total_products = len(results)
    
    # Safe calculation of averages
    completion_rates_list = []
    for item in results:
        rates = item.get('completion_rates')
        if isinstance(rates, CompletionRates):
            completion_rates_list.append({
                'general': rates.general,
                'required': rates.required
            })
        else:
            # Fallback for dict format
            rates_dict = item.get('completion_rates', {})
            completion_rates_list.append({
                'general': rates_dict.get('general', 0),
                'required': rates_dict.get('required', 0)
            })
    
    avg_general = sum(r['general'] for r in completion_rates_list) / total_products if total_products > 0 else 0
    avg_required = sum(r['required'] for r in completion_rates_list) / total_products if total_products > 0 else 0
    
    # Compliance counts
    full_compliant = sum(1 for item in results 
                        if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    partial_compliant = sum(1 for item in results 
                          if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT)
    non_compliant = total_products - full_compliant - partial_compliant
    
    # Display metrics
    stats_col1, stats_col2, stats_col3, stats_col4, stats_col5 = st.columns(5)
    
    with stats_col1:
        st.metric("Jami Tovarlar", total_products)
    with stats_col2:
        st.metric("O'rtacha Umumiy", f"{avg_general:.1f}%", 
                 delta=f"{avg_general - 75:.1f}%" if avg_general != 75 else None)
    with stats_col3:
        st.metric("O'rtacha Majburiy", f"{avg_required:.1f}%",
                 delta=f"{avg_required - 80:.1f}%" if avg_required != 80 else None)
    with stats_col4:
        st.metric("To'liq Muvofiq", full_compliant,
                 delta=f"{(full_compliant/total_products*100):.1f}%")
    with stats_col5:
        compliance_rate = (full_compliant / total_products * 100) if total_products > 0 else 0
        st.metric("Muvofiqlik Darajasi", f"{compliance_rate:.1f}%")
    
    # Status summary
    if compliance_rate >= 80:
        st.success(f"✅ Yaxshi natija! {compliance_rate:.1f}% tovarlar to'liq muvofiq")
    elif compliance_rate >= 50:
        st.warning(f"⚠️ O'rtacha natija. {non_compliant} ta tovarni yaxshilash kerak")
    else:
        st.error(f"❌ Yomon natija. {non_compliant} ta tovarda jiddiy kamchiliklar bor")

def display_analysis_charts(results):
    """Tahlil diagrammalarini ko'rsatish"""
    st.markdown("### 📈 Vizual Tahlil")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        fig1 = create_enhanced_completion_chart(results)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.error("Diagram yaratishda xato")
    
    with chart_col2:
        fig2 = create_sections_stats_chart(results)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.error("Diagram yaratishda xato")

def display_detailed_results(results):
    """Batafsil natijalarni ko'rsatish"""
    st.markdown("### 📋 Batafsil Tahlil")
    
    # Filter and sort options
    detail_filter_col1, detail_filter_col2, detail_filter_col3 = st.columns(3)
    
    with detail_filter_col1:
        filter_option = st.selectbox(
            "Ko'rsatish:",
            ["Barchasi", "To'liq muvofiq", "Qisman muvofiq", "Nomuvofiq"],
            key="detail_filter"
        )
    
    with detail_filter_col2:
        sort_option = st.selectbox(
            "Tartiblash:",
            ["Majburiy bo'limlar (yuqori)", "Majburiy bo'limlar (past)", 
             "Umumiy bo'limlar (yuqori)", "Tovar nomi"],
            key="detail_sort"
        )
    
    with detail_filter_col3:
        max_display = st.selectbox(
            "Ko'rsatish soni:",
            [5, 10, 20, "Barchasi"],
            key="max_display"
        )
    
    # Apply filters and sorting
    filtered_results = filter_results(results, filter_option)
    sorted_results = sort_results(filtered_results, sort_option)
    
    # Limit display count
    if max_display != "Barchasi":
        sorted_results = sorted_results[:max_display]
    
    # Display results
    for idx, item in enumerate(sorted_results):
        display_product_detail(item, idx)

def filter_results(results, filter_option):
    """Natijalarni filterlash"""
    if filter_option == "Barchasi":
        return results
    elif filter_option == "To'liq muvofiq":
        return [r for r in results if r.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT]
    elif filter_option == "Qisman muvofiq":
        return [r for r in results if r.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT]
    elif filter_option == "Nomuvofiq":
        return [r for r in results if r.get('compliance_level') == ComplianceLevel.NON_COMPLIANT]
    return results

def sort_results(results, sort_option):
    """Natijalarni tartiblash"""
    try:
        if sort_option == "Majburiy bo'limlar (yuqori)":
            return sorted(results, key=lambda x: get_required_rate(x), reverse=True)
        elif sort_option == "Majburiy bo'limlar (past)":
            return sorted(results, key=lambda x: get_required_rate(x))
        elif sort_option == "Umumiy bo'limlar (yuqori)":
            return sorted(results, key=lambda x: get_general_rate(x), reverse=True)
        elif sort_option == "Tovar nomi":
            return sorted(results, key=lambda x: get_product_name(x))
        return results
    except Exception as e:
        logger.error(f"Sorting error: {str(e)}")
        return results

def get_required_rate(item):
    """Majburiy bo'limlar foizini olish"""
    rates = item.get('completion_rates')
    if isinstance(rates, CompletionRates):
        return rates.required
    return item.get('completion_rates', {}).get('required', 0)

def get_general_rate(item):
    """Umumiy bo'limlar foizini olish"""
    rates = item.get('completion_rates')
    if isinstance(rates, CompletionRates):
        return rates.general
    return item.get('completion_rates', {}).get('general', 0)

def get_product_name(item):
    """Tovar nomini olish"""
    product_info = item.get('product_info')
    if isinstance(product_info, ProductInfo):
        return product_info.name.lower()
    return item.get('product_info', {}).get('name', '').lower()

def display_product_detail(item, idx):
    """Tovar batafsil ma'lumotini ko'rsatish"""
    # Extract data safely
    completion_rates = item.get('completion_rates')
    if isinstance(completion_rates, CompletionRates):
        general_rate = completion_rates.general
        required_rate = completion_rates.required
    else:
        rates_dict = item.get('completion_rates', {})
        general_rate = rates_dict.get('general', 0)
        required_rate = rates_dict.get('required', 0)
    
    compliance_level = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
    
    # Status indicators
    if compliance_level == ComplianceLevel.FULL_COMPLIANT:
        status_icon = "🟢"
        status_text = "TO'LIQ MUVOFIQ"
        status_color = "success"
    elif compliance_level == ComplianceLevel.PARTIAL_COMPLIANT:
        status_icon = "🟡"
        status_text = "QISMAN MUVOFIQ"
        status_color = "warning"
    else:
        status_icon = "🔴"
        status_text = "NOMUVOFIQ"
        status_color = "error"
    
    # Product info
    product_info = item.get('product_info')
    if isinstance(product_info, ProductInfo):
        product_name = product_info.name
    else:
        product_name = item.get('product_info', {}).get('name', 'Noma\'lum')
    
    # Main expander
    with st.expander(f"{status_icon} {idx+1}. {product_name} - {status_text} (Majburiy: {required_rate:.1f}%)"):
        
        # Basic information
        display_product_basic_info(item)
        
        # Grafa sections
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            display_filled_sections(item)
        
        with detail_col2:
            display_missing_sections(item)

def display_product_basic_info(item):
    """Tovarning asosiy ma'lumotlarini ko'rsatish"""
    # Product info
    product_info = item.get('product_info')
    completion_rates = item.get('completion_rates')
    
    if isinstance(product_info, ProductInfo):
        name = product_info.name
        brand = product_info.brand
        model = product_info.model
    else:
        info_dict = item.get('product_info', {})
        name = info_dict.get('name', 'Noma\'lum')
        brand = info_dict.get('brand', 'Noma\'lum')
        model = info_dict.get('model', 'Noma\'lum')
    
    # Display basic info
    basic_info_col1, basic_info_col2, basic_info_col3 = st.columns(3)
    with basic_info_col1:
        st.write(f"**Tovar nomi:** {name}")
    with basic_info_col2:
        st.write(f"**Brend:** {brand}")
    with basic_info_col3:
        st.write(f"**Model:** {model}")
    
    # Metrics
    if isinstance(completion_rates, CompletionRates):
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        with metrics_col1:
            st.metric("Majburiy Bo'limlar", f"{completion_rates.required:.1f}%")
        with metrics_col2:
            st.metric("Umumiy Bo'limlar", f"{completion_rates.general:.1f}%")
        with metrics_col3:
            st.metric("To'ldirilgan", completion_rates.filled_sections)
        with metrics_col4:
            st.metric("Jami", completion_rates.total_sections)
    
    # Validation warnings
    if not item.get('is_valid', True) and item.get('validation_warnings'):
        st.warning("⚠️ Validatsiya ogohlantirishlari:")
        for warning in item.get('validation_warnings', []):
            st.write(f"• {warning}")

def display_filled_sections(item):
    """To'ldirilgan bo'limlarni ko'rsatish"""
    st.markdown("**✅ To'ldirilgan bo'limlar:**")
    grafa_data = item.get('grafa_data', {})
    
    if not grafa_data:
        st.write("Hech qanday bo'lim to'ldirilmagan")
        return
    
    for section_key, content in grafa_data.items():
        section_info = GRAFA_31_SECTIONS.get(section_key, {})
        section_name = section_info.get('name', section_key)
        is_required = section_info.get('required', False)
        
        required_badge = "⭐" if is_required else "📋"
        
        # Truncate long content
        display_content = str(content)
        if len(display_content) > 150:
            display_content = display_content[:150] + "..."
        
        st.markdown(f"""
        <div class="grafa-section filled-section">
            <span class="section-number">{section_key.split('_')[0]}</span>
            <b>{section_name}</b> {required_badge}
            <br><small>{display_content}</small>
        </div>
        """, unsafe_allow_html=True)

def display_missing_sections(item):
    """Yetishmayotgan bo'limlarni ko'rsatish"""
    st.markdown("**❌ Yetishmayotgan bo'limlar:**")
    missing_sections = item.get('missing_sections', {})
    
    # Required missing sections
    required_missing = missing_sections.get('required', [])
    if required_missing:
        st.markdown("**🔴 Majburiy (KRITIK):**")
        for section_key in required_missing:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            st.markdown(f"""
            <div class="grafa-section missing-section">
                <span class="section-number">{section_key.split('_')[0]}</span>
                {section_name}
                <span class="required-badge">KRITIK</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Optional missing sections
    optional_missing = missing_sections.get('optional', [])
    if optional_missing:
        st.markdown("**🔵 Ixtiyoriy:**")
        display_count = min(3, len(optional_missing))  # Show max 3
        
        for section_key in optional_missing[:display_count]:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            st.markdown(f"""
            <div class="grafa-section missing-section">
                <span class="section-number">{section_key.split('_')[0]}</span>
                {section_name}
                <span class="optional-badge">Ixtiyoriy</span>
            </div>
            """, unsafe_allow_html=True)
        
        if len(optional_missing) > display_count:
            st.write(f"... va yana {len(optional_missing) - display_count} ta ixtiyoriy bo'lim")
    
    if not required_missing and not optional_missing:
        st.success("Barcha bo'limlar to'ldirilgan!")

def show_analysis_navigation():
    """Tahlil sahifasi navigatsiyasi"""
    st.markdown("---")
    nav_col1, nav_col2 = st.columns(2)
    
    with nav_col1:
        if st.button("🌐 Web Search", use_container_width=True):
            st.session_state.current_page = 'search'
            st.rerun()
    
    with nav_col2:
        if st.button("📄 Rasmiy Hisobot", use_container_width=True):
            st.session_state.current_page = 'report'
            st.rerun()

def show_enhanced_search_page():
    """Yaxshilangan qidiruv sahifasi"""
    st.markdown("# 🌐 Web Search - Yetishmayotgan Ma'lumotlarni To'ldirish")
    st.markdown("---")
    
    if not st.session_state.processed_data:
        show_no_data_warning('analysis')
        return
    
    # Missing sections analysis
    display_missing_analysis()
    
    # Search configuration
    display_search_configuration()
    
    # Search execution
    if st.button("🚀 Aqlli Web Search Boshlash", type="primary", use_container_width=True):
        execute_smart_search()
    
    # Navigation
    show_search_navigation()

def display_missing_analysis():
    """Yetishmayotgan ma'lumotlar tahlili"""
    results = st.session_state.processed_data
    
    # Calculate missing statistics with smart filtering
    total_missing_required = 0
    total_missing_optional = 0
    total_skipped_required = 0
    total_skipped_optional = 0
    products_with_missing_required = 0
    
    missing_by_section = {}
    skipped_by_section = {}
    
    for item in results:
        missing_sections = item.get('missing_sections', {})
        required_missing = missing_sections.get('required', [])
        optional_missing = missing_sections.get('optional', [])
        
        product_info = item.get('product_info')
        
        # Separate truly missing from not applicable
        actual_required_missing = []
        actual_optional_missing = []
        skipped_required = []
        skipped_optional = []
        
        for section_key in required_missing:
            if st.session_state.processor.should_skip_section_search(product_info, section_key):
                skipped_required.append(section_key)
                total_skipped_required += 1
            else:
                actual_required_missing.append(section_key)
                total_missing_required += 1
        
        for section_key in optional_missing:
            if st.session_state.processor.should_skip_section_search(product_info, section_key):
                skipped_optional.append(section_key)
                total_skipped_optional += 1
            else:
                actual_optional_missing.append(section_key)
                total_missing_optional += 1
        
        if actual_required_missing:
            products_with_missing_required += 1
        
        # Count by section (actual missing only)
        for section_key in actual_required_missing + actual_optional_missing:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            
            if section_name not in missing_by_section:
                missing_by_section[section_name] = 0
            missing_by_section[section_name] += 1
        
        # Count skipped sections
        for section_key in skipped_required + skipped_optional:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            
            if section_name not in skipped_by_section:
                skipped_by_section[section_name] = 0
            skipped_by_section[section_name] += 1
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Kerak Bo'lgan Majburiy", total_missing_required)
    with col2:
        st.metric("Kerak Bo'lgan Ixtiyoriy", total_missing_optional)
    with col3:
        st.metric("Tegishli Emas", total_skipped_required + total_skipped_optional)
    with col4:
        total_products = len(results)
        coverage = ((total_products - products_with_missing_required) / total_products * 100) if total_products > 0 else 0
        st.metric("Majburiy Qamrovlik", f"{coverage:.1f}%")
    
    # Status message
    if total_missing_required == 0:
        st.success("🎉 Barcha kerak bo'lgan majburiy bo'limlar to'ldirilgan!")
        if total_skipped_required > 0:
            st.info(f"ℹ️ {total_skipped_required} ta majburiy bo'lim bu tovarlar uchun tegishli emas")
    else:
        st.warning(f"⚠️ {total_missing_required} ta majburiy bo'lim haqiqatan ham to'ldirilishi kerak")
        if total_skipped_required > 0:
            st.info(f"ℹ️ {total_skipped_required} ta majburiy bo'lim bu tovarlar uchun tegishli emas")
    
    # Most missing sections (actual missing only)
    if missing_by_section:
        st.markdown("### 📊 Haqiqatan Yetishmayotgan Bo'limlar")
        sorted_missing = sorted(missing_by_section.items(), key=lambda x: x[1], reverse=True)
        
        for section_name, count in sorted_missing[:5]:
            percentage = (count / len(results)) * 100
            if count > 0:
                st.write(f"• **{section_name[:60]}{'...' if len(section_name) > 60 else ''}**: {count} ta tovar ({percentage:.1f}%)")
    
    # Most skipped sections
    if skipped_by_section:
        st.markdown("### ⏭️ Tovar Turiga Mos Kelmaydigan Bo'limlar")
        sorted_skipped = sorted(skipped_by_section.items(), key=lambda x: x[1], reverse=True)
        
        for section_name, count in sorted_skipped[:3]:
            percentage = (count / len(results)) * 100
            if count > 0:
                st.write(f"• **{section_name[:60]}{'...' if len(section_name) > 60 else ''}**: {count} ta tovar ({percentage:.1f}%)")
        
        st.markdown("""
        **💡 Tushuntirish:**
        - **Aksiz markalari**: Avtomobillar uchun aksiz markalari yo'q, faqat alkogol, tamaki va ba'zi maxsus tovarlar uchun
        - **Konteyner raqamlari**: Kichik tovarlar yoki individual yuklar uchun alohida konteyner kerak emas  
        - **Yetkazib berish muddati**: Faqat quvur transporti va elektr uzatish liniyalari uchun
        - **Investitsiya/Soha kodlari**: Faqat sanoat asbob-uskunalari uchun tegishli
        """)

def display_search_configuration():
    """Qidiruv konfiguratsiyasi"""
    st.markdown("### ⚙️ Qidiruv Sozlamalari")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        search_priority = st.selectbox(
            "Birinchi navbatda qidirish:",
            ["Majburiy bo'limlar", "Hammasi", "Ixtiyoriy bo'limlar"],
            key="search_priority"
        )
    
    with config_col2:
        max_products = st.selectbox(
            "Maksimal tovarlar soni:",
            [5, 10, 20, "Barchasi"],
            key="max_search_products"
        )
    
    with config_col3:
        sections_per_product = st.selectbox(
            "Har bir tovar uchun maksimal qidiruv:",
            [2, 3, 5, "Barchasi"],
            key="sections_per_product"
        )
    
    # Search preview
    if st.checkbox("Qidiruv rejasini ko'rsatish"):
        display_search_plan(search_priority, max_products, sections_per_product)

def display_search_plan(priority, max_products, sections_per_product):
    """Qidiruv rejasini ko'rsatish"""
    results = st.session_state.processed_data
    
    st.markdown("#### 📋 Aqlli Qidiruv Rejasi")
    
    search_queue = []
    skipped_sections = []
    
    for idx, item in enumerate(results):
        if max_products != "Barchasi" and idx >= max_products:
            break
        
        missing_sections = item.get('missing_sections', {})
        product_info = item.get('product_info')
        
        if isinstance(product_info, ProductInfo):
            product_name = product_info.name
        else:
            product_name = item.get('product_info', {}).get('name', f'Tovar {idx+1}')
        
        # Prioritize sections
        if priority == "Majburiy bo'limlar":
            sections_to_search = missing_sections.get('required', [])
        elif priority == "Ixtiyoriy bo'limlar":
            sections_to_search = missing_sections.get('optional', [])
        else:  # Hammasi
            sections_to_search = missing_sections.get('required', []) + missing_sections.get('optional', [])
        
        # Filter out sections that should be skipped
        actual_sections = []
        skipped_for_product = []
        
        for section_key in sections_to_search:
            if st.session_state.processor.should_skip_section_search(product_info, section_key):
                skipped_for_product.append(section_key)
            else:
                actual_sections.append(section_key)
        
        # Limit sections per product
        if sections_per_product != "Barchasi":
            actual_sections = actual_sections[:sections_per_product]
        
        if actual_sections or skipped_for_product:
            search_queue.append((product_name, actual_sections, skipped_for_product))
    
    # Display plan
    if search_queue:
        total_searches = sum(len(sections) for _, sections, _ in search_queue)
        total_skipped = sum(len(skipped) for _, _, skipped in search_queue)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📊 **{len(search_queue)} ta tovar**")
        with col2:
            st.success(f"🔍 **{total_searches} ta qidiruv**")
        with col3:
            st.warning(f"⏭️ **{total_skipped} ta o'tkazib yuborish**")
        
        # Show details for first few products
        for idx, (product_name, sections, skipped) in enumerate(search_queue[:3]):
            st.write(f"**{idx + 1}. {product_name[:40]}{'...' if len(product_name) > 40 else ''}**")
            
            if sections:
                section_names = [GRAFA_31_SECTIONS[s]['name'][:30] + '...' if len(GRAFA_31_SECTIONS[s]['name']) > 30 else GRAFA_31_SECTIONS[s]['name'] for s in sections]
                st.write(f"   🔍 Qidiriladi: {', '.join(section_names)}")
            
            if skipped:
                skipped_names = [GRAFA_31_SECTIONS[s]['name'][:30] + '...' if len(GRAFA_31_SECTIONS[s]['name']) > 30 else GRAFA_31_SECTIONS[s]['name'] for s in skipped]
                st.write(f"   ⏭️ O'tkazib yuboriladi: {', '.join(skipped_names)}")
        
        if len(search_queue) > 3:
            st.write(f"... va yana {len(search_queue) - 3} ta tovar")
        
        # Show common skipped reasons
        if total_skipped > 0:
            st.markdown("##### 💡 O'tkazib Yuborish Sababları:")
            st.write("• **Aksiz markalari**: Avtomobillarga aksiz markalari talab etilmaydi")
            st.write("• **Konteyner raqamlari**: Kichik yoki maxsus tovarlar alohida konteynerda tashilmaydi")
            st.write("• **Yetkazib berish**: Faqat quvur transporti va elektr uzatish uchun")
            st.write("• **Investitsiya/Soha kodlari**: Faqat tegishli asbob-uskunalar uchun")
    else:
        st.warning("Qidiruv uchun mos tovarlar topilmadi")

def execute_smart_search():
    """Aqlli qidiruv amalga oshirish"""
    results = st.session_state.processed_data
    
    # Get search parameters
    search_priority = st.session_state.get('search_priority', 'Majburiy bo\'limlar')
    max_products = st.session_state.get('max_search_products', 10)
    sections_per_product = st.session_state.get('sections_per_product', 2)
    
    progress_container = st.container()
    progress_container.markdown('<div class="success-message">🔍 Aqlli Web Search jarayoni boshlandi...</div>', 
                               unsafe_allow_html=True)
    
    # Initialize counters
    filled_count = 0
    total_attempts = 0
    error_count = 0
    skipped_count = 0
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner("Aqlli qidiruv algoritmi ishlamoqda..."):
        search_products = results[:max_products] if max_products != "Barchasi" else results
        
        for idx, item in enumerate(search_products):
            missing_sections = item.get('missing_sections', {})
            product_info = item.get('product_info')
            
            if isinstance(product_info, ProductInfo):
                product_name = product_info.name
            else:
                product_name = item.get('product_info', {}).get('name', f'Tovar {idx+1}')
            
            # Skip if no missing sections
            all_missing = missing_sections.get('required', []) + missing_sections.get('optional', [])
            if not all_missing:
                continue
            
            status_text.text(f"Qidiruv: {idx + 1}/{len(search_products)} - {product_name[:40]}...")
            progress_container.write(f"\n📦 **{idx + 1}. {product_name}**")
            
            # Select sections based on priority
            if search_priority == "Majburiy bo'limlar":
                sections_to_search = missing_sections.get('required', [])
            elif search_priority == "Ixtiyoriy bo'limlar":
                sections_to_search = missing_sections.get('optional', [])
            else:
                # Prioritize required, then optional
                required = missing_sections.get('required', [])
                optional = missing_sections.get('optional', [])
                sections_to_search = required + optional
            
            # Limit sections per product
            if sections_per_product != "Barchasi":
                sections_to_search = sections_to_search[:sections_per_product]
            
            # Search for each section
            for section_key in sections_to_search:
                section_info = GRAFA_31_SECTIONS.get(section_key, {})
                section_name = section_info.get('name', section_key)
                is_required = section_info.get('required', False)
                priority_label = "🔴 MAJBURIY" if is_required else "🔵 Ixtiyoriy"
                
                total_attempts += 1
                
                try:
                    filled_info, success = st.session_state.processor.fill_missing_section(
                        product_info, section_key, progress_container
                    )
                    
                    # Tegishli emasligini tekshirish
                    if "Bu tovar turi uchun tegishli emas" in filled_info:
                        skipped_count += 1
                        # Yetishmayotgan bo'limlardan olib tashlash
                        if section_key in missing_sections.get('required', []):
                            missing_sections['required'].remove(section_key)
                        elif section_key in missing_sections.get('optional', []):
                            missing_sections['optional'].remove(section_key)
                        continue
                    
                    if success:
                        # Add to grafa_data
                        if 'grafa_data' not in item:
                            item['grafa_data'] = {}
                        item['grafa_data'][section_key] = filled_info
                        
                        # Remove from missing sections
                        if section_key in missing_sections.get('required', []):
                            missing_sections['required'].remove(section_key)
                        elif section_key in missing_sections.get('optional', []):
                            missing_sections['optional'].remove(section_key)
                        
                        filled_count += 1
                        progress_container.write(f"  ✅ **{priority_label} {section_name[:50]}**: muvaffaqiyatli to'ldirildi")
                        
                    else:
                        progress_container.write(f"  ❌ **{priority_label} {section_name[:50]}**: ma'lumot topilmadi")
                    
                except Exception as e:
                    error_count += 1
                    progress_container.write(f"  ⚠️ **{section_name[:50]}**: xato - {str(e)}")
                    logger.error(f"Search error for {section_key}: {str(e)}")
            
            # Update completion rates
            item['completion_rates'] = st.session_state.processor.calculate_completion_rate(item.get('grafa_data', {}))
            item['missing_sections'] = missing_sections
            
            # Update progress
            progress_bar.progress((idx + 1) / len(search_products))
    
    # Final results
    success_rate = (filled_count / (total_attempts - skipped_count)) * 100 if (total_attempts - skipped_count) > 0 else 0
    
    if success_rate >= 70:
        message_type = "success-message"
        icon = "🎉"
    elif success_rate >= 40:
        message_type = "warning-message"
        icon = "⚠️"
    else:
        message_type = "error-message"
        icon = "❌"
    
    progress_container.markdown(f'''
    <div class="{message_type}">
        {icon} Aqlli Web Search yakunlandi!<br>
        ✅ To'ldirildi: {filled_count} ta bo'lim<br>
        ⏭️ O'tkazib yuborildi: {skipped_count} ta (tovar turiga mos emas)<br>
        ❌ Topilmadi: {total_attempts - filled_count - skipped_count} ta<br>
        ⚠️ Xatolar: {error_count} ta<br>
        📊 Muvaffaqiyat darajasi: {success_rate:.1f}%
    </div>
    ''', unsafe_allow_html=True)
    
    status_text.success(f"✅ Aqlli qidiruv yakunlandi! Muvaffaqiyat: {success_rate:.1f}%")

def show_search_navigation():
    """Qidiruv sahifasi navigatsiyasi"""
    st.markdown("---")
    search_nav_col1, search_nav_col2 = st.columns(2)
    
    with search_nav_col1:
        if st.button("🔍 Tahlilni Qayta Qilish", use_container_width=True):
            st.session_state.current_page = 'analysis'
            st.rerun()
    
    with search_nav_col2:
        if st.button("📄 Rasmiy Hisobot Ko'rish", use_container_width=True):
            st.session_state.current_page = 'report'
            st.rerun()

def show_enhanced_report_page():
    """Yaxshilangan hisobot sahifasi"""
    st.markdown("# 📄 31-Grafa Rasmiy Hisobot")
    st.markdown("---")
    
    if not st.session_state.processed_data:
        show_no_data_warning('analysis')
        return
    
    results = st.session_state.processed_data
    
    # Report header with key metrics
    display_report_header(results)
    
    # Report tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 To'liq Hisobot", 
        "📊 Statistika", 
        "⚖️ Muvofiqlik", 
        "💾 Eksport",
        "📈 Tendentsiyalar"
    ])
    
    with tab1:
        display_full_report_tab(results)
    
    with tab2:
        display_statistics_tab(results)
    
    with tab3:
        display_compliance_tab(results)
    
    with tab4:
        display_export_tab(results)
    
    with tab5:
        display_trends_tab(results)

def display_report_header(results):
    """Hisobot sarlavhasi va asosiy metrikalar"""
    total_products = len(results)
    
    # Calculate safe averages
    avg_general = 0
    avg_required = 0
    compliance_counts = {
        ComplianceLevel.FULL_COMPLIANT: 0,
        ComplianceLevel.PARTIAL_COMPLIANT: 0,
        ComplianceLevel.NON_COMPLIANT: 0
    }
    
    if total_products > 0:
        general_sum = 0
        required_sum = 0
        
        for item in results:
            rates = item.get('completion_rates')
            if isinstance(rates, CompletionRates):
                general_sum += rates.general
                required_sum += rates.required
            else:
                rates_dict = item.get('completion_rates', {})
                general_sum += rates_dict.get('general', 0)
                required_sum += rates_dict.get('required', 0)
            
            compliance = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
            compliance_counts[compliance] += 1
        
        avg_general = general_sum / total_products
        avg_required = required_sum / total_products
    
    # Display header metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Jami Tovarlar", total_products)
    with col2:
        st.metric("O'rtacha Umumiy", f"{avg_general:.1f}%")
    with col3:
        st.metric("O'rtacha Majburiy", f"{avg_required:.1f}%")
    with col4:
        st.metric("To'liq Muvofiq", compliance_counts[ComplianceLevel.FULL_COMPLIANT],
                 delta=f"{(compliance_counts[ComplianceLevel.FULL_COMPLIANT]/total_products*100):.1f}%")
    with col5:
        st.metric("Qisman Muvofiq", compliance_counts[ComplianceLevel.PARTIAL_COMPLIANT])
    with col6:
        overall_compliance = (compliance_counts[ComplianceLevel.FULL_COMPLIANT] / total_products * 100) if total_products > 0 else 0
        st.metric("Umumiy Muvofiqlik", f"{overall_compliance:.1f}%")
    
    # Executive summary
    if overall_compliance >= 90:
        st.success("🎉 A'lo natija! Deyarli barcha tovarlar yo'riqnoma talablariga to'liq muvofiq")
    elif overall_compliance >= 70:
        st.info("✅ Yaxshi natija! Ko'pgina tovarlar muvofiq, ba'zilari yaxshilanishi mumkin")
    elif overall_compliance >= 50:
        st.warning("⚠️ O'rtacha natija. Bir necha tovarlarni yaxshilash talab etiladi")
    else:
        st.error("❌ Kam natija. Ko'pgina tovarlarda jiddiy kamchiliklar mavjud")

def display_full_report_tab(results):
    """To'liq hisobot bo'limi"""
    st.markdown("### 📋 Har bir Tovar uchun 31-Grafa Rasmiy Tahlili")
    
    # Filters
    filter_rep_col1, filter_rep_col2 = st.columns(2)
    with filter_rep_col1:
        compliance_filter = st.selectbox(
            "Muvofiqlik bo'yicha filter:",
            ["Barchasi", "To'liq muvofiq", "Qisman muvofiq", "Nomuvofiq"],
            key="report_compliance_filter"
        )
    
    with filter_rep_col2:
        sort_by = st.selectbox(
            "Tartiblash:",
            ["Majburiy foiz (yuqori)", "Majburiy foiz (past)", "Tovar nomi"],
            key="report_sort_by"
        )
    
    # Apply filters
    filtered_results = filter_results(results, compliance_filter)
    sorted_results = sort_results(filtered_results, sort_by)
    
    # Display count
    st.info(f"Ko'rsatilmoqda: {len(sorted_results)} ta tovar")
    
    # Display results
    for idx, item in enumerate(sorted_results):
        display_comprehensive_product_report(item, idx)

def display_comprehensive_product_report(item, idx):
    """Har bir tovar uchun keng qamrovli hisobot"""
    # Extract data safely
    completion_rates = item.get('completion_rates')
    if isinstance(completion_rates, CompletionRates):
        general_rate = completion_rates.general
        required_rate = completion_rates.required
        filled_sections = completion_rates.filled_sections
        total_sections = completion_rates.total_sections
    else:
        rates_dict = item.get('completion_rates', {})
        general_rate = rates_dict.get('general', 0)
        required_rate = rates_dict.get('required', 0)
        filled_sections = rates_dict.get('filled_sections', 0)
        total_sections = rates_dict.get('total_sections', 11)
    
    compliance_level = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
    
    # Status indicators
    if compliance_level == ComplianceLevel.FULL_COMPLIANT:
        status_icon = "🟢"
        status_text = "TO'LIQ MUVOFIQ"
        status_color = "#059669"
    elif compliance_level == ComplianceLevel.PARTIAL_COMPLIANT:
        status_icon = "🟡"
        status_text = "QISMAN MUVOFIQ"
        status_color = "#D97706"
    else:
        status_icon = "🔴"
        status_text = "NOMUVOFIQ"
        status_color = "#DC2626"
    
    # Product info
    product_info = item.get('product_info')
    if isinstance(product_info, ProductInfo):
        product_name = product_info.name
        brand = product_info.brand
        model = product_info.model
    else:
        info_dict = item.get('product_info', {})
        product_name = info_dict.get('name', 'Noma\'lum')
        brand = info_dict.get('brand', 'Noma\'lum')
        model = info_dict.get('model', 'Noma\'lum')
    
    # Main expander
    with st.expander(f"{status_icon} {idx+1}. {product_name} - {status_text} (Majburiy: {required_rate:.1f}%)"):
        
        # Status banner
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {status_color}, {status_color}aa); 
                    color: white; padding: 1rem; border-radius: 8px; text-align: center; 
                    font-weight: bold; margin-bottom: 1rem;">
            {status_text} - Majburiy Bo'limlar: {required_rate:.1f}%
        </div>
        """, unsafe_allow_html=True)
        
        # Basic information
        comp_rep_col1, comp_rep_col2, comp_rep_col3 = st.columns(3)
        with comp_rep_col1:
            st.write(f"**📦 Tovar nomi:** {product_name}")
        with comp_rep_col2:
            st.write(f"**🏷️ Brend:** {brand if brand else 'Noma\'lum'}")
        with comp_rep_col3:
            st.write(f"**🔧 Model:** {model if model else 'Noma\'lum'}")
        
        # Detailed metrics
        st.markdown("#### 📊 Batafsil Metrikalar")
        comp_metrics_col1, comp_metrics_col2, comp_metrics_col3, comp_metrics_col4 = st.columns(4)
        
        with comp_metrics_col1:
            st.metric("Majburiy Bo'limlar", f"{required_rate:.1f}%", 
                     delta=f"{required_rate - 100:.1f}%" if required_rate != 100 else None)
        with comp_metrics_col2:
            st.metric("Umumiy Bo'limlar", f"{general_rate:.1f}%",
                     delta=f"{general_rate - 75:.1f}%" if general_rate != 75 else None)
        with comp_metrics_col3:
            st.metric("To'ldirilgan", f"{filled_sections}/{total_sections}")
        with comp_metrics_col4:
            completion_percentage = (filled_sections / total_sections * 100) if total_sections > 0 else 0
            st.metric("To'ldirilish", f"{completion_percentage:.1f}%")
        
        st.markdown("---")
        
        # Grafa sections analysis
        comp_grafa_col1, comp_grafa_col2 = st.columns(2)
        
        with comp_grafa_col1:
            display_comprehensive_filled_sections(item)
        
        with comp_grafa_col2:
            display_comprehensive_missing_sections(item)
        
        # Validation and processing info
        display_processing_info(item)

def display_comprehensive_filled_sections(item):
    """To'ldirilgan bo'limlarni keng qamrovli ko'rsatish"""
    st.markdown("#### ✅ To'ldirilgan Bo'limlar")
    grafa_data = item.get('grafa_data', {})
    
    if not grafa_data:
        st.write("Hech qanday bo'lim to'ldirilmagan")
        return
    
    # Sort by section number
    sorted_sections = sorted(grafa_data.items(), key=lambda x: int(x[0].split('_')[0]))
    
    for section_key, content in sorted_sections:
        section_info = GRAFA_31_SECTIONS.get(section_key, {})
        section_name = section_info.get('name', section_key)
        is_required = section_info.get('required', False)
        
        # Status and priority indicators
        priority_icon = "⭐" if is_required else "📋"
        priority_text = "Majburiy" if is_required else "Ixtiyoriy"
        
        # Content analysis
        content_str = str(content)
        content_length = len(content_str)
        
        # Quality indicators
        if content_length > 100:
            quality_icon = "🟢"
            quality_text = "Batafsil"
        elif content_length > 20:
            quality_icon = "🟡"
            quality_text = "O'rtacha"
        else:
            quality_icon = "🔴"
            quality_text = "Qisqa"
        
        # Display content
        display_content = content_str[:100] + "..." if len(content_str) > 100 else content_str
        
        st.markdown(f"""
        <div class="grafa-section filled-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                    <span class="section-number">{section_key.split('_')[0]}</span>
                    <strong>{section_name}</strong>
                </div>
                <div>
                    {priority_icon} <small>{priority_text}</small>
                    {quality_icon} <small>{quality_text}</small>
                </div>
            </div>
            <div style="background: white; padding: 8px; border-radius: 4px; font-size: 0.9em;">
                {display_content}
            </div>
            <div style="margin-top: 4px; font-size: 0.8em; color: #666;">
                Uzunlik: {content_length} belgi
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_comprehensive_missing_sections(item):
    """Yetishmayotgan bo'limlarni keng qamrovli ko'rsatish"""
    st.markdown("#### ❌ Yetishmayotgan Bo'limlar")
    missing_sections = item.get('missing_sections', {})
    
    required_missing = missing_sections.get('required', [])
    optional_missing = missing_sections.get('optional', [])
    
    if not required_missing and not optional_missing:
        st.success("🎉 Barcha bo'limlar to'ldirilgan!")
        return
    
    # Critical missing (required)
    if required_missing:
        st.markdown("##### 🔴 KRITIK - Majburiy Bo'limlar")
        st.error(f"⚠️ {len(required_missing)} ta majburiy bo'lim yetishmaydi!")
        
        for section_key in required_missing:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            description = section_info.get('description', '')
            
            st.markdown(f"""
            <div class="grafa-section missing-section">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="section-number">{section_key.split('_')[0]}</span>
                        <strong>{section_name}</strong>
                        <span class="required-badge">KRITIK</span>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 0.85em; color: #666;">
                    {description[:100]}{'...' if len(description) > 100 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Optional missing
    if optional_missing:
        st.markdown("##### 🔵 Ixtiyoriy Bo'limlar")
        st.info(f"💡 {len(optional_missing)} ta ixtiyoriy bo'lim to'ldirilishi mumkin")
        
        # Show first 5 optional missing
        display_count = min(5, len(optional_missing))
        
        for section_key in optional_missing[:display_count]:
            section_info = GRAFA_31_SECTIONS.get(section_key, {})
            section_name = section_info.get('name', section_key)
            
            st.markdown(f"""
            <div class="grafa-section missing-section" style="background: #f0f9ff; border-left-color: #0ea5e9;">
                <span class="section-number">{section_key.split('_')[0]}</span>
                {section_name}
                <span class="optional-badge">Ixtiyoriy</span>
            </div>
            """, unsafe_allow_html=True)
        
        if len(optional_missing) > display_count:
            st.write(f"... va yana {len(optional_missing) - display_count} ta ixtiyoriy bo'lim")

def display_processing_info(item):
    """Qayta ishlash ma'lumotlarini ko'rsatish"""
    st.markdown("#### ℹ️ Qayta Ishlash Ma'lumotlari")
    
    processing_col1, processing_col2, processing_col3 = st.columns(3)
    
    with processing_col1:
        is_valid = item.get('is_valid', True)
        status = "✅ Validatsiya o'tdi" if is_valid else "❌ Validatsiya xatosi"
        st.write(f"**Validatsiya:** {status}")
    
    with processing_col2:
        processed_at = item.get('processed_at', 'Noma\'lum')
        if processed_at != 'Noma\'lum':
            try:
                processed_time = datetime.fromisoformat(processed_at).strftime('%Y-%m-%d %H:%M')
                st.write(f"**Qayta ishlangan:** {processed_time}")
            except:
                st.write(f"**Qayta ishlangan:** {processed_at}")
        else:
            st.write(f"**Qayta ishlangan:** {processed_at}")
    
    with processing_col3:
        compliance_level = item.get('compliance_level', ComplianceLevel.NON_COMPLIANT)
        compliance_text = compliance_level.value if hasattr(compliance_level, 'value') else str(compliance_level)
        st.write(f"**Muvofiqlik:** {compliance_text}")
    
    # Validation warnings
    warnings = item.get('validation_warnings', [])
    if warnings:
        st.markdown("**⚠️ Validatsiya Ogohlantirishlari:**")
        for warning in warnings:
            st.write(f"• {warning}")

def display_statistics_tab(results):
    """Statistika bo'limi"""
    st.markdown("### 📊 31-Grafa Bo'limlari Statistikasi")
    
    # Enhanced visualizations
    stats_viz_col1, stats_viz_col2 = st.columns(2)
    
    with stats_viz_col1:
        fig1 = create_enhanced_completion_chart(results)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
    
    with stats_viz_col2:
        fig2 = create_sections_stats_chart(results)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed statistics table
    display_detailed_statistics_table(results)
    
    # Performance metrics
    display_performance_metrics()

def display_detailed_statistics_table(results):
    """Batafsil statistika jadvali"""
    st.markdown("### 📈 Bo'limlar bo'yicha Batafsil Jadval")
    
    total_products = len(results)
    section_stats = []
    
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        filled_count = sum(1 for item in results 
                         if section_key in item.get('grafa_data', {}))
        missing_count = total_products - filled_count
        percentage = (filled_count / total_products) * 100 if total_products > 0 else 0
        
        # Average content length for filled sections
        content_lengths = []
        for item in results:
            grafa_data = item.get('grafa_data', {})
            if section_key in grafa_data:
                content_lengths.append(len(str(grafa_data[section_key])))
        
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        section_stats.append({
            'Bo\'lim Raqami': section_key.split('_')[0],
            'Bo\'lim Nomi': section_info['name'][:50] + ('...' if len(section_info['name']) > 50 else ''),
            'Turi': '⭐ Majburiy' if section_info.get('required', False) else '📋 Ixtiyoriy',
            'To\'ldirilgan': filled_count,
            'Yetishmayotgan': missing_count,
            'Foiz': f"{percentage:.1f}%",
            'O\'rtacha Uzunlik': f"{avg_length:.0f}",
            'Sifat': get_quality_indicator(percentage, avg_length)
        })
    
    # Sort by completion percentage
    section_stats.sort(key=lambda x: float(x['Foiz'].replace('%', '')), reverse=True)
    
    df_stats = pd.DataFrame(section_stats)
    
    # Color coding based on completion rate
    def color_percentage(val):
        if val.endswith('%'):
            num = float(val.replace('%', ''))
            if num >= 80:
                return 'background-color: #dcfce7'  # Light green
            elif num >= 50:
                return 'background-color: #fef3c7'  # Light yellow
            else:
                return 'background-color: #fef2f2'  # Light red
        return ''
    
    styled_df = df_stats.style.applymap(color_percentage, subset=['Foiz'])
    st.dataframe(styled_df, use_container_width=True)

def get_quality_indicator(percentage, avg_length):
    """Sifat indikatorini olish"""
    if percentage >= 80 and avg_length >= 50:
        return "🟢 A'lo"
    elif percentage >= 60 and avg_length >= 30:
        return "🟡 Yaxshi"
    elif percentage >= 40:
        return "🟠 O'rtacha"
    else:
        return "🔴 Yomon"

def display_performance_metrics():
    """Sistema unumdorligi metriklari"""
    st.markdown("### ⚡ Sistema Unumdorligi")
    
    if st.session_state.processor:
        stats = st.session_state.processor.get_processing_stats()
        
        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        
        with perf_col1:
            st.metric("Qayta Ishlangan", stats['processed_count'])
        with perf_col2:
            st.metric("Muvaffaqiyat Darajasi", f"{stats['success_rate']:.1f}%")
        with perf_col3:
            st.metric("Qidiruv So'rovlari", stats['search_requests'])
        with perf_col4:
            if stats['search_requests'] > 0:
                st.metric("Qidiruv Muvaffaqiyati", f"{stats['search_success_rate']:.1f}%")

def display_compliance_tab(results):
    """Muvofiqlik bo'limi"""
    st.markdown("### ⚖️ Yo'riqnomaga Muvofiqlik Tahlili")
    
    # Compliance distribution
    display_compliance_distribution(results)
    
    # Compliance analysis by categories
    display_compliance_analysis(results)
    
    # Recommendations
    display_compliance_recommendations(results)

def display_compliance_distribution(results):
    """Muvofiqlik taqsimoti"""
    total_products = len(results)
    
    compliant = [item for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT]
    partial = [item for item in results if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT]
    non_compliant = [item for item in results if item.get('compliance_level') == ComplianceLevel.NON_COMPLIANT]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="grafa-section filled-section">
            <h4>🟢 TO'LIQ MUVOFIQ</h4>
            <p><strong>{len(compliant)} ta tovar ({(len(compliant)/total_products*100):.1f}%)</strong></p>
            <p>Barcha majburiy bo'limlar to'ldirilgan</p>
            <p>Bojxona rasmiylashtirishga tayyor</p>
        </div>
        """, unsafe_allow_html=True)
        
        if compliant:
            st.write("**Top muvofiq tovarlar:**")
            for item in compliant[:3]:
                name = get_product_name_safe(item)
                required_rate = get_required_rate(item)
                st.write(f"• {name[:40]}{'...' if len(name) > 40 else ''} ({required_rate:.1f}%)")

def get_product_name_safe(item):
    """Xavfsiz tarzda tovar nomini olish"""
    product_info = item.get('product_info')
    if isinstance(product_info, ProductInfo):
        return product_info.name
    return item.get('product_info', {}).get('name', 'Noma\'lum')

def display_compliance_analysis(results):
    """Muvofiqlik tahlili"""
    st.markdown("### 📊 Muvofiqlik Tahlili")
    
    total_products = len(results)
    
    # Required sections analysis
    required_sections = [k for k, v in GRAFA_31_SECTIONS.items() if v.get('required', False)]
    
    st.markdown("#### 🔍 Majburiy Bo'limlar Tahlili")
    
    required_completion = {}
    for section_key in required_sections:
        section_info = GRAFA_31_SECTIONS[section_key]
        filled_count = sum(1 for item in results if section_key in item.get('grafa_data', {}))
        completion_rate = (filled_count / total_products * 100) if total_products > 0 else 0
        
        required_completion[section_key] = {
            'name': section_info['name'],
            'filled': filled_count,
            'rate': completion_rate,
            'critical': completion_rate < 80
        }
    
    # Show critical missing sections
    critical_sections = [(k, v) for k, v in required_completion.items() if v['critical']]
    
    if critical_sections:
        st.error(f"⚠️ {len(critical_sections)} ta majburiy bo'lim 80% dan kam to'ldirilgan!")
        
        for section_key, data in sorted(critical_sections, key=lambda x: x[1]['rate']):
            st.markdown(f"""
            <div class="error-message">
                <strong>{data['name'][:50]}{'...' if len(data['name']) > 50 else ''}</strong><br>
                To'ldirilgan: {data['filled']}/{total_products} ({data['rate']:.1f}%)
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Barcha majburiy bo'limlar 80% dan yuqori to'ldirilgan!")
    
    # Compliance trends
    display_compliance_trends(results)

def display_compliance_trends(results):
    """Muvofiqlik tendentsiyalari"""
    st.markdown("#### 📈 Muvofiqlik Tendentsiyalari")
    
    # Completion rate distribution
    completion_ranges = {
        '90-100%': 0,
        '80-89%': 0,
        '70-79%': 0,
        '60-69%': 0,
        '50-59%': 0,
        '<50%': 0
    }
    
    for item in results:
        required_rate = get_required_rate(item)
        
        if required_rate >= 90:
            completion_ranges['90-100%'] += 1
        elif required_rate >= 80:
            completion_ranges['80-89%'] += 1
        elif required_rate >= 70:
            completion_ranges['70-79%'] += 1
        elif required_rate >= 60:
            completion_ranges['60-69%'] += 1
        elif required_rate >= 50:
            completion_ranges['50-59%'] += 1
        else:
            completion_ranges['<50%'] += 1
    
    # Display distribution
    trends_col1, trends_col2 = st.columns(2)
    
    with trends_col1:
        st.write("**Majburiy Bo'limlar To'ldirilish Taqsimoti:**")
        for range_name, count in completion_ranges.items():
            percentage = (count / len(results) * 100) if results else 0
            if count > 0:
                if range_name in ['90-100%', '80-89%']:
                    st.success(f"✅ {range_name}: {count} ta tovar ({percentage:.1f}%)")
                elif range_name in ['70-79%', '60-69%']:
                    st.warning(f"⚠️ {range_name}: {count} ta tovar ({percentage:.1f}%)")
                else:
                    st.error(f"❌ {range_name}: {count} ta tovar ({percentage:.1f}%)")
    
    with trends_col2:
        # Create pie chart for compliance distribution
        try:
            labels = list(completion_ranges.keys())
            values = list(completion_ranges.values())
            
            # Filter out zero values
            filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0]
            if filtered_data:
                labels, values = zip(*filtered_data)
                
                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Majburiy Bo'limlar To'ldirilish Taqsimoti"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.write("Diagram yaratishda xato yuz berdi")

def display_compliance_recommendations(results):
    """Muvofiqlik tavsiyalari"""
    st.markdown("### 💡 Rasmiy Tavsiyalar")
    
    total_products = len(results)
    compliant_count = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    compliance_rate = (compliant_count / total_products * 100) if total_products > 0 else 0
    
    # Strategic recommendations
    if compliance_rate >= 95:
        st.markdown("""
        <div class="success-message">
            🎉 <strong>MUKAMMAL NATIJA!</strong><br>
            • Barcha tovarlar deyarli yo'riqnoma talablariga to'liq muvofiq<br>
            • Deklaratsiya jarayoni muammosiz o'tadi<br>
            • Joriy sifat nazorati tizimini saqlang
        </div>
        """, unsafe_allow_html=True)
        
    elif compliance_rate >= 80:
        st.markdown("""
        <div class="success-message">
            ✅ <strong>YAXSHI NATIJA!</strong><br>
            • Ko'pgina tovarlar muvofiq<br>
            • Qolgan tovarlar uchun qo'shimcha ma'lumot to'plash tavsiya etiladi<br>
            • Sistemli yondashuv bilan 100% muvofiqlikka erishish mumkin
        </div>
        """, unsafe_allow_html=True)
        
    elif compliance_rate >= 50:
        st.markdown("""
        <div class="warning-message">
            ⚠️ <strong>YAXSHILASH TALAB ETILADI!</strong><br>
            • Tovarlarning yarmi muvofiq emas<br>
            • Ma'lumot to'plash jarayonini qayta ko'rib chiqish kerak<br>
            • Web search va qo'shimcha tadqiqotlar amalga oshiring
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div class="error-message">
            🚨 <strong>JIDDIY MUAMMO!</strong><br>
            • Ko'pgina tovarlar yo'riqnoma talablariga javob bermaydi<br>
            • Bojxona rasmiylashtirishdan oldin jiddiy ishlash kerak<br>
            • Ma'lumot manbalarini qayta ko'rib chiqing va tizimli yondashuvni amalga oshiring
        </div>
        """, unsafe_allow_html=True)
    
    # Specific recommendations
    st.markdown("#### 🎯 Aniq Tavsiyalar")
    
    # Find most problematic sections
    section_problems = {}
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        if section_info.get('required', False):
            filled_count = sum(1 for item in results if section_key in item.get('grafa_data', {}))
            completion_rate = (filled_count / total_products * 100) if total_products > 0 else 0
            
            if completion_rate < 80:
                section_problems[section_key] = {
                    'name': section_info['name'],
                    'rate': completion_rate,
                    'missing_count': total_products - filled_count
                }
    
    if section_problems:
        st.warning(f"🔧 {len(section_problems)} ta majburiy bo'lim yaxshilanishi kerak:")
        
        for section_key, data in sorted(section_problems.items(), key=lambda x: x[1]['rate']):
            st.write(f"• **{data['name'][:60]}{'...' if len(data['name']) > 60 else ''}**: "
                    f"{data['missing_count']} ta tovarda yetishmaydi ({data['rate']:.1f}% to'ldirilgan)")
    else:
        st.success("✅ Barcha majburiy bo'limlar yaxshi darajada to'ldirilgan!")
    
    # Action plan
    display_action_plan(results)

def display_action_plan(results):
    """Harakat rejasi"""
    st.markdown("#### 📋 Harakat Rejasi")
    
    non_compliant = [item for item in results if item.get('compliance_level') == ComplianceLevel.NON_COMPLIANT]
    partial_compliant = [item for item in results if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT]
    
    steps = []
    
    if non_compliant:
        steps.append(f"1. **Kritik holatdagi {len(non_compliant)} ta tovarni birinchi navbatda tuzating**")
        steps.append("   - Majburiy bo'limlarni to'ldirish uchun qo'shimcha ma'lumot manbalarini topish")
        steps.append("   - Yetkazuvchilar bilan bog'lanib, texnik hujjatlarni so'rash")
        
    if partial_compliant:
        steps.append(f"2. **Qisman muvofiq {len(partial_compliant)} ta tovarni yaxshilash**")
        steps.append("   - Web search orqali yetishmayotgan ma'lumotlarni qidirish")
        steps.append("   - Mahsulot kataloglari va rasmiy veb-saytlarni tekshirish")
    
    steps.append("3. **Sifat nazorati tizimini o'rnatish**")
    steps.append("   - Yangi tovarlar uchun majburiy tekshiruv ro'yxati yaratish")
    steps.append("   - Ma'lumotlar bazasini muntazam yangilab turish")
    
    steps.append("4. **Jarayonni avtomatlashtirish**")
    steps.append("   - API integratsiyalari orqali ma'lumotlarni avtomatik to'plash")
    steps.append("   - Xatolarni erta aniqlash tizimini joriy etish")
    
    for step in steps:
        st.write(step)

def display_export_tab(results):
    """Eksport bo'limi"""
    st.markdown("### 💾 Rasmiy Eksport va Yuklab Olish")
    
    # Export statistics
    total_products = len(results)
    compliant_count = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    
    st.info(f"📊 **Eksport statistikasi**: {total_products} ta tovar, {compliant_count} ta to'liq muvofiq")
    
    # Excel export
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("#### 📊 Excel Hisobot")
        st.write("Keng qamrovli Excel hisobot - barcha ma'lumotlar, metrikalar va tahlillar")
        
        excel_buffer = export_to_enhanced_excel(results)
        
        if excel_buffer:
            st.download_button(
                label="📊 Rasmiy Excel Hisobot Yuklab Olish",
                data=excel_buffer,
                file_name=f"31_grafa_rasmiy_hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                help="Batafsil Excel hisobotni yuklab olish"
            )
        else:
            st.error("Excel eksport xatosi yuz berdi")
    
    with export_col2:
        st.markdown("#### 📄 JSON Ma'lumotlar")
        st.write("Texnik ma'lumotlar va API integratsiyasi uchun JSON format")
        
        # Create comprehensive JSON export
        export_data = create_comprehensive_json_export(results)
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📄 JSON Ma'lumotlarni Yuklab Olish",
            data=json_str.encode('utf-8'),
            file_name=f"31_grafa_ma_lumotlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="Texnik ma'lumotlarni JSON formatda yuklab olish"
        )
    
    # Export preview
    if st.checkbox("Eksport namunasini ko'rish"):
        display_export_preview(results)
    
    # Final summary
    display_final_summary(results)

def create_comprehensive_json_export(results):
    """Keng qamrovli JSON eksport yaratish"""
    total_products = len(results)
    
    # Calculate comprehensive statistics
    compliance_counts = {
        'full_compliant': sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT),
        'partial_compliant': sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT),
        'non_compliant': sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.NON_COMPLIANT)
    }
    
    # Average completion rates
    if results:
        avg_general = sum(get_general_rate(item) for item in results) / len(results)
        avg_required = sum(get_required_rate(item) for item in results) / len(results)
    else:
        avg_general = avg_required = 0
    
    # Section-wise statistics
    section_statistics = {}
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        filled_count = sum(1 for item in results if section_key in item.get('grafa_data', {}))
        section_statistics[section_key] = {
            'name': section_info['name'],
            'description': section_info['description'],
            'required': section_info.get('required', False),
            'filled_count': filled_count,
            'completion_rate': (filled_count / total_products * 100) if total_products > 0 else 0
        }
    
    # Processing statistics
    processing_stats = st.session_state.processor.get_processing_stats() if st.session_state.processor else {}
    
    return {
        "metadata": {
            "report_generated_at": datetime.now().isoformat(),
            "system_version": "31-Grafa Enhanced Analysis System v2.0",
            "regulation_reference": "O'zbekiston Respublikasi Adliya vazirligi 2773-son yo'riqnomasi",
            "total_products_analyzed": total_products
        },
        "summary": {
            "compliance_distribution": compliance_counts,
            "average_completion_rates": {
                "general": round(avg_general, 2),
                "required": round(avg_required, 2)
            },
            "overall_compliance_rate": round((compliance_counts['full_compliant'] / total_products * 100), 2) if total_products > 0 else 0
        },
        "section_analysis": section_statistics,
        "processing_statistics": processing_stats,
        "grafa_31_sections_reference": GRAFA_31_SECTIONS,
        "detailed_results": [
            {
                "product_id": idx + 1,
                "product_info": {
                    "name": get_product_name_safe(item),
                    "brand": item.get('product_info', {}).get('brand', '') if isinstance(item.get('product_info'), dict) else (item.get('product_info').brand if item.get('product_info') else ''),
                    "model": item.get('product_info', {}).get('model', '') if isinstance(item.get('product_info'), dict) else (item.get('product_info').model if item.get('product_info') else '')
                },
                "completion_rates": {
                    "general": get_general_rate(item),
                    "required": get_required_rate(item)
                },
                "compliance_level": item.get('compliance_level').value if hasattr(item.get('compliance_level'), 'value') else str(item.get('compliance_level')),
                "filled_sections": list(item.get('grafa_data', {}).keys()),
                "missing_sections": item.get('missing_sections', {}),
                "validation_status": item.get('is_valid', True),
                "processed_at": item.get('processed_at', '')
            }
            for idx, item in enumerate(results)
        ]
    }

def display_export_preview(results):
    """Eksport namunasini ko'rsatish"""
    st.markdown("#### 👀 Eksport Namunasi")
    
    if results:
        sample_item = results[0]
        
        # Show what will be exported
        preview_export_col1, preview_export_col2 = st.columns(2)
        
        with preview_export_col1:
            st.write("**Excel hisobotiga kiradigan ma'lumotlar:**")
            st.write("• Tovar asosiy ma'lumotlari")
            st.write("• Barcha 31-grafa bo'limlari")
            st.write("• Muvofiqlik darajalari")
            st.write("• To'ldirilish foizlari")
            st.write("• Validatsiya holati")
            st.write("• Qo'shimcha metrikalar")
        
        with preview_export_col2:
            st.write("**JSON ma'lumotlariga kiradigan ma'lumotlar:**")
            st.write("• Batafsil metadata")
            st.write("• Umumiy statistikalar")
            st.write("• Bo'limlar tahlili")
            st.write("• Jarayon statistikalari")
            st.write("• Har bir tovar uchun to'liq ma'lumot")
            st.write("• Yo'riqnoma ma'lumotnomasi")
        
        # Show sample data structure
        if st.checkbox("JSON strukturasini ko'rsatish"):
            sample_export = create_comprehensive_json_export(results[:1])
            st.json(sample_export)

def display_final_summary(results):
    """Yakuniy xulosa"""
    st.markdown("### 📋 Yakuniy Rasmiy Xulosa")
    
    total_products = len(results)
    compliant_count = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    partial_count = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT)
    non_compliant_count = total_products - compliant_count - partial_count
    
    compliance_rate = (compliant_count / total_products * 100) if total_products > 0 else 0
    
    # Executive summary based on compliance
    if compliance_rate >= 95:
        summary_class = "success-message"
        summary_icon = "🎉"
        summary_title = "MUKAMMAL NATIJA"
        summary_text = "Barcha tovarlar deyarli yo'riqnoma talablariga to'liq muvofiq! Deklaratsiya uchun tayyor."
        action_needed = "Joriy sifat nazorati tizimini saqlang va yangi tovarlar uchun ham shu darajani ta'minlang."
    elif compliance_rate >= 80:
        summary_class = "success-message"
        summary_icon = "✅"
        summary_title = "YAXSHI NATIJA"
        summary_text = "Ko'pgina tovarlar muvofiq. Qolgan tovarlar uchun qo'shimcha ishlar amalga oshiring."
        action_needed = "Qisman muvofiq va nomuvofiq tovarlarni yaxshilash uchun web search va qo'shimcha tadqiqotlar o'tkazing."
    elif compliance_rate >= 50:
        summary_class = "warning-message"
        summary_icon = "⚠️"
        summary_title = "YAXSHILASH TALAB ETILADI"
        summary_text = "Tovarlarning yarmi muvofiq. Ma'lumot to'plash jarayonini qayta ko'rib chiqish kerak."
        action_needed = "Sistemli yondashuv bilan ma'lumot manbalarini kengaytiring va texnik hujjatlarni to'ldiring."
    else:
        summary_class = "error-message"
        summary_icon = "🚨"
        summary_title = "JIDDIY YAXSHILASH KERAK"
        summary_text = "Ko'pgina tovarlar yo'riqnoma talablariga javob bermaydi."
        action_needed = "Bojxona rasmiylashtirishdan oldin jiddiy tuzatishlar amalga oshiring. Ma'lumot manbalarini to'liq qayta ko'rib chiqing."
    
    st.markdown(f"""
    <div class="{summary_class}">
        {summary_icon} <strong>{summary_title}</strong><br>
        📊 Muvofiqlik darajasi: {compliance_rate:.1f}%<br>
        📋 {summary_text}<br>
        💡 <strong>Tavsiya:</strong> {action_needed}
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed breakdown
    st.markdown(f"""
    **Rasmiy tahlil xulosasi (Adliya vazirligi 2773-son yo'riqnomasiga asosan):**
    
    📊 **Asosiy ko'rsatkichlar:**
    - **{total_products} ta tovar** tahlil qilindi
    - **{compliant_count} ta tovar** to'liq muvofiq (majburiy bo'limlar 100%)
    - **{partial_count} ta tovar** qisman muvofiq (majburiy bo'limlar 80-99%)
    - **{non_compliant_count} ta tovar** nomuvofiq (majburiy bo'limlar 80% dan kam)
    
    ⚖️ **Yo'riqnomaga muvofiqlik:**
    - Umumiy muvofiqlik darajasi: **{compliance_rate:.1f}%**
    - Bojxona rasmiylashtirishiga tayyor: **{compliant_count} ta tovar**
    - Qo'shimcha ishlar talab etiladi: **{partial_count + non_compliant_count} ta tovar**
    
    📅 **Tahlil sanasi:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    📋 **Tizim versiyasi:** 31-Grafa Enhanced Analysis System v2.0
    """)

def display_trends_tab(results):
    """Tendentsiyalar bo'limi"""
    st.markdown("### 📈 Tendentsiyalar va Tahlil")
    
    # Quality distribution analysis
    display_quality_distribution(results)
    
    # Content analysis
    display_content_analysis(results)
    
    # Predictive insights
    display_predictive_insights(results)

def display_quality_distribution(results):
    """Sifat taqsimoti tahlili"""
    st.markdown("#### 📊 Sifat Taqsimoti Tahlili")
    
    # Analyze content quality across sections
    section_quality = {}
    
    for section_key, section_info in GRAFA_31_SECTIONS.items():
        content_lengths = []
        filled_count = 0
        
        for item in results:
            grafa_data = item.get('grafa_data', {})
            if section_key in grafa_data:
                filled_count += 1
                content = str(grafa_data[section_key])
                content_lengths.append(len(content))
        
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            min_length = min(content_lengths)
            max_length = max(content_lengths)
            
            # Quality assessment
            if avg_length >= 100 and filled_count >= len(results) * 0.8:
                quality_score = "A'lo"
                quality_color = "#059669"
            elif avg_length >= 50 and filled_count >= len(results) * 0.6:
                quality_score = "Yaxshi"
                quality_color = "#D97706"
            elif avg_length >= 20 and filled_count >= len(results) * 0.4:
                quality_score = "O'rtacha"
                quality_color = "#DC2626"
            else:
                quality_score = "Past"
                quality_color = "#991B1B"
        else:
            avg_length = min_length = max_length = 0
            quality_score = "Ma'lumot yo'q"
            quality_color = "#6B7280"
        
        section_quality[section_key] = {
            'name': section_info['name'],
            'filled_count': filled_count,
            'avg_length': avg_length,
            'min_length': min_length,
            'max_length': max_length,
            'quality_score': quality_score,
            'quality_color': quality_color,
            'required': section_info.get('required', False)
        }
    
    # Display quality metrics
    quality_col1, quality_col2 = st.columns(2)
    
    with quality_col1:
        st.write("**Eng Yaxshi Sifatli Bo'limlar:**")
        best_sections = sorted(section_quality.items(), key=lambda x: x[1]['avg_length'], reverse=True)[:5]
        
        for section_key, data in best_sections:
            st.markdown(f"""
            <div style="background: {data['quality_color']}20; padding: 8px; border-radius: 4px; margin: 4px 0;">
                <strong>{data['name'][:50]}{'...' if len(data['name']) > 50 else ''}</strong><br>
                <small>Sifat: {data['quality_score']} | O'rtacha: {data['avg_length']:.0f} belgi</small>
            </div>
            """, unsafe_allow_html=True)
    
    with quality_col2:
        st.write("**Yaxshilanishi Kerak Bo'limlar:**")
        worst_sections = sorted(section_quality.items(), key=lambda x: x[1]['avg_length'])[:5]
        
        for section_key, data in worst_sections:
            if data['filled_count'] > 0:  # Only show sections that have some data
                st.markdown(f"""
                <div style="background: {data['quality_color']}20; padding: 8px; border-radius: 4px; margin: 4px 0;">
                    <strong>{data['name'][:50]}{'...' if len(data['name']) > 50 else ''}</strong><br>
                    <small>Sifat: {data['quality_score']} | O'rtacha: {data['avg_length']:.0f} belgi</small>
                </div>
                """, unsafe_allow_html=True)

def display_content_analysis(results):
    """Tarkib tahlili"""
    st.markdown("#### 📝 Tarkib Tahlili")
    
    # Analyze common patterns and issues
    total_products = len(results)
    
    # Common missing patterns
    missing_patterns = {}
    for item in results:
        missing = item.get('missing_sections', {}).get('required', [])
        if missing:
            pattern = tuple(sorted(missing))
            missing_patterns[pattern] = missing_patterns.get(pattern, 0) + 1
    
    if missing_patterns:
        st.write("**Umumiy Yetishmayotgan Bo'limlar Naqshlari:**")
        
        # Show top 3 most common missing patterns
        top_patterns = sorted(missing_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for pattern, count in top_patterns:
            percentage = (count / total_products * 100)
            section_names = [GRAFA_31_SECTIONS[key]['name'][:30] for key in pattern]
            
            st.write(f"• **{count} ta tovar ({percentage:.1f}%)** da yetishmaydi:")
            for name in section_names:
                st.write(f"  - {name}{'...' if len(name) == 30 else ''}")
    
    # Content quality insights
    st.markdown("#### 💡 Tarkib Sifati Xulosalari")
    
    insights = []
    
    # Check for very short content
    short_content_count = 0
    for item in results:
        grafa_data = item.get('grafa_data', {})
        for content in grafa_data.values():
            if len(str(content)) < 20:
                short_content_count += 1
                break
    
    if short_content_count > total_products * 0.3:
        insights.append(f"⚠️ {short_content_count} ta tovar juda qisqa ma'lumotlarga ega")
    
    # Check for missing required sections
    critical_missing = 0
    for item in results:
        if item.get('missing_sections', {}).get('required', []):
            critical_missing += 1
    
    if critical_missing > total_products * 0.2:
        insights.append(f"🚨 {critical_missing} ta tovarda majburiy bo'limlar yetishmaydi")
    
    # Check for good compliance
    excellent_products = sum(1 for item in results if get_required_rate(item) >= 95)
    if excellent_products > total_products * 0.7:
        insights.append(f"✅ {excellent_products} ta tovar a'lo darajada muvofiq")
    
    for insight in insights:
        st.write(insight)

def display_predictive_insights(results):
    """Bashoratli tahlillar"""
    st.markdown("#### 🔮 Bashoratli Tahlillar")
    
    total_products = len(results)
    
    # Predict completion timeline
    missing_work = sum(len(item.get('missing_sections', {}).get('all', [])) for item in results)
    
    # Estimate time needed
    if missing_work > 0:
        # Assume 10 minutes per missing section on average
        estimated_hours = (missing_work * 10) / 60
        estimated_days = estimated_hours / 8  # 8 hours per work day
        
        st.info(f"📅 **Baholangan vaqt**: {missing_work} ta yetishmayotgan bo'limni to'ldirish uchun "
                f"taxminan {estimated_days:.1f} ish kuni ({estimated_hours:.1f} soat) kerak bo'ladi")
    
    # Resource recommendations
    high_priority_products = sum(1 for item in results 
                                if item.get('compliance_level') == ComplianceLevel.NON_COMPLIANT)
    
    if high_priority_products > 0:
        st.warning(f"🎯 **Ustuvorlik**: Birinchi navbatda {high_priority_products} ta kritik tovarga e'tibor bering")
    
    # Success probability
    current_compliance = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.FULL_COMPLIANT)
    partial_compliance = sum(1 for item in results if item.get('compliance_level') == ComplianceLevel.PARTIAL_COMPLIANT)
    
    # Estimate how many partial can become full compliant
    potential_full = partial_compliance * 0.7  # Assume 70% of partial can become full
    projected_compliance = (current_compliance + potential_full) / total_products * 100
    
    st.success(f"📈 **Prognoz**: Qo'shimcha ishlar bilan {projected_compliance:.1f}% muvofiqlikga erishish mumkin")

def show_no_data_warning(redirect_page):
    """Ma'lumot yo'q ogohlantirishi"""
    st.warning("⚠️ Avval kerakli ma'lumotlarni tayyorlang!")
    
    if redirect_page == 'upload':
        message = "JSON fayl yuklang"
        button_text = "📁 Fayl Yuklash Sahifasiga O'tish"
    elif redirect_page == 'analysis':
        message = "Tovarlarni tahlil qiling"
        button_text = "🔍 Tahlil Sahifasiga O'tish"
    else:
        message = "Avvalgi bosqichlarni bajaring"
        button_text = "🏠 Bosh Sahifaga O'tish"
    
    st.info(f"💡 {message}")
    
    if st.button(button_text, use_container_width=True):
        st.session_state.current_page = redirect_page
        st.rerun()

# Main execution
if __name__ == "__main__":
    main()
    
    with col2:
        st.markdown(f"""
        <div class="grafa-section" style="background: #fef3c7; border-left-color: #D97706;">
            <h4>🟡 QISMAN MUVOFIQ</h4>
            <p><strong>{len(partial)} ta tovar ({(len(partial)/total_products*100):.1f}%)</strong></p>
            <p>80-99% majburiy bo'limlar to'ldirilgan</p>
            <p>Qo'shimcha ma'lumotlar talab etiladi</p>
        </div>
        """, unsafe_allow_html=True)
        
        if partial:
            st.write("**Yaxshilanishi kerak bo'lgan tovarlar:**")
            for item in sorted(partial, key=get_required_rate, reverse=True)[:3]:
                name = get_product_name_safe(item)
                required_rate = get_required_rate(item)
                st.write(f"• {name[:40]}{'...' if len(name) > 40 else ''} ({required_rate:.1f}%)")
    
    with col3:
        st.markdown(f"""
        <div class="grafa-section missing-section">
            <h4>🔴 NOMUVOFIQ</h4>
            <p><strong>{len(non_compliant)} ta tovar ({(len(non_compliant)/total_products*100):.1f}%)</strong></p>
            <p>80% dan kam majburiy bo'limlar</p>
            <p>Jiddiy tuzatishlar kerak</p>
        </div>
        """, unsafe_allow_html=True)
        
        if non_compliant:
            st.write("**Eng kam muvofiq tovarlar:**")
            for item in sorted(non_compliant, key=get_required_rate)[:3]:
                name = get_product_name_safe(item)
                required_rate = get_required_rate(item)
                st.write(f"• {name[:40]}{'...' if len(name) > 40 else ''} ({required_rate:.1f}%)")

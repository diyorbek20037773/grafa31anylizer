import streamlit as st
import json
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
from difflib import SequenceMatcher
import io
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
import xlsxwriter
import openpyxl
import urllib.parse
from collections import Counter
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
warnings.filterwarnings('ignore')

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="Grafa31 Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    * {
        font-family: Verdana, Geneva, Tahoma, sans-serif !important;
    }
    
    .main-header {
        color: #2275AC !important;
        text-align: center;
        font-size: 4rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        letter-spacing: -2px;
        position: relative;
        font-family: 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif !important;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 200px;
        height: 4px;
        background: linear-gradient(90deg, #2275AC, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    .sub-header {
        text-align: center;
        color: #2275AC;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-bottom: 2rem;
        font-family: Verdana, Geneva, Tahoma, sans-serif !important;
    }
    
    .stButton > button {
        width: 90% !important;
        height: 60px !important;
        border: none !important;
        outline: none !important;
        color: #fff !important;
        background: #111 !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 0 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        margin: 10px auto !important;
        display: block !important;
    }
    
    .stButton > button:before {
        content: '';
        background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
        position: absolute;
        top: -2px;
        left: -2px;
        background-size: 400%;
        z-index: -1;
        filter: blur(5px);
        width: calc(100% + 4px);
        height: calc(100% + 4px);
        animation: glowing 20s linear infinite;
        opacity: 0;
        transition: opacity .3s ease-in-out;
        border-radius: 10px;
    }
    
    .stButton > button:hover:before {
        opacity: 1 !important;
    }
    
    .stButton > button:after {
        z-index: -1;
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background: greenyellow;
        left: 0;
        top: 0;
        border-radius: 10px;
    }
    
    @keyframes glowing {
        0% { background-position: 0 0; }
        50% { background-position: 400% 0; }
        100% { background-position: 0 0; }
    }
    
    .search-progress {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .success-message {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(90deg, #dc3545, #e83e8c);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    .nav-button {
        background: #2275AC;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        margin: 5px 0;
        cursor: pointer;
        width: 100%;
        text-align: left;
        font-weight: 600;
    }
    
    .nav-button:hover {
        background: #1a5a8a;
    }
    
    .nav-button.active {
        background: #28a745;
    }
    
    .logo-container {
        text-align: center;
        margin-top: 20px;
        position: relative;
    }
    
    .logo-container img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        border: 4px solid #fff;
        background: white;
        padding: 2px;
        transition: transform 0.3s ease;
    }
    
    .logo-container img:hover {
        transform: scale(1.05);
    }
    
    .logo-container::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 80px;
        height: 3px;
        background: linear-gradient(90deg, #4caf50, #2275AC);
        border-radius: 2px;
    }
    
    .logo-container::before {
        content: '';
        position: absolute;
        top: -5px;
        left: 50%;
        transform: translateX(-50%);
        width: 110px;
        height: 110px;
        border: 2px solid #4caf50;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: translateX(-50%) scale(1); opacity: 1; }
        100% { transform: translateX(-50%) scale(1.1); opacity: 0; }
    }
    
    .logo-container::after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, #2275AC, #667eea);
        border-radius: 2px;
    }
    
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# NLTK ma'lumotlarini yuklab olish
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)

download_nltk_data()

# Serper API konfiguratsiyasi
SERPER_API_KEYS = [
    "f73aaf81a1604fc9270c38b7b7f47b9ad9e90fca",
    "4f13f583cdbb95a1771adcd2f091ab3ec1bc49b8"
]

SERPER_URL = "https://google.serper.dev/search"

# 31-grafa bo'limlari (Rus va O'zbek tillarida)
GRAFA_SECTIONS_MULTILINGUAL = {
    "tovar_nomi": {
        "name": "1. Tovar nomi, turi",
        "name_ru": "1. Наименование товара",
        "description": "Mahsulotning aniq nomi va turi",
        "keywords": {
            "ru": ["наименование", "название", "товар", "продукт", "изделие", "тип", "вид", "модель", "артикул", "код", "марка", "автомобиль", "легковой", "электромобиль", "машина"],
            "uz": ["nomi", "mahsulot", "tovar", "model", "marka", "avtomobil"]
        },
        "json_fields": {
            "ru": ["наименование_товара", "название_товара", "товар", "продукт", "изделие", "наименование", "название", "модель", "артикул", "код"],
            "uz": ["tovar_nomi", "mahsulot_nomi", "nomi", "model"]
        },
        "search_terms": ["наименование товара", "название продукта", "модель автомобиля", "тип машины"],
        "priority": 10
    },
    "o_ram_turi": {
        "name": "2. O'ram turi",
        "name_ru": "2. Вид упаковки",
        "description": "Mahsulotning qadoqlash turi",
        "keywords": {
            "ru": ["упаковка", "упаковочный", "тара", "контейнер", "коробка", "пакет", "бутылка", "банка", "мешок", "ящик"],
            "uz": ["o'ram", "qadoq", "paket", "quti"]
        },
        "json_fields": {
            "ru": ["упаковка", "тара", "контейнер", "коробка", "пакет", "бутылка", "упаковочный_материал", "вид_упаковки"],
            "uz": ["oram", "qadoq", "paket"]
        },
        "search_terms": ["упаковка автомобиля", "как упаковывают", "контейнер доставки", "тара транспорта"],
        "priority": 6
    },
    "materiali": {
        "name": "3. Materiali",
        "name_ru": "3. Материал",
        "description": "Mahsulot ishlab chiqarilgan material",
        "keywords": {
            "ru": ["материал", "изготовлен", "состав", "сырье", "вещество", "сделан", "пластик", "металл", "дерево", "стекло", "ткань", "хлопок", "полиэстер", "алюминий", "сталь", "железо", "резина", "кожа", "бумага"],
            "uz": ["material", "tarkib", "modda", "plastik", "metall"]
        },
        "json_fields": {
            "ru": ["материал", "состав", "сырье", "вещество", "материал_изготовления", "основной_материал"],
            "uz": ["material", "tarkib", "modda"]
        },
        "search_terms": ["материал изготовления автомобиля", "из чего сделан", "состав машины", "металл кузова"],
        "priority": 8
    },
    "ishlab_chiqarish_texnologiyasi": {
        "name": "4. Ishlab chiqarish texnologiyasi",
        "name_ru": "4. Технология производства",
        "description": "Ishlab chiqarish usuli va texnologiyasi",
        "keywords": {
            "ru": ["технология", "производство", "изготовление", "метод", "способ", "технологический", "процесс", "обработка", "формование", "сварка", "штамповка"],
            "uz": ["texnologiya", "ishlab_chiqarish", "usul", "jarayon"]
        },
        "json_fields": {
            "ru": ["технология", "производство", "изготовление", "метод", "способ_производства", "технология_изготовления"],
            "uz": ["texnologiya", "ishlab_chiqarish", "usul"]
        },
        "search_terms": ["технология производства автомобиля", "как изготавливают", "метод сборки", "процесс производства"],
        "priority": 5
    },
    "ishlatilish_maqsadi": {
        "name": "5. Ishlatilish maqsadi",
        "name_ru": "5. Назначение",
        "description": "Mahsulotning ishlatilish maqsadi",
        "keywords": {
            "ru": ["назначение", "применение", "использование", "цель", "предназначен", "используется", "применяется", "служит", "функция", "область_применения"],
            "uz": ["maqsad", "ishlatish", "foydalanish", "vazifa"]
        },
        "json_fields": {
            "ru": ["назначение", "применение", "использование", "цель", "область_применения", "функция", "предназначение"],
            "uz": ["maqsad", "ishlatish", "foydalanish"]
        },
        "search_terms": ["назначение автомобиля", "для чего используется", "цель применения", "функция машины"],
        "priority": 7
    },
    "tovar_ishlatiladigan_sanoat": {
        "name": "6. Tovar ishlatiladigan sanoat",
        "name_ru": "6. Отрасль применения",
        "description": "Mahsulot qo'llaniladigan sanoat sohasi",
        "keywords": {
            "ru": ["отрасль", "сфера", "область", "индустрия", "промышленность", "сектор", "автомобильная", "пищевая", "текстильная", "строительная", "электронная", "медицинская", "химическая"],
            "uz": ["sanoat", "soha", "tarmoq", "avtomobil", "oziq-ovqat"]
        },
        "json_fields": {
            "ru": ["отрасль", "сфера", "область", "индустрия", "промышленность", "сектор_применения"],
            "uz": ["sanoat", "soha", "tarmoq"]
        },
        "search_terms": ["автомобильная промышленность", "транспортная отрасль", "сфера применения", "индустрия"],
        "priority": 4
    },
    "ishlab_chiqaruvchi": {
        "name": "7. Ishlab chiqaruvchi",
        "name_ru": "7. Производитель",
        "description": "Mahsulot ishlab chiqaruvchi kompaniya",
        "keywords": {
            "ru": ["производитель", "изготовитель", "завод", "фабрика", "компания", "фирма", "предприятие", "организация", "корпорация", "бренд"],
            "uz": ["ishlab_chiqaruvchi", "zavod", "kompaniya", "firma"]
        },
        "json_fields": {
            "ru": ["производитель", "изготовитель", "завод", "фабрика", "компания", "место_происхождения", "страна_производитель", "бренд", "название_бренда"],
            "uz": ["ishlab_chiqaruvchi", "zavod", "kompaniya", "brend"]
        },
        "search_terms": ["производитель автомобиля", "завод изготовитель", "компания производитель", "бренд машины"],
        "priority": 8
    },
    "savdo_belgisi": {
        "name": "8. Savdo belgisi",
        "name_ru": "8. Товарный знак",
        "description": "Tovar markasi va brendi",
        "keywords": {
            "ru": ["бренд", "марка", "торговая_марка", "товарный_знак", "логотип", "знак", "торговый_знак", "фирменный_знак"],
            "uz": ["brend", "marka", "savdo_belgisi", "logotip"]
        },
        "json_fields": {
            "ru": ["бренд", "марка", "торговая_марка", "товарный_знак", "название_бренда", "логотип", "знак"],
            "uz": ["brend", "marka", "savdo_belgisi"]
        },
        "search_terms": ["товарный знак автомобиля", "бренд машины", "марка авто", "логотип"],
        "priority": 7
    },
    "texnik_xususiyatlar": {
        "name": "9. Texnik xususiyatlar",
        "name_ru": "9. Технические характеристики",
        "description": "Mahsulotning texnik parametrlari",
        "keywords": {
            "ru": ["характеристики", "параметры", "спецификация", "свойства", "показатели", "размеры", "вес", "мощность", "напряжение", "частота", "температура", "давление", "скорость", "производительность", "емкость", "технические", "двигатель", "объем"],
            "uz": ["xususiyat", "parametr", "ko'rsatkich", "o'lcham", "og'irlik"]
        },
        "json_fields": {
            "ru": ["характеристики", "параметры", "спецификация", "свойства", "технические_характеристики", "стандарт", "размеры", "вес", "дополнительные_измерения_и_показатели"],
            "uz": ["xususiyat", "parametr", "ko'rsatkich"]
        },
        "search_terms": ["технические характеристики автомобиля", "параметры машины", "объем двигателя", "мощность авто"],
        "priority": 9
    },
    "ishlab_chiqarilgan_yil": {
        "name": "10. Ishlab chiqarilgan yil",
        "name_ru": "10. Дата изготовления",
        "description": "Mahsulot ishlab chiqarilgan sana",
        "keywords": {
            "ru": ["дата", "год", "изготовления", "производства", "выпуска", "выпущен", "произведен", "изготовлен", "дата_выпуска", "год_выпуска"],
            "uz": ["sana", "yil", "ishlab_chiqarilgan", "tayyorlangan"]
        },
        "json_fields": {
            "ru": ["дата_изготовления", "год_производства", "дата_выпуска", "год", "дата_производства", "год_изготовления"],
            "uz": ["ishlab_chiqarilgan_sana", "yil", "sana"]
        },
        "search_terms": ["дата изготовления автомобиля", "год выпуска машины", "когда произведен", "год производства"],
        "priority": 5
    },
    "tovar_kodi": {
        "name": "11. Tovar kodi (modeli, versiyasi)",
        "name_ru": "11. Код товара (модель, версия)",
        "description": "Mahsulot kodi, modeli, versiyasi",
        "keywords": {
            "ru": ["модель", "код", "артикул", "версия", "серия", "номер", "индекс", "обозначение", "каталожный_номер", "серийный_номер"],
            "uz": ["model", "kod", "versiya", "seria", "raqam"]
        },
        "json_fields": {
            "ru": ["модель", "код", "артикул", "версия", "серия", "номер_позиции", "каталожный_номер", "серийный_номер"],
            "uz": ["model", "kod", "versiya", "seria"]
        },
        "search_terms": ["модель автомобиля", "код машины", "артикул авто", "версия модели"],
        "priority": 6
    }
}

# HS kodlar bazasi
HS_CODES_DATABASE = {
    "8703": "Легковые автомобили и прочие моторные транспортные средства",
    "8471": "Автоматик маълумотларни қайта ишлаш машиналари",
    "8517": "Телефон аппаратлари, радио-телефон аппаратлари",
    "8528": "Мониторлар ва проекторлар, телевизорлар",
    "8414": "Ҳаво ёки вакуум насослари, компрессорлар",
    "8418": "Музлаткичлар, музхона анжомлари",
    "8443": "Принтерлар, копир машиналари",
    "9403": "Бошқа мебеллар ва уларнинг қисмлари",
    "3926": "Пластмасса буюмлари"
}

class SerperAPIClient:
    """Serper API bilan ishlash uchun sinf"""
    
    def __init__(self):
        self.api_keys = SERPER_API_KEYS
        self.current_key_index = 0
        self.base_url = SERPER_URL
        
    def get_next_api_key(self):
        """Navbatdagi API kalitni olish"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def google_search(self, query):
        """Google orqali qidiruv Serper API orqali"""
        headers = {
            "X-API-KEY": self.get_next_api_key(),
            "Content-Type": "application/json"
        }
        
        data = {"q": query}
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            # Birinchi natijaning snippet qismini olish
            snippet = results.get("organic", [{}])[0].get("snippet", "not found")
            return snippet
            
        except requests.exceptions.RequestException as e:
            st.warning(f"API xatosi: {str(e)}")
            return "not found"
        except Exception as e:
            st.error(f"Umumiy xato: {str(e)}")
            return "not found"

class TextAnalyzer:
    def __init__(self):
        self.stemmers = {
            'russian': SnowballStemmer('russian'),
            'english': SnowballStemmer('english')
        }
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        
    def detect_language(self, text):
        """Matn tilini aniqlash"""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Rus tilini aniqlash
        russian_chars = re.findall(r'[а-яё]', text_lower)
        # Ingliz tilini aniqlash
        english_chars = re.findall(r'[a-z]', text_lower)
        
        total_chars = len(re.findall(r'[а-яёa-z]', text_lower))
        
        if total_chars == 0:
            return 'unknown'
        
        russian_ratio = len(russian_chars) / total_chars
        english_ratio = len(english_chars) / total_chars
        
        if russian_ratio > 0.3:
            return 'ru'
        elif english_ratio > 0.5:
            return 'en'
        else:
            return 'ru'  # Default to Russian
    
    def preprocess_text(self, text, language='ru'):
        """Matnni oldindan qayta ishlash"""
        if not text:
            return ""
        
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        try:
            tokens = word_tokenize(text)
        except:
            tokens = text.split()
        
        # Stop so'zlarni o'chirish
        try:
            if language == 'ru':
                stop_words = set(stopwords.words('russian'))
            elif language == 'en':
                stop_words = set(stopwords.words('english'))
            else:
                stop_words = set()
        except:
            stop_words = set()
        
        # Avtomobil sohasiga oid stop so'zlar
        automotive_stopwords = {'шт', 'кг', 'см3', 'год', 'not', 'specified', 'г.в.', 'года', 'производства'}
        stop_words.update(automotive_stopwords)
        
        tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
        
        # Stemming
        if language in self.stemmers:
            stemmer = self.stemmers[language]
            tokens = [stemmer.stem(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def calculate_similarity(self, text1, text2):
        """Matnlar o'xshashligini hisoblash"""
        try:
            lang1 = self.detect_language(text1)
            lang2 = self.detect_language(text2)
            
            lang = lang1 if lang1 != 'unknown' else lang2
            
            texts = [self.preprocess_text(text1, lang), self.preprocess_text(text2, lang)]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def analyze_text_for_section(self, text, section_key):
        """Matnni bo'limga tegishliligini tahlil qilish"""
        if not text or not section_key:
            return 0, []
        
        section_data = GRAFA_SECTIONS_MULTILINGUAL[section_key]
        score = 0
        matched_keywords = []
        
        text_lower = text.lower()
        detected_lang = self.detect_language(text)
        
        # Aniqlangan tilga mos kalit so'zlarni olish
        if detected_lang in section_data["keywords"]:
            keywords = section_data["keywords"][detected_lang]
        else:
            keywords = []
            for lang_keywords in section_data["keywords"].values():
                keywords.extend(lang_keywords)
        
        # Kalit so'zlarni qidirish
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                score += 2
                matched_keywords.append(keyword)
            elif any(SequenceMatcher(None, keyword_lower, word).ratio() > 0.8 
                    for word in text_lower.split()):
                score += 1
                matched_keywords.append(f"fuzzy:{keyword}")
        
        # Pattern matching rus tili uchun
        if detected_lang == 'ru':
            patterns = [
                r"модел.*", r"код.*", r"артикул.*", r"верси.*", r"сери.*",
                r"производител.*", r"изготовител.*", r"завод.*", r"фабрик.*",
                r"материал.*", r"состав.*", r"технолог.*", r"производств.*"
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 3
                    matched_keywords.append(f"pattern:{pattern}")
        
        # TF-IDF similarity
        keywords_text = ' '.join(keywords)
        similarity = self.calculate_similarity(text, keywords_text)
        score += similarity * 5
        
        # Priority weight
        score *= section_data["priority"] / 10
        
        return score, matched_keywords

class NotSpecifiedFiller:
    """Not specified maydonlarni to'ldirish uchun sinf"""
    
    def __init__(self):
        self.serper_client = SerperAPIClient()
        self.text_analyzer = TextAnalyzer()
    
    def find_not_specified_fields(self, product):
        """Mahsulotda 'not specified' maydonlarni topish"""
        not_specified_fields = []
        
        for key, value in product.items():
            if isinstance(value, str) and ("not specified" in value.lower() or "не указано" in value.lower() or "не указан" in value.lower()):
                not_specified_fields.append(key)
        
        return not_specified_fields
    
    def create_search_query(self, product, field_name):
        """Maydon uchun qidiruv so'rovini yaratish"""
        product_name = product.get('наименование_товара', product.get('товар', ''))
        brand = product.get('название_бренда', '')
        model = product.get('модель', '')
        
        if not product_name:
            return f"{field_name}"
        
        # Asosiy so'rovni yaratish
        query = f"{product_name} {brand} {model} {field_name}".strip()
        
        return query
    
    def fill_not_specified_field(self, product, field_name, progress_container=None):
        """Bitta 'not specified' maydonni to'ldirish"""
        query = self.create_search_query(product, field_name)
        
        if progress_container:
            progress_container.write(f"🔍 Qidirilmoqda: {query}")
        
        # Serper API orqali qidiruv
        snippet = self.serper_client.google_search(query)
        
        if progress_container:
            if snippet != "not found":
                progress_container.write(f"✅ Topildi: {snippet[:100]}...")
            else:
                progress_container.write(f"❌ Topilmadi: {field_name}")
        
        return snippet
    
    def fill_all_not_specified_fields(self, product, progress_container=None):
        """Barcha 'not specified' maydonlarni to'ldirish"""
        not_specified_fields = self.find_not_specified_fields(product)
        
        if not not_specified_fields:
            if progress_container:
                progress_container.write("✅ Barcha maydonlar allaqachon to'ldirilgan!")
            return product
        
        if progress_container:
            progress_container.write(f"📋 {len(not_specified_fields)} ta 'not specified' maydon topildi")
        
        filled_product = product.copy()
        
        for field_name in not_specified_fields:
            if progress_container:
                progress_container.write(f"🔄 Maydon: {field_name}")
            
            snippet = self.fill_not_specified_field(filled_product, field_name, progress_container)
            
            if snippet != "not found":
                filled_product[field_name] = snippet
            
            # Rate limiting
            time.sleep(1.2)
        
        return filled_product
    
    def process_products_list(self, products, progress_container=None):
        """Ko'plab tovarlarni qayta ishlash"""
        if progress_container:
            progress_container.write(f"🚀 {len(products)} ta tovar qayta ishlanmoqda...")
        
        cleaned_products = []
        
        for idx, product in enumerate(products):
            if progress_container:
                progress_container.write(f"\n📦 Tovar {idx + 1}/{len(products)}")
            
            filled_product = self.fill_all_not_specified_fields(product, progress_container)
            cleaned_products.append(filled_product)
        
        return cleaned_products

class DataAnalyzer:
    def __init__(self):
        self.text_analyzer = TextAnalyzer()
        self.not_specified_filler = NotSpecifiedFiller()
    
    def analyze_single_product(self, data, product_id):
        """Bitta tovarni tahlil qilish va 31-Grafa bo'limlariga taqsimlash"""
        filled_sections = {}
        confidence_scores = {}
        
        # Ma'lumot turini aniqlash
        if isinstance(data, dict):
            product_data = data
        else:
            st.error("Ma'lumot dictionary formatida emas!")
            return {}, [], {}
        
        # Tovar ma'lumotlarini ko'rsatish
        product_name = product_data.get('наименование_товара', product_data.get('товар', 'Noma\'lum'))
        brand = product_data.get('название_бренда', product_data.get('бренд', ''))
        model = product_data.get('модель', '')
        
        # Har bir maydonni 31-Grafa bo'limlariga taqsimlash
        for field_name, value in product_data.items():
            if not value or str(value).strip() in ['', 'not specified', 'не указано', 'не указан']:
                continue
                
            value_str = str(value).strip()
            if len(value_str) < 2:
                continue
            
            # Matn tilini aniqlash
            detected_lang = self.text_analyzer.detect_language(value_str)
            
            # Har bir 31-Grafa bo'limini tekshirish
            best_section = None
            best_score = 0
            
            for section_key, section_data in GRAFA_SECTIONS_MULTILINGUAL.items():
                score = 0
                
                # 1. Maydon nomi bo'yicha to'g'ridan-to'g'ri moslik
                field_lower = field_name.lower()
                json_fields = section_data["json_fields"].get(detected_lang, [])
                for lang, fields in section_data["json_fields"].items():
                    json_fields.extend(fields)
                
                for json_field in json_fields:
                    if json_field.lower() in field_lower or field_lower in json_field.lower():
                        score += 30  # Yuqori ball
                        break
                
                # 2. Aniq mos kelishlar
                exact_matches = {
                    'tovar_nomi': ['наименование_товара', 'название_товара', 'товар'],
                    'savdo_belgisi': ['товарный_знак', 'торговая_марка', 'бренд', 'марка', 'название_бренда'],
                    'tovar_kodi': ['модель', 'код', 'артикул'],
                    'texnik_xususiyatlar': ['технические_характеристики', 'характеристики', 'дополнительные_измерения_и_показатели', 'стандарт'],
                    'ishlab_chiqarilgan_yil': ['дата_изготовления', 'год_производства', 'дата_выпуска'],
                    'ishlab_chiqaruvchi': ['производитель', 'изготовитель', 'место_происхождения'],
                    'materiali': ['материал', 'состав', 'состав_качества'],
                    'o_ram_turi': ['упаковка', 'тара', 'единица_измерения', 'количество'],
                    'ishlatilish_maqsadi': ['назначение', 'применение', 'использование'],
                    'tovar_ishlatiladigan_sanoat': ['отрасль', 'сфера', 'область', 'промышленность'],
                    'ishlab_chiqarish_texnologiyasi': ['технология', 'производство', 'изготовление', 'класс_энергоэффективности']
                }
                
                if section_key in exact_matches:
                    for exact_field in exact_matches[section_key]:
                        if exact_field in field_lower:
                            score += 40  # Eng yuqori ball
                            break
                
                # 3. Matn mazmuni bo'yicha tahlil
                content_score, matched_keywords = self.text_analyzer.analyze_text_for_section(value_str, section_key)
                score += content_score
                
                # 4. Priority weight
                score *= section_data["priority"] / 10
                
                # Eng yaxshi bo'limni tanlash
                if score > best_score:
                    best_score = score
                    best_section = section_key
            
            # Natijani saqlash (faqat ishonchli natijalarni)
            if best_section and best_score > 5:  # Minimal threshold
                if best_section not in filled_sections or best_score > confidence_scores.get(best_section, 0):
                    filled_sections[best_section] = value_str
                    confidence_scores[best_section] = best_score
        
        # Yetishmayotgan bo'limlarni aniqlash
        missing_sections = [key for key in GRAFA_SECTIONS_MULTILINGUAL.keys() if key not in filled_sections]
        
        return filled_sections, missing_sections, confidence_scores

def read_uploaded_file(uploaded_file):
    """Yuklangan faylni o'qish"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'json':
            json_data = json.load(uploaded_file)
            return json_data, 'json'
        else:
            st.error(f"Faqat JSON formatlar qo'llab-quvvatlanadi: {file_extension}")
            return None, None
    except Exception as e:
        st.error(f"Faylni o'qishda xatolik: {str(e)}")
        return None, None

def create_completion_charts(filled_sections, missing_sections):
    """To'ldirilish diagrammalarini yaratish"""
    total_sections = len(GRAFA_SECTIONS_MULTILINGUAL)
    filled_count = len(filled_sections)
    missing_count = len(missing_sections)
    
    # Donut diagramma
    fig_pie = go.Figure(data=[go.Pie(
        labels=['To\'ldirilgan', 'Yetishmayotgan'],
        values=[filled_count, missing_count],
        marker_colors=['#28a745', '#dc3545'],
        textinfo='label+percent+value',
        textfont_size=14,
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>Soni: %{value}<br>Foiz: %{percent}<extra></extra>'
    )])
    
    fig_pie.update_layout(
        title={
            'text': "31-Grafa Ma'lumotlari To'ldirilishi",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2275AC', 'family': 'Verdana'}
        },
        font=dict(size=14, family='Verdana'),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=True
    )
    
    return fig_pie

def export_to_excel(all_results):
    """Excel formatga eksport qilish"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_data = []
            
            for idx, result in enumerate(all_results):
                product_data = result['product_info']
                filled_sections = result['filled_sections']
                
                # Har bir tovar uchun qator yaratish
                row = {
                    'Tovar_ID': idx + 1,
                    'Tovar_Nomi': product_data.get('наименование_товара', ''),
                    'Brend': product_data.get('название_бренда', ''),
                    'Model': product_data.get('модель', ''),
                }
                
                # 31-Grafa bo'limlarini qo'shish
                for section_key, section_data in GRAFA_SECTIONS_MULTILINGUAL.items():
                    column_name = section_data['name']
                    row[column_name] = filled_sections.get(section_key, '')
                
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            df.to_excel(writer, sheet_name='31-Grafa Tahlil', index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        st.error(f"Excel eksport xatosi: {str(e)}")
        return None

def main():
    # Session state ni boshlash
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'data_upload'
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = DataAnalyzer()

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.empty()  # Bo'sh joy
    
    with col2:
        st.markdown('<h1 class="main-header">📊 Grafa31 Analyzer</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Bojxona Auditi Boshqarmasi</p>', unsafe_allow_html=True)
    
    with col3:
        # Bojxona Auditi Boshqarmasi Logo
        st.markdown("""
        <div class="logo-container">
            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ3JlZW5HcmFkaWVudCIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzRjYWY1MDtzdG9wLW9wYWNpdHk6MSIgLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMzg4ZTNjO3N0b3Atb3BhY2l0eToxIiAvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxyYWRpYWxHcmFkaWVudCBpZD0iZWFydGhHcmFkaWVudCI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNlM2Y2ZmQ7c3RvcC1vcGFjaXR5OjEiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzllZTRmNDtzdG9wLW9wYWNpdHk6MSIgLz4KICAgIDwvcmFkaWFsR3JhZGllbnQ+CiAgPC9kZWZzPgogIAogIDwhLS0gWXVsZHV6c2ltb24gZm9uIC0tPgogIDxwb2x5Z29uIHBvaW50cz0iNjAsNSA3NSwyNSA5NSwyNSA4MCw0NSA4NSw2NSA2MCw1NSAzNSw2NSA0MCw0NSAyNSwyNSA0NSwyNSIgZmlsbD0iI2NjYyIgc3Ryb2tlPSIjOTk5IiBzdHJva2Utd2lkdGg9IjIiLz4KICA8cG9seWdvbiBwb2ludHM9IjYwLDEwIDcwLDMwIDkwLDMwIDc1LDQ1IDgwLDYwIDYwLDUwIDQwLDYwIDQ1LDQ1IDMwLDMwIDUwLDMwIiBmaWxsPSIjZTVlNWU1IiBzdHJva2U9IiNiYmIiIHN0cm9rZS13aWR0aD0iMSIvPgogIAogIDwhLS0gWWFzaGlsIGRvaXJhIC0tPgogIDxjaXJjbGUgY3g9IjYwIiBjeT0iNDAiIHI9IjI4IiBmaWxsPSJ1cmwoI2dyZWVuR3JhZGllbnQpIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMyIvPgogIDx0ZXh0IHg9IjIwIiB5PSI0NSIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPk88L3RleHQ+CiAgPHRleHQgeD0iMjAiIHk9IjUyIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+WjwvdGV4dD4KICA8dGV4dCB4PSIyMCIgeT0iNTkiIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5CPC90ZXh0PgogIDx0ZXh0IHg9IjIwIiB5PSI2NiIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkU8L3RleHQ+CiAgPHRleHQgeD0iMjAiIHk9IjczIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+SzwvdGV4dD4KICA8dGV4dCB4PSIyMCIgeT0iODAiIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5JPC90ZXh0PgogIDx0ZXh0IHg9IjI2IiB5PSI4NyIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPlM8L3RleHQ+CiAgPHRleHQgeD0iMzMiIHk9IjkzIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+VDwvdGV4dD4KICA8dGV4dCB4PSI0MCIgeT0iOTciIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5PTjwvdGV4dD4KICA8dGV4dCB4PSI4MCIgeT0iOTciIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5SRVNQVUJMSUtBU0k8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI0NSIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkQ8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI1MiIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkE8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI1OSIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkQ8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI2NiIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkw8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI3MyIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkE8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI4MCIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkI8L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI4NyIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPk88L3RleHQ+CiAgPHRleHQgeD0iMTAwIiB5PSI5NCIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkpYT05BPC90ZXh0PgogIDx0ZXh0IHg9IjEwMCIgeT0iMTAxIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+WElaTUFUSTwvdGV4dD4KICA8dGV4dCB4PSI2MCIgeT0iMTEwIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+REFWTEFUIEJPSlhPTkEgWElaTUFUSTwvdGV4dD4KICA8dGV4dCB4PSI2MCIgeT0iMTAwIiBmb250LWZhbWlseT0iVmVyZGFuYSIgZm9udC1zaXplPSI2IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXdlaWdodD0iYm9sZCI+TEFUPC90ZXh0PgogIAogIDwhLS0gRHVueW8gZ2xvYnVzaSAtLT4KICA8Y2lyY2xlIGN4PSI2MCIgY3k9IjQwIiByPSIxOCIgZmlsbD0idXJsKCNlYXJ0aEdyYWRpZW50KSIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjEiLz4KICA8Y2lyY2xlIGN4PSI2MCIgY3k9IjQwIiByPSIxNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjEiLz4KICA8Y2lyY2xlIGN4PSI2MCIgY3k9IjQwIiByPSIxMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjEiLz4KICA8Y2lyY2xlIGN4PSI2MCIgY3k9IjQwIiByPSI2IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMSIvPgogIDxjaXJjbGUgY3g9IjYwIiBjeT0iNDAiIHI9IjMiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIxIi8+CiAgCiAgPCEtLSBNZWRpY2FsIGNhZHVjZXVzIC0tPgogIDxsaW5lIHgxPSI2MCIgeTE9IjI1IiB4Mj0iNjAiIHkyPSI1NSIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjIiLz4KICA8cGF0aCBkPSJNIDU1IDMwIEwgNjUgMzAgTCA2MCAyNSBaIiBmaWxsPSIjMzMzIi8+CiAgPHBhdGggZD0iTSA1NSA1MCBMIDY1IDUwIEwgNjAgNTUgWiIgZmlsbD0iIzMzMyIvPgogIDxwYXRoIGQ9Ik0gNTAgMzUgQyA0NSAzNSA0NSA0NSA1MCA0NSBMIDYwIDQwIFoiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIxIi8+CiAgPHBhdGggZD0iTSA3MCAzNSBDIDc1IDM1IDc1IDQ1IDcwIDQ1IEwgNjAgNDAgWiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9zdmc+" 
                 alt="Bojxona Auditi Boshqarmasi Logo">
        </div>
        """, unsafe_allow_html=True)

    # Sidebar navigatsiyasi
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ3JlZW5HcmFkaWVudDIiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM0Y2FmNTA7c3RvcC1vcGFjaXR5OjEiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzI4YTc0NTtzdG9wLW9wYWNpdHk6MSIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIAogIDwhLS0gVGFzaHFpIGRvaXJhIC0tPgogIDxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjQ1IiBmaWxsPSJ1cmwoI2dyZWVuR3JhZGllbnQyKSIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjIiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIzNSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIyNSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIxNSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI1IiBmaWxsPSIjZmZmIiBzdHJva2U9Im5vbmUiLz4KICA8dGV4dCB4PSI1MCIgeT0iMzUiIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjgiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5CT0pYT05BPC90ZXh0PgogIDx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IlZlcmRhbmEiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC13ZWlnaHQ9ImJvbGQiPkFVRElUSTwvdGV4dD4KICA8dGV4dCB4PSI1MCIgeT0iNjciIGZvbnQtZmFtaWx5PSJWZXJkYW5hIiBmb250LXNpemU9IjYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtd2VpZ2h0PSJib2xkIj5CT1NIUUFSTUFTSTwvdGV4dD4KPC9zdmc+" 
             style="width: 50px; height: 50px; border-radius: 50%; margin-bottom: 10px;" 
             alt="Logo">
        <h4 style="color: #2275AC; margin: 0; font-size: 12px; line-height: 1.2;">Grafa31<br>Analyzer</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("## 🧭 Navigatsiya")
    
    nav_options = {
        'data_upload': '📁 1. Ma\'lumotni Yuklash',
        'analysis': '🔍 2. Tahlil va Vizualizatsiya',
        'web_search': '🌐 3. Web Search',
        'report': '📄 4. Hisobot'
    }
    
    for key, label in nav_options.items():
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
    
    # Joriy holat ko'rsatkichi
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📈 Joriy Holat")
    
    if st.session_state.json_data:
        if 'results' in st.session_state.json_data:
            total_products = len(st.session_state.json_data['results'])
            st.sidebar.metric("Yuklangan tovarlar", total_products)
        if st.session_state.processed_results:
            st.sidebar.metric("Qayta ishlangan", len(st.session_state.processed_results))
    else:
        st.sidebar.info("Hali JSON fayl yuklanmagan")

    # Sahifalar
    if st.session_state.current_page == 'data_upload':
        show_data_upload_page()
    elif st.session_state.current_page == 'analysis':
        show_analysis_page()
    elif st.session_state.current_page == 'web_search':
        show_web_search_page()
    elif st.session_state.current_page == 'report':
        show_report_page()

def show_data_upload_page():
    """Ma'lumot yuklash sahifasi"""
    st.markdown("# 📁 JSON Fayl Yuklash va Tahlil")
    st.markdown("**1000+ tovarli JSON faylni yuklang**")
    st.markdown("---")
    
    # Fayl yuklash
    uploaded_file = st.file_uploader(
        "JSON faylni tanlang:",
        type=['json'],
        help="Faqat JSON formatdagi fayllar qo'llab-quvvatlanadi"
    )
    
    if uploaded_file is not None:
        with st.spinner("JSON fayl o'qilmoqda..."):
            data, file_type = read_uploaded_file(uploaded_file)
            
            if data is not None:
                st.markdown('<div class="success-message">✅ JSON fayl muvaffaqiyatli yuklandi!</div>', unsafe_allow_html=True)
                
                # JSON strukturasini tekshirish
                if isinstance(data, dict) and 'results' in data:
                    st.session_state.json_data = data
                    
                    # Metadata ma'lumotlarini ko'rsatish
                    if 'metadata' in data:
                        metadata = data['metadata']
                        st.markdown("### 📊 Metadata Ma'lumotlari")
                        
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
                    
                    # Tovarlar ma'lumotlarini ko'rsatish
                    products = data['results']
                    st.info(f"📦 **{len(products)} ta tovar topildi**")
                    
                    # Birinchi 3 ta tovarni ko'rsatish
                    st.markdown("### 📋 Birinchi 3 ta Tovar (Namuna)")
                    for i in range(min(3, len(products))):
                        with st.expander(f"Tovar {i+1}: {products[i].get('наименование_товара', 'Noma\'lum')}"):
                            st.json(products[i])
                    
                    # Tahlil tugmasi
                    if st.button("🔍 Barchasi Tahlil Qilish", type="primary", use_container_width=True):
                        st.session_state.current_page = 'analysis'
                        st.rerun()
                        
                else:
                    st.error("JSON fayl noto'g'ri formatda! 'results' maydoni bo'lishi kerak.")
            else:
                st.error("Faylni o'qishda xatolik!")
    else:
        # Yo'riqnoma
        st.markdown("### 📖 Qanday Ishlatish")
        
        st.markdown("""
        1. **📁 JSON fayl yuklang** - Metadata va results bo'limlari bo'lgan fayl
        2. **🔍 Tahlil qilish** - 31-Grafa bo'yicha tahlil
        3. **🌐 Web Search** - "not specified" maydonlarni to'ldirish
        4. **📄 Hisobot** - Yakuniy natijalar
        """)
        
        st.markdown("### 📋 JSON Format Namunasi")
        st.code('''
{
    "metadata": {
        "total_items": 18,
        "processed_at": "2025-07-08T16:12:43.133616",
        "successful_items": 18,
        "failed_items": 0
    },
    "results": [
        {
            "наименование_товара": "Легковой автомобиль",
            "товарный_знак": "BMW i3",
            "название_бренда": "BMW",
            "модель": "BMW7000ABEV",
            "технические_характеристики": "not specified",
            "материал": "не указано"
        }
    ]
}
        ''', language='json')

def show_analysis_page():
    """Tahlil sahifasi"""
    st.markdown("# 🔍 Tahlil va Vizualizatsiya")
    st.markdown("---")
    
    if not st.session_state.json_data:
        st.warning("⚠️ Avval JSON fayl yuklang!")
        if st.button("📁 Fayl Yuklash Sahifasiga O'tish"):
            st.session_state.current_page = 'data_upload'
            st.rerun()
        return
    
    products = st.session_state.json_data['results']
    
    # Tahlil jarayoni
    if not st.session_state.processed_results:
        st.markdown("### 🔄 Tahlil Jarayoni")
        
        with st.spinner("Tovarlar tahlil qilinmoqda..."):
            processed_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, product in enumerate(products):
                status_text.text(f"Tahlil qilinmoqda: {idx + 1}/{len(products)}")
                
                filled_sections, missing_sections, confidence_scores = st.session_state.analyzer.analyze_single_product(product, f"Product_{idx}")
                
                processed_results.append({
                    'product_info': product,
                    'filled_sections': filled_sections,
                    'missing_sections': missing_sections,
                    'confidence_scores': confidence_scores
                })
                
                progress_bar.progress((idx + 1) / len(products))
            
            st.session_state.processed_results = processed_results
            st.success("✅ Tahlil yakunlandi!")
    
    # Natijalarni ko'rsatish
    st.markdown("### 📊 Tahlil Natijalari")
    
    results = st.session_state.processed_results
    
    # Umumiy statistika
    total_products = len(results)
    total_sections_possible = total_products * len(GRAFA_SECTIONS_MULTILINGUAL)
    total_filled = sum(len(result['filled_sections']) for result in results)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Jami Tovarlar", total_products)
    with col2:
        st.metric("To'ldirilgan Bo'limlar", total_filled)
    with col3:
        completion_rate = (total_filled / total_sections_possible) * 100
        st.metric("To'ldirilish Foizi", f"{completion_rate:.1f}%")
    
    # Vizualizatsiya
    st.markdown("### 📈 Vizualizatsiya")
    
    # Har bir tovar uchun to'ldirilish foizi
    completion_data = []
    for idx, result in enumerate(results):
        product_name = result['product_info'].get('наименование_товара', f'Tovar {idx+1}')
        filled_count = len(result['filled_sections'])
        completion_pct = (filled_count / len(GRAFA_SECTIONS_MULTILINGUAL)) * 100
        
        completion_data.append({
            'Tovar': product_name[:30] + '...' if len(product_name) > 30 else product_name,
            'To\'ldirilish_Foizi': completion_pct,
            'To\'ldirilgan_Soni': filled_count
        })
    
    df_completion = pd.DataFrame(completion_data)
    
    # Bar chart
    fig_bar = px.bar(
        df_completion, 
        x='Tovar', 
        y='To\'ldirilish_Foizi',
        title='Tovarlar bo\'yicha To\'ldirilish Foizi',
        labels={'To\'ldirilish_Foizi': 'To\'ldirilish Foizi (%)', 'Tovar': 'Tovarlar'},
        color='To\'ldirilish_Foizi',
        color_continuous_scale='RdYlGn'
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Tovarlar bo'yicha jadval
    st.markdown("### 📋 Tovarlar Jadvali")
    
    st.dataframe(df_completion, use_container_width=True)
    
    # Keyingi sahifaga o'tish
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌐 Web Search", use_container_width=True):
            st.session_state.current_page = 'web_search'
            st.rerun()
    
    with col2:
        if st.button("📄 Hisobot", use_container_width=True):
            st.session_state.current_page = 'report'
            st.rerun()

def show_web_search_page():
    """Web Search sahifasi"""
    st.markdown("# 🌐 Web Search")
    st.markdown("**'Not specified' maydonlarni to'ldirish**")
    st.markdown("---")
    
    if not st.session_state.processed_results:
        st.warning("⚠️ Avval tovarlarni tahlil qiling!")
        if st.button("🔍 Tahlil Sahifasiga O'tish"):
            st.session_state.current_page = 'analysis'
            st.rerun()
        return
    
    # API kalitlar holati
    st.markdown("### 🔑 API Kalitlar Holati")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"💡 **Mavjud API kalitlar:** {len(SERPER_API_KEYS)}")
        for i, key in enumerate(SERPER_API_KEYS):
            st.code(f"Kalit {i+1}: {key[:20]}...")
    
    with col2:
        st.info(f"🌐 **API URL:** {SERPER_URL}")
        st.info("⚡ **Rate Limiting:** 1.2 soniya kutish")
    
    # "Not specified" maydonlarni tekshirish
    products = st.session_state.json_data['results']
    
    not_specified_count = 0
    products_with_not_specified = []
    
    for idx, product in enumerate(products):
        not_specified_fields = []
        
        for key, value in product.items():
            if isinstance(value, str) and ("not specified" in value.lower() or "не указано" in value.lower() or "не указан" in value.lower()):
                not_specified_fields.append(key)
        
        if not_specified_fields:
            not_specified_count += len(not_specified_fields)
            products_with_not_specified.append({
                'index': idx,
                'product': product,
                'not_specified_fields': not_specified_fields
            })
    
    # Statistika
    st.markdown("### 📊 'Not Specified' Statistikasi")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Jami 'Not Specified'", not_specified_count)
    with col2:
        st.metric("Tegishli Tovarlar", len(products_with_not_specified))
    with col3:
        if len(products) > 0:
            fill_percentage = (len(products_with_not_specified) / len(products)) * 100
            st.metric("Tovarlar Foizi", f"{fill_percentage:.1f}%")
    
    if not products_with_not_specified:
        st.success("🎉 Barcha tovarlar to'ldirilgan! 'Not specified' maydonlar topilmadi.")
        return
    
    # 'Not specified' maydonlarni ko'rsatish
    st.markdown("### 📋 'Not Specified' Maydonlar")
    
    with st.expander("📊 Batafsil Ma'lumotlar", expanded=True):
        for idx, item in enumerate(products_with_not_specified[:10]):  # Faqat birinchi 10 ta
            product = item['product']
            fields = item['not_specified_fields']
            
            st.write(f"**{idx + 1}. {product.get('наименование_товара', 'Noma\'lum')}**")
            st.write(f"   • 'Not specified' maydonlar: {', '.join(fields)}")
    
    # Qidiruvni boshlash
    st.markdown("---")
    
    if st.button("🚀 Web Search Boshlash", type="primary", use_container_width=True):
        
        # Progress container
        progress_container = st.container()
        progress_container.markdown('<div class="search-progress">🔍 Web Search jarayoni boshlandi...</div>', unsafe_allow_html=True)
        
        # Ma'lumotlarni to'ldirish
        with st.spinner("🌐 API orqali ma'lumotlar to'ldirilmoqda..."):
            filler = NotSpecifiedFiller()
            
            filled_products = []
            processed_count = 0
            total_filled = 0
            
            for item in products_with_not_specified:
                product = item['product']
                
                progress_container.write(f"\n📦 **Tovar {processed_count + 1}/{len(products_with_not_specified)}:** {product.get('наименование_товара', 'Noma\'lum')}")
                
                filled_product = filler.fill_all_not_specified_fields(product, progress_container)
                filled_products.append(filled_product)
                
                # Nechta maydon to'ldirilganini hisoblash
                original_not_specified = len(item['not_specified_fields'])
                current_not_specified = len(filler.find_not_specified_fields(filled_product))
                filled_count = original_not_specified - current_not_specified
                total_filled += filled_count
                
                processed_count += 1
        
        # Natijalar
        st.markdown(f'<div class="success-message">🎉 Web Search yakunlandi! {processed_count} ta tovar, {total_filled} ta maydon to\'ldirildi.</div>', unsafe_allow_html=True)
        
        # Yangilangan ma'lumotlarni session state ga saqlash
        updated_results = st.session_state.json_data.copy()
        
        # Filled products ni asosiy ma'lumotlarga qo'shish
        for i, item in enumerate(products_with_not_specified):
            original_index = item['index']
            updated_results['results'][original_index] = filled_products[i]
        
        st.session_state.json_data = updated_results
        
        # Statistika
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Qayta ishlangan tovarlar", processed_count)
        with col2:
            st.metric("To'ldirilgan maydonlar", total_filled)
        with col3:
            success_rate = (total_filled / not_specified_count) * 100 if not_specified_count > 0 else 0
            st.metric("Muvaffaqiyat", f"{success_rate:.1f}%")
        
        # Keyingi harakatlar
        st.markdown("### 🎯 Keyingi Harakatlar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Tahlilni Qayta Qilish", use_container_width=True):
                st.session_state.processed_results = []  # Clear previous results
                st.session_state.current_page = 'analysis'
                st.rerun()
        
        with col2:
            if st.button("📄 Hisobot Ko'rish", use_container_width=True):
                st.session_state.current_page = 'report'
                st.rerun()

def show_report_page():
    """Hisobot sahifasi"""
    st.markdown("# 📄 Hisobot")
    st.markdown("---")
    
    if not st.session_state.processed_results:
        st.warning("⚠️ Avval tovarlarni tahlil qiling!")
        if st.button("🔍 Tahlil Sahifasiga O'tish"):
            st.session_state.current_page = 'analysis'
            st.rerun()
        return
    
    results = st.session_state.processed_results
    
    # Yakuniy statistika
    total_products = len(results)
    total_sections_possible = total_products * len(GRAFA_SECTIONS_MULTILINGUAL)
    total_filled = sum(len(result['filled_sections']) for result in results)
    
    # Header metrikalari
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jami Tovarlar", total_products)
    with col2:
        st.metric("Jami Bo'limlar", total_sections_possible)
    with col3:
        st.metric("To'ldirilgan Bo'limlar", total_filled)
    with col4:
        completion_rate = (total_filled / total_sections_possible) * 100
        st.metric("Umumiy To'ldirilish", f"{completion_rate:.1f}%")
    
    # Progress vizualizatsiyasi
    st.progress(completion_rate / 100, text=f"Umumiy to'ldirilish: {completion_rate:.1f}%")
    
    st.markdown("---")
    
    # Batafsil hisobot
    tab1, tab2, tab3 = st.tabs([
        "📋 To'liq Ma'lumotlar", 
        "📊 Vizual Tahlil", 
        "💾 Eksport"
    ])
    
    with tab1:
        st.markdown("### 📋 Har bir Tovar uchun 31-Grafa Bo'limlari")
        
        for idx, result in enumerate(results):
            product_info = result['product_info']
            filled_sections = result['filled_sections']
            missing_sections = result['missing_sections']
            
            product_name = product_info.get('наименование_товара', f'Tovar {idx+1}')
            
            with st.expander(f"📦 {idx+1}. {product_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**✅ To'ldirilgan bo'limlar:**")
                    for section_key, content in filled_sections.items():
                        section_name = GRAFA_SECTIONS_MULTILINGUAL[section_key]['name']
                        st.write(f"• **{section_name}**: {content[:50]}...")
                
                with col2:
                    st.markdown("**❌ Yetishmayotgan bo'limlar:**")
                    for section_key in missing_sections:
                        section_name = GRAFA_SECTIONS_MULTILINGUAL[section_key]['name']
                        st.write(f"• {section_name}")
    
    with tab2:
        st.markdown("### 📊 Vizual Tahlil")
        
        # Birinchi tovar uchun pie chart
        if results:
            first_result = results[0]
            fig_pie = create_completion_charts(first_result['filled_sections'], first_result['missing_sections'])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Bo'limlar bo'yicha statistika
        section_stats = {}
        for section_key, section_data in GRAFA_SECTIONS_MULTILINGUAL.items():
            filled_count = sum(1 for result in results if section_key in result['filled_sections'])
            section_stats[section_data['name']] = {
                'filled': filled_count,
                'missing': total_products - filled_count,
                'percentage': (filled_count / total_products) * 100
            }
        
        st.markdown("### 📈 Bo'limlar bo'yicha Statistika")
        
        stats_data = []
        for section_name, stats in section_stats.items():
            stats_data.append({
                'Bo\'lim': section_name,
                'To\'ldirilgan': stats['filled'],
                'Yetishmayotgan': stats['missing'],
                'Foiz': f"{stats['percentage']:.1f}%"
            })
        
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True)
    
    with tab3:
        st.markdown("### 💾 Eksport Qilish")
        
        # Excel eksport
        excel_buffer = export_to_excel(results)
        
        if excel_buffer:
            st.download_button(
                label="📊 Excel Formatda Yuklab Olish",
                data=excel_buffer,
                file_name=f"grafa31_hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        
        # JSON eksport
        export_data = {
            "analysis_date": datetime.now().isoformat(),
            "total_products": total_products,
            "completion_rate": completion_rate,
            "results": results
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 JSON Formatda Yuklab Olish",
            data=json_str.encode('utf-8'),
            file_name=f"grafa31_hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # Yakuniy JSON (to'ldirilgan ma'lumotlar bilan)
        if st.session_state.json_data:
            final_json = json.dumps(st.session_state.json_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="🚀 To'ldirilgan JSON Yuklab Olish",
                data=final_json.encode('utf-8'),
                file_name=f"filled_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
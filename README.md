# 📊 Grafa31 Analyzer

**Bojxona auditi boshqarmasi uchun 31-Grafa avtomatik tahlil tizimi**

## 🎯 Loyiha haqida

Grafa31 Analyzer - bu bojxona deklaratsiyalarining 31-Grafa bo'limini avtomatik tahlil qilish va to'ldirish uchun mo'ljallangan MVP (Minimum Viable Product) loyihasi. Tizim sun'iy intellekt va web scraping texnologiyalarini qo'llab, yetishmayotgan ma'lumotlarni avtomatik ravishda topib beradi.

## ⭐ Asosiy xususiyatlar

### 🔍 **Ma'lumot tahlili**
- JSON, Excel, CSV formatlardan ma'lumot import qilish
- Qo'lda ma'lumot kiritish imkoniyati
- NLP (Natural Language Processing) orqali avtomatik bo'lim aniqlash
- Matn o'xshashligi va kalit so'zlar tahlili

### 🌐 **Web Qidiruv**
- Yetishmayotgan bo'limlar uchun avtomatik internet qidiruv
- DuckDuckGo va Bing qidiruv tizimlari integratsiyasi
- Content scraping va ma'lumot ajratish
- Qidiruv chuqurligi sozlamalari

### 📊 **Vizualizatsiya**
- Interaktiv diagrammalar (Plotly)
- To'ldirilish statistikalari
- Bo'limlar holati ko'rsatkichlari
- Real-time progress tracking

### 🎯 **HS Kod Tavsiyasi**
- Mahsulot tavsifiga asoslangan avtomatik HS kod tavsiyasi
- Machine Learning algoritmlari
- Mos kelish darajasi ko'rsatkichi

### 💾 **Eksport**
- Excel (.xlsx) - to'liq jadval va statistikalar
- JSON - strukturali ma'lumotlar
- CSV - oddiy jadval formati
- Markdown hisobot

## 🛠 Texnologiyalar

### **Frontend**
- **Streamlit** - Web interfeys
- **Plotly** - Interaktiv grafiklar
- **Custom CSS** - Modern dizayn va animatsiyalar

### **Backend**
- **Python 3.8+** - Asosiy dasturlash tili
- **Pandas** - Ma'lumotlarni qayta ishlash
- **NLTK** - Tabiiy til qayta ishlash
- **Scikit-learn** - Machine Learning

### **Web Scraping**
- **Requests** - HTTP so'rovlar
- **BeautifulSoup4** - HTML parsing
- **DuckDuckGo API** - Qidiruv tizimi

### **Ma'lumotlar**
- **JSON** - Konfiguratsiya va ma'lumotlar
- **Excel/CSV** - Import/Export
- **SQLite** - Keshirlash (opsional)

## 🚀 O'rnatish va ishga tushirish

### **1. Repository klonlash**
```bash
git clone https://github.com/your-username/grafa31-analyzer.git
cd grafa31-analyzer
```

### **2. Virtual muhit yaratish**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate     # Windows
```

### **3. Kutubxonalarni o'rnatish**
```bash
pip install -r requirements.txt
```

### **4. Ilovani ishga tushirish**
```bash
streamlit run main.py
```

### **5. Brauzerda ochish**
Avtomatik ochiladi yoki qo'lda: `http://localhost:8501`

## 📋 Requirements.txt

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
nltk>=3.8.0
scikit-learn>=1.3.0
plotly>=5.15.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
python-dateutil>=2.8.0
```

## 📁 Loyiha strukturasi

```
grafa31-analyzer/
│
├── main.py                 # Asosiy Streamlit ilovasi
├── style.css              # CSS stillari
├── requirements.txt       # Python kutubxonalar ro'yxati
├── README.md              # Loyiha dokumentatsiyasi
│
├── data/                  # Ma'lumotlar papkasi
│   ├── hs_codes.json     # HS kodlar bazasi
│   └── sample_data.json  # Namuna ma'lumotlar
│
├── modules/               # Modullar
│   ├── text_analyzer.py  # Matn tahlil moduli
│   ├── web_scraper.py    # Web scraping moduli
│   └── data_processor.py # Ma'lumot qayta ishlash
│
├── assets/               # Rasm va fayllar
│   ├── logo.png         # Logotip
│   └── screenshots/     # Ekran rasmlari
│
└── tests/               # Testlar
    ├── test_analyzer.py
    └── test_scraper.py
```

## 🎮 Foydalanish qo'llanmasi

### **1. Ma'lumot kiritish**
- **Fayl yuklash**: JSON, Excel yoki CSV faylni drag & drop
- **Qo'lda kiritish**: 11 ta bo'lim uchun forma to'ldirish
- **JSON**: Bevosita JSON ma'lumotlarni kiritish

### **2. Tahlil**
- Avtomatik bo'lim aniqlash
- To'ldirilgan va yetishmayotgan bo'limlar ko'rsatkichi
- Ishonch darajasi metrikalari

### **3. Web qidiruv**
- Mahsulot nomini kiritish
- Qidiruv chuqurligi tanlash (Tez/O'rta/To'liq)
- Avtomatik ma'lumot ajratish

### **4. Natijalar**
- To'liq 31-Grafa jadvali
- Vizual tahlil grafiklari
- HS kod tavsiyasi
- Batafsil hisobot

### **5. Eksport**
- Excel, JSON, CSV formatlar
- Statistika va xulosalar
- Professional hisobotlar

## 🔧 Konfiguratsiya

### **31-Grafa bo'limlari**
```python
GRAFA_SECTIONS = {
    "tovar_nomi": "Tovar nomi, turi",
    "o_ram_turi": "O'ram turi", 
    "materiali": "Materiali",
    "ishlab_chiqarish_texnologiyasi": "Ishlab chiqarish texnologiyasi",
    "ishlatilish_maqsadi": "Ishlatilish maqsadi",
    "tovar_ishlatiladigan_sanoat": "Tovar ishlatiladigan sanoat",
    "ishlab_chiqaruvchi": "Ishlab chiqaruvchi",
    "savdo_belgisi": "Savdo belgisi",
    "texnik_xususiyatlar": "Texnik xususiyatlar",
    "ishlab_chiqarilgan_yil": "Ishlab chiqarilgan yil",
    "tovar_kodi": "Tovar kodi (modeli, versiyasi)"
}
```

### **HS kodlar bazasi**
```python
HS_CODES_DATABASE = {
    "8471": "Avtomatik ma'lumotlarni qayta ishlash mashinalari",
    "8517": "Telefon apparatlari, radio-telefon apparatlari",
    "8528": "Monitorlar va projektorlar, televizorlar",
    # ... qo'shimcha kodlar
}
```

## 📊 Algoritm ishlash prinsipi

### **1. Matn tahlili**
```python
def analyze_text_for_section(text, section_key):
    # Keyword matching
    # Pattern recognition  
    # TF-IDF similarity
    # Priority weighting
    return score, matched_keywords
```

### **2. Web qidiruv**
```python
def search_for_missing_sections(product_name, missing_sections):
    # Multi-engine search (DuckDuckGo + Bing)
    # Content scraping
    # Relevance filtering
    # Information extraction
    return scraped_data
```

### **3. HS kod tavsiyasi**
```python
def suggest_hs_code(combined_description):
    # Text similarity calculation
    # Database matching
    # Confidence scoring
    return best_match, similarity_score
```

## 🎨 Dizayn xususiyatlari

### **Modern UI/UX**
- Clean va minimal dizayn
- Sistem temasiga mos (qora/oq)
- Responsive layout
- Professional ko'rinish

### **Button animatsiyalari (style.css)**
- Rainbow gradient borders
- Glowing hover effects
- Smooth transitions
- Active state animations

### **Interaktiv elementlar**
- Progress bars
- Loading spinners
- Tooltip help texts
- Expandable sections

## 🧪 Test qilish

### **Unit testlar**
```bash
python -m pytest tests/
```

### **Manual test**
1. Turli formatdagi fayllarni yuklash
2. Web qidiruv funksiyasini test qilish
3. Eksport formatlarini tekshirish
4. Performance monitoring

## 📈 Performance ko'rsatkichlari

- **Ma'lumot tahlili**: ~2-5 soniya
- **Web qidiruv**: ~30-60 soniya (3-5 bo'lim)
- **Eksport**: ~1-3 soniya
- **Memory usage**: ~50-100MB

## 🔒 Xavfsizlik

- Input validation va sanitization
- Rate limiting web requests
- Error handling va logging
- No sensitive data storage

## 🛣 Rivojlanish rejasi

### **Versiya 1.1** (Keyingi 2-3 oy)
- [ ] Foydalanuvchi autentifikatsiyasi
- [ ] Ma'lumotlar bazasi integratsiyasi
- [ ] Batch processing
- [ ] API endpoints

### **Versiya 1.2** (3-6 oy)
- [ ] Machine Learning model training
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Mobile application

### **Versiya 2.0** (6-12 oy)
- [ ] Cloud deployment
- [ ] Microservices architecture
- [ ] Real-time collaboration
- [ ] Enterprise features

## 🤝 Hissa qo'shish

1. **Fork** qiling repositoryni
2. **Branch** yarating (`git checkout -b feature/AmazingFeature`)
3. **Commit** qiling o'zgarishlaringizni (`git commit -m 'Add AmazingFeature'`)
4. **Push** qiling branchga (`git push origin feature/AmazingFeature`)
5. **Pull Request** oching

## 📜 Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatiladi. Batafsil ma'lumot uchun `LICENSE` faylini ko'ring.

## 🙏 Minnatdorchilik

- **Streamlit** - Web framework
- **NLTK** - Natural Language Processing
- **Plotly** - Data visualization
- **BeautifulSoup** - Web scraping
- **O'zbekiston Bojxona Qo'mitasi** - Texnik talablar

---

<div align="center">

**📊 Grafa31 Analyzer** - Bojxona auditi boshqarmasi

*Avtomatik tahlil. Professional natijalar. Oddiy foydalanish.*

**⭐ Agar loyiha foydali bo'lsa, star bosing!**

</div>
import os
import sys
import polars as pl

# Projenin ana dizinini yola ekleyelim ki 'ai_api' modülü bulunabilsin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_api.data_processing.metadata_extractor import extract_metadata
from ai_api.agents.decision_agent import get_data_cleaning_decision
from ai_api.data_processing.polars_cleaner import clean_data

def run_test():
    print("--- Test Başlıyor ---")
    
    # 1. Test için örnek bir CSV dosyası oluşturalım
    print("\n1. Örnek CSV dosyası oluşturuluyor (dummy_data.csv)...")
    df = pl.DataFrame({
        "ID": [1, 2, 3, 4, 5],
        "Name": ["Ali", "Veli", "Ayşe", "Fatma", "Ahmet"],
        "Age": [25, None, 30, 22, None], # 2 eksik veri
        "Salary": [5000, 6000, 5500, None, 7000], # 1 eksik veri
        "Purchased": ["Yes", "No", "Yes", "Yes", "No"] # Hedef Kolon (Sınıflandırma)
    })
    df.write_csv("dummy_data.csv")
    print("CSV Oluşturuldu!")
    
    # 2. Metadata (Veri Özeti) Çıkarma
    print("\n2. Polars ile Metadata çıkarılıyor...")
    metadata_json = extract_metadata("dummy_data.csv")
    print(f"Çıkarılan Metadata:\n{metadata_json}")
    
    # API Key kontrolü
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n[HATA] GOOGLE_API_KEY bulunamadı! LLM çağrısı yapılamıyor.")
        print("Lütfen .env dosyanızı oluşturup içine GOOGLE_API_KEY=... ekleyin.")
        return
        
    # 3. LLM'e Karar Aldırma
    print("\n3. LLM'e (Gemini) bağlanılıyor ve temizleme kararları alınıyor...")
    try:
        decision = get_data_cleaning_decision(metadata_json)
        print("\nLLM Kararı (JSON):")
        import json
        print(json.dumps(decision, indent=2, ensure_ascii=False))
        
        # 4. Kararları Polars ile Uygulama
        print("\n4. LLM kararları doğrultusunda veriler temizleniyor...")
        output_file = clean_data("dummy_data.csv", "cleaned_data.csv", decision)
        
        print("\nTemizlenmiş Veri (cleaned_data.csv):")
        cleaned_df = pl.read_csv(output_file)
        print(cleaned_df)
        print("\n--- Test Başarıyla Tamamlandı! ---")
        
    except Exception as e:
        print(f"\n[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    # Eğer .env dosyanız üst klasördeyse, test çalışırken yolu bulması için:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="../.env")
    run_test()

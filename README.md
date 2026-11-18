# Otonom Soroban Güvenlik Ajanı (Agentic AI)

Bu proje, Stellar Soroban akıllı sözleşmelerini analiz eden, açık kaynaklı araçlarla zafiyet taraması yapan ve bulguları Lokal bir LLM (Qwen 2.5) kullanarak Türkçe, profesyonel bir rapora dönüştüren otonom bir siber güvenlik ajanıdır.

## Özellikler
- **Otonom Tarama:** `sentinel-soroban` kullanarak Testnet üzerindeki sözleşmeleri derinlemesine analiz eder.
- **Agentic Raporlama (LLM):** Ham JSON verisini, halüsinasyon görmeyen ve sadece veriyi formatlayan lokal bir LLM (Qwen 2.5) ile insan odaklı Markdown raporuna dönüştürür.
- **Zincir Üstü Mühürleme (Audit Trail):** Üretilen raporun SHA-256 hash'ini Stellar Testnet ağına bir işlem (memo) olarak kaydeder. Bu sayede raporun değiştirilemezliği kanıtlanır.
- **Modern Arayüz:** Streamlit ile geliştirilmiş, karanlık temalı kullanıcı dostu web arayüzü.

## Kurulum ve Çalıştırma
1. Gerekli Python kütüphanelerini yükleyin:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Lokal LLLM ' i başlat : 
    ```bash
    ollama run qwen2.5:7b
    ```
3. Arayüzü Çalıştır:
    ```bash
    streamlit run app.py
    ```

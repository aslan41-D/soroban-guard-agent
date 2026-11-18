import streamlit as st
import subprocess
import json
import os
from agent import generate_report # Kendi yazdığımız LLM fonksiyonunu içe aktarıyoruz
from agent import generate_report, seal_on_stellar 

st.set_page_config(page_title="Soroban Guard Agent", page_icon="🛡️", layout="wide")

st.title("Otonom Soroban Güvenlik Ajanı")
st.markdown("Stellar Testnet üzerindeki akıllı sözleşmeleri analiz edin ve LLM destekli rapor alın.")

# Kenar Çubuğu (Sidebar)
st.sidebar.header("Tarama Ayarları")
contract_id = st.sidebar.text_input("Contract ID (C... ile başlayan)", "")

if st.sidebar.button("Analizi Başlat"):
    if not contract_id:
        st.sidebar.error("Lütfen geçerli bir Contract ID girin.")
    else:
        with st.spinner("Sentinel ile sözleşme taranıyor..."):
            # Sentinel komutunu çalıştır (JSON çıktısını bir dosyaya kaydet)
            cmd = f"npx sentinel-soroban scan {contract_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Not: Sentinel'ın çıktısını doğrudan JSON olarak almak için komutuna
            # '--json' veya '> report.json' gibi bir parametre eklemen gerekebilir.
            # Burada varsayıyoruz ki çıktıyı bir şekilde report.json'a kaydettik.
            
            # Eğer çıktı başarılıysa LLM'e gönder
            try:
                # Örnek olarak önceden kaydettiğimiz report.json'u okuyalım
                # Gerçek uygulamada subprocess çıktısını parse etmelisin.
                with open("report.json", "r") as f:
                    report_data = json.load(f)
                
                st.toast("Tarama tamamlandı! LLM Raporu oluşturuluyor...")
                
                # LLM Raporunu oluştur
                llm_report = generate_report(report_data)
                
                # Sonuçları ekranda göster
                st.subheader("📋 Yapay Zeka Destekli Güvenlik Raporu")
                st.markdown(llm_report)

                # --- ZİNCİR ÜSTÜ KAYIT KISMI ---
                                # --- ZİNCİR ÜSTÜ KAYIT KISMI ---
                with st.spinner("Rapor Stellar Testnet'e mühürleniyor..."):
                    try:
                        # agent.py içindeki yeni fonksiyonu çağırıyoruz
                        tx_hash = seal_on_stellar(llm_report)
                        
                        st.success(f"⛓️ **Zincir Üstü Mühür Başarılı!** Raporun özeti Stellar Testnet'e kaydedildi.")
                        st.code(f"İşlem Hash'i: {tx_hash}")
                        st.markdown(f"[Stellar Expert'te Görüntüle](https://stellar.expert/explorer/testnet/tx/{tx_hash})")
                        
                    except Exception as e:
                        st.error(f"Zincire kayıt başarısız oldu. Hata detayı: {e}")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")

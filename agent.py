import json
import requests
import sys
import hashlib
import subprocess
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Payment, Asset, Memo


# 1. JSON raporunu oku
def load_report(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Hata: {file_path} bulunamadı. Lütfen dosya yolunu kontrol edin.")
        sys.exit(1)

# 2. LLM'e (Ollama'ya) istek at
def generate_report(report_data):
    print("⏳ Ajan veriyi hazırlıyor...")
    
    # 1. Sadece LLM'in ihtiyacı olan verileri filtrele (Gürültüyü temizle)
    # Detector, confidence, evidence gibi LLM'in kafasını karıştıran kısımları atıyoruz.
    clean_findings = []
    for f in report_data.get('findings', []):
        # Sadece High ve Medium olanları alalım (Düşükler zaten çok fazla, raporu şişirmesin)
        if f.get('severity') in ['high', 'medium']:
            clean_findings.append({
                "title": f.get('title'),
                "severity": f.get('severity'),
                "function": f.get('affectedFunction', 'Genel'),
                "description": f.get('description'),
                "recommendation": f.get('recommendation')
            })
            
    # Eğer hiç bulgu yoksa
    if not clean_findings:
        return "## Yönetici Özeti\nSözleşmede yüksek veya orta riskli bir zafiyet tespit edilmedi. Risk Skoru: " + str(report_data.get('riskScore'))

    # 2. LLM'e vereceğimiz KESİN Şablon (System Prompt)
    system_prompt = """
    Sen bir çeviri ve formatlama motorusun. Sana bir JSON listesi vereceğim. 
    Görevin: Bu JSON'daki verileri kullanarak AŞAĞIDAKİ ŞABLONA BİREBİR UYAN Türkçe bir Markdown raporu oluşturmak.

    KESİN KURALLAR:
    - SADECE Türkçe yazacaksın. İngilizce kelime kullanmayacaksın.
    - Açıklama (description) ve Öneri (recommendation) kısımlarını Türkçeye çevireceksin.
    - ASLA kod yazmayacaksın, ASLA sohbet etmeyeceksin. Sadece Markdown çıktısı vereceksin.
    - JSON'da olmayan hiçbir şeyi uydurmayacaksın.

    ŞABLON:
    #  Soroban Güvenlik Raporu
    
    ## Yönetici Özeti
    - **Risk Skoru:** {risk_skoru}/100
    - **Tespit Edilen Riskler:** {yuksek_sayisi} Yüksek, {orta_sayisi} Orta
    
    ## Bulgular
    [Her bulgu için aşağıdaki formatı tekrarla]
    ### [Bulgu Başlığı - Türkçe]
    - **Risk Seviyesi:** [High -> Yüksek, Medium -> Orta]
    - **Etkilenen Fonksiyon:** `[Fonksiyon Adı]`
    - **Açıklama:** [Description kısmını Türkçe yaz]
    - **Öneri:** [Recommendation kısmını Türkçe yaz]
    """

    user_prompt = f"""
    Risk Skoru: {report_data.get('riskScore')}
    Yüksek Sayısı: {report_data.get('high', 0)}
    Orta Sayısı: {report_data.get('medium', 0)}
    
    İşte Bulgular (JSON):
    {json.dumps(clean_findings, indent=2, ensure_ascii=False)}
    """

    # 3. Ollama API'sine istek
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5:7b", # Qwen veya Llama3
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # Yaratıcılığı SIFIRLA. Sadece kurallara uysun.
            "top_p": 0.1
        }
    }
    
    print("⏳ LLM Raporu yazıyor...")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json().get("response", "")
        
        # Bazen modeller "İşte raporunuz:" diye başlayabiliyor, onu temizleyelim
        if "```markdown" in result:
            result = result.split("```markdown")[1].split("```")[0]
            
        return result.strip()
    except Exception as e:
        print(f"Hata: {e}")
        return "Rapor oluşturulamadı."


# 3. Raporu kaydet
def save_markdown(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Başarılı! Rapor şuraya kaydedildi: {output_path}")

def seal_on_stellar(markdown_report):
    print("⛓️ Rapor Stellar Testnet'e mühürleniyor...")
    
    # 1. Raporun SHA-256 hash'ini al ve kısalt
    report_hash = hashlib.sha256(markdown_report.encode('utf-8')).hexdigest()[:28]
    
    # 2. Stellar Testnet'e bağlan
    server = Server(horizon_url="https://horizon-testnet.stellar.org")
    
    # 3. 'alice' cüzdanını yükle (stellar CLI'daki gizli anahtarı kullanarak)
    # Not: Cüzdanın gizli anahtarını (S... ile başlayan) buraya girmelisin.
    # Güvenlik nedeniyle, bu anahtarı bir ortam değişkeninden okumak daha iyidir.
    # Örnek: ALICE_SECRET = os.getenv("ALICE_SECRET")
    # Şimdilik test amaçlı doğrudan yazıyoruz (Üretimde ASLA yapma!):
    ALICE_SECRET = "SDWAC4AOL6ZU67IIF2LNJ4ED7A2H6CA6NNBYPJYBUT3VLMYIOIDAXOKE"
    source_keypair = Keypair.from_secret(ALICE_SECRET)
    source_account = server.load_account(source_keypair.public_key)

    # 4. İşlemi oluştur (1 XLM gönderimi + Memo)
    transaction = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=100,
        )
        .add_text_memo(report_hash) # İşte memo burada ekleniyor!
        .append_payment_op(
            destination=source_keypair.public_key, # Kendine gönder
            amount="1",
            asset=Asset.native(),
        )
        .set_timeout(30)
        .build()
    )

    # 5. İşlemi imzala ve gönder
    transaction.sign(source_keypair)
    response = server.submit_transaction(transaction)
    print(f"✅ Rapor zincire mühürlendi! İşlem Hash'i: {response['hash']}")

    return response['hash'] 


if __name__ == "__main__":
    # Kullanıcıdan dosya yolunu al (varsayılan: report.json)
    input_file = sys.argv[1] if len(sys.argv) > 1 else "report.json"
    output_file = "final_security_report.md"
    
    print(f"📂 Rapor okunuyor: {input_file}")
    report_data = load_report(input_file)
    
    final_report = generate_report(report_data)
    
    save_markdown(final_report, output_file)
    seal_on_stellar(final_report)


    

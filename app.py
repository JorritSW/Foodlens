from flask import Flask, render_template, request, redirect, url_for
from database import ProductDatabase
from Clip import ocr_scan
import os
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()

app = Flask(__name__)
db = ProductDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_barcode', methods=['POST'])
def search_barcode():
    product_name = request.form.get('barcode')
    if not product_name:
        return render_template('result.html', error="Geen productnaam ingevoerd")
    
    product = db.search_product(product_name)
    if not product:
        return render_template('result.html', error="Product niet gevonden")
    
    # Debug print
    print("Product ingrediënten:", product.get('ingredienten'))
    
    return render_template('result.html', product=product)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return render_template('result.html', error="Geen afbeelding geüpload")
    
    image = request.files['image']
    if image.filename == '':
        return render_template('result.html', error="Geen afbeelding geselecteerd")
    
    try:
        temp_path = "temp_image.jpg"
        image.save(temp_path)
        
        print("\n=== Nieuwe analyse gestart ===")
        # Gebruik de verbeterde ocr_scan functie
        scan_result = ocr_scan(temp_path)
        print(f"Volledige tekst: {scan_result['full_text']}")
        print(f"Opgeschoonde tekst: {scan_result['cleaned_text']}")
        print(f"Gevonden hoeveelheid: {scan_result['quantity']}")
        
        # Zoek het product in de database met de opgeschoonde tekst
        product = db.search_product(scan_result['cleaned_text'])
        
        if product:
            # Voeg de gevonden hoeveelheid toe aan het product als die gevonden is
            if scan_result['quantity']:
                product['hoeveelheid'] = scan_result['quantity']
            return render_template('result.html', 
                                product=product,
                                extracted_text=scan_result['full_text'])
        else:
            return render_template('result.html', 
                                error=f"Geen product gevonden voor: {scan_result['cleaned_text']}",
                                extracted_text=scan_result['full_text'])
            
    except Exception as e:
        return render_template('result.html', 
                             error=f"Fout tijdens analyse: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # Reloader uitgezet, debug aan
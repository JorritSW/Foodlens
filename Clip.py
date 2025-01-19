import os
from typing import List, Dict
import easyocr
import argparse
import re
import cv2

def preprocess_image(image_path: str):
    """Preprocess image voor betere OCR herkenning"""
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    # Vergroot de afbeelding voor betere herkenning
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Verbeter contrast en helderheid
    image = cv2.convertScaleAbs(image, alpha=1.5, beta=20)
    return image

def ocr_scan(image_path: str) -> Dict[str, str]:
    """Running OCR over the image and extracting product info"""
    try:
        # Preprocess de afbeelding
        preprocessed_image = preprocess_image(image_path)
        
        # Configureer de reader met optimale parameters voor grote tekst
        reader = easyocr.Reader(
            ['nl', 'en'],
            gpu=True,
            model_storage_directory='./models',
            download_enabled=True,
            paragraph=True,
            decoder='beamsearch',
            beamWidth=10,
            batch_size=1,
            contrast_ths=0.3,
            adjust_contrast=0.8,
            text_threshold=0.7,
            link_threshold=0.4,
            mag_ratio=1.5
        )
        
        # Lees de tekst met confidence scores
        result = reader.readtext(preprocessed_image)
        
        # Filter op basis van tekstgrootte en confidence
        filtered_text = []
        for (bbox, text, confidence) in result:
            # Bereken de hoogte van de tekstbox
            height = bbox[2][1] - bbox[0][1]
            
            # Filter op basis van tekstgrootte en confidence score
            if height > 30 and confidence > 0.5:
                cleaned_segment = text.strip()
                if len(cleaned_segment) > 1 or cleaned_segment.isalpha():
                    filtered_text.append(cleaned_segment)
        
        recognized_text = " ".join(filtered_text)
        
        # Uitgebreide text normalisatie
        ocr_corrections = {
            '0': 'o', '1': 'i', '|': 'i', '@': 'a', '5': 's',
            '€': 'e', "'": "'", '"': '"', '—': '-', '`': "'",
            '°': '', '®': '', '™': ''
        }
        
        cleaned_text = recognized_text
        for wrong, correct in ocr_corrections.items():
            cleaned_text = cleaned_text.replace(wrong, correct)
        
        # Verbeterde quantity detection
        quantity_pattern = r'\b(\d+(?:[,.]\d+)?)\s*(?:ml|g|kg|l|gram|liter|cl|gr|kilo|milliliter|oz|lb)\b'
        quantity_matches = re.finditer(quantity_pattern, cleaned_text.lower())
        quantities = [match.group(0) for match in quantity_matches]
        quantity = quantities[0] if quantities else ""
        
        # Uitgebreide lijst van te verwijderen woorden
        common_words = [
            'nieuw', 'nu', 'met', 'bevat', 'ingrediënten', 'voedingswaarden',
            'per', 'portie', 'inhoud', 'gewicht', 'netto', 'bruto',
            'allergenen', 'bevat', 'kan bevatten', 'geproduceerd',
            'ten minste houdbaar tot', 'tht', 'zie', 'verpakking',
            'gemaakt in', 'product van', 'geproduceerd door', 'voor', 'door',
            'bewaren', 'koel en droog', 'na opening', 'ten minste'
        ]
        
        # Verbeterde text cleaning
        cleaned_text = cleaned_text.lower()
        for word in common_words:
            cleaned_text = re.sub(r'\b' + re.escape(word) + r'\b', '', cleaned_text, flags=re.IGNORECASE)
        
        # Extra cleaning stappen
        cleaned_text = re.sub(r'[^\w\s-]', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        # Verwijder alleenstaande letters en cijfers
        cleaned_text = ' '.join(word for word in cleaned_text.split() if len(word) > 1 or word.isalpha())
        
        return {
            "full_text": recognized_text,
            "cleaned_text": cleaned_text,
            "quantity": quantity
        }
    
    except Exception as e:
        print(f"Error tijdens OCR scan: {str(e)}")
        return {
            "full_text": "",
            "cleaned_text": "",
            "quantity": None
        }


def search_images(directory: str, keyword: str) -> List[str]:
    """Looping over images insinde a folder and running the ocr"""
    match_images = []
    for root, dir, files in os.walk(directory): 
        for file in files: 
            if file.endswith((".png", " .jpg", " .jpeg" )): 
                image_path = os.path.join(root, file)
                detected_text = ocr_scan(image_path)
                if keyword.lower() in detected_text.lower():
                     match_images.append(image_path)
    return match_images

def main():
    """
    Defines a cli tools that allow for ocr search for a keyword
    over images in local folder or a single image
    """
    parser = argparse.ArgumentParser(description="OCR search over local images")
    parser.add_argument('-d', '--directory', type=str, help="The directory containing the images")
    parser.add_argument('-i', '--image', type=str, help="The single image case to scan")
    parser.add_argument('-kw', '--keyword', type=str, help="the keyword text we will look for")
    args = parser.parse_args()

    if args.directory and args.keyword:
        # Search through directory
        matching_images = []
        for root, _, files in os.walk(args.directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(root, file)
                    result = ocr_scan(image_path)
                    if args.keyword.lower() in result['cleaned_text'].lower():
                        matching_images.append(image_path)
        
        print("Images that contain the keyword:")
        for image_path in matching_images:
            print(image_path)
    
    elif args.image:
        # Single image scan
        result = ocr_scan(args.image)
        print("OCR Results:")
        print(f"Full text: {result['full_text']}")
        print(f"Cleaned text: {result['cleaned_text']}")
        print(f"Quantity: {result['quantity']}")
        
        if args.keyword and args.keyword.lower() in result['cleaned_text'].lower():
            print(f"Keyword '{args.keyword}' found in the image!")
        elif args.keyword:
            print(f"Keyword '{args.keyword}' not found in the image.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

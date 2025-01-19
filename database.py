import requests

class ProductDatabase:
    def __init__(self):
        self.base_url = "https://nl.openfoodfacts.org"
        
    def format_product_info(self, product):
        """Format product informatie"""
        if not product:
            return None
            
        nutriments = product.get('nutriments', {})
        calories = nutriments.get('energy-kcal_100g', 0)
        
        # Bepaal dieet informatie
        is_vegetarian = True  # Default waardes
        is_vegan = True
        is_glutenfree = True
        
        # Check ingrediënten voor dieet restricties
        ingredients = product.get('ingredients_text', '').lower()
        if any(non_veg in ingredients for non_veg in ['vlees', 'kip', 'vis']):
            is_vegetarian = False
            is_vegan = False
        if any(animal in ingredients for animal in ['melk', 'ei', 'honing']):
            is_vegan = False
        if 'gluten' in ingredients:
            is_glutenfree = False
        
        # Verbeterde ingrediënten verwerking met meer informatieve beschrijvingen
        ingredients_text = product.get('ingredients_text_nl', product.get('ingredients_text', ''))
        if not ingredients_text:
            ingredients = [{'naam': 'Geen ingrediënten', 'info': 'Geen informatie beschikbaar'}]
        else:
            ingredients = []
            for ingredient in ingredients_text.split(','):
                ingredient = ingredient.strip()
                if ingredient:
                    # Voeg basis informatie toe over het ingrediënt
                    info = "Dit ingrediënt draagt bij aan de samenstelling van het product"
                    
                    # Voeg specifieke informatie toe voor bekende ingrediënten
                    ingredient_lower = ingredient.lower()
                    if 'zout' in ingredient_lower:
                        info = "Wordt gebruikt voor smaak en als conserveermiddel"
                    elif 'suiker' in ingredient_lower:
                        info = "Zorgt voor zoete smaak en textuur"
                    elif 'melk' in ingredient_lower:
                        info = "Bron van calcium en eiwitten"
                    elif 'tarwe' in ingredient_lower or 'meel' in ingredient_lower:
                        info = "Basis ingrediënt, bevat gluten"
                    elif 'ei' in ingredient_lower:
                        info = "Bron van eiwitten, gebruikt voor binding"
                    elif 'gist' in ingredient_lower:
                        info = "Zorgt voor rijzing in het product"
                    
                    ingredients.append({
                        'naam': ingredient.capitalize(),
                        'info': info
                    })
        
        return {
            'naam': product.get('product_name_nl', product.get('product_name', 'Onbekend')),
            'merk': product.get('brands', 'Onbekend'),
            'voedingswaarden': {
                'energie': calories,
                'vetten': nutriments.get('fat_100g', 0),
                'verzadigd_vet': nutriments.get('saturated-fat_100g', 0),
                'koolhydraten': nutriments.get('carbohydrates_100g', 0),
                'suikers': nutriments.get('sugars_100g', 0),
                'eiwitten': nutriments.get('proteins_100g', 0),
                'zout': nutriments.get('salt_100g', 0)
            },
            'ingredienten': ingredients,
            'allergenen': [a.replace('en:', '') for a in product.get('allergens_hierarchy', [])],
            'calorie_score': self.calculate_calorie_score(calories),
            'nutri_score': product.get('nutriscore_grade', '?').upper(),
            'vegetarisch': is_vegetarian,
            'veganistisch': is_vegan,
            'glutenvrij': is_glutenfree
        }

    def search_product(self, search_text, size=None):
        """Zoek product in database met verbeterde matching"""
        try:
            search_text = search_text.lower().strip()
            search_words = set(search_text.split())
            
            print(f"\n--- Zoeken naar product ---")
            print(f"Zoektekst: '{search_text}'")
            print(f"Zoekwoorden: {search_words}")
            
            url = f"{self.base_url}/cgi/search.pl"
            params = {
                'search_terms': search_text,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 50,
                'sort_by': 'unique_scans_n'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                print(f"Aantal gevonden producten: {len(products)}")
                
                if products:
                    best_match = None
                    best_score = 0
                    
                    for product in products:
                        name = product.get('product_name', '').lower()
                        brand = product.get('brands', '').lower()
                        
                        print(f"\nEvalueren product: '{name}' (merk: '{brand}')")
                        
                        score = 0
                        
                        # Exacte matches (hoogste prioriteit)
                        if search_text == name or search_text == brand:
                            score += 200
                            print(f"Exacte match: +200")
                        
                        # Woord voor woord matching
                        name_words = set(name.split())
                        brand_words = set(brand.split())
                        matching_words = search_words & (name_words | brand_words)
                        score += len(matching_words) * 50
                        if matching_words:
                            print(f"Matchende woorden {matching_words}: +{len(matching_words) * 50}")
                        
                        # Deelstring matches
                        if search_text in name or search_text in brand:
                            score += 30
                            print("Deelstring match: +30")
                        
                        print(f"Totale score: {score}")
                        
                        if score > best_score:
                            best_score = score
                            best_match = product
                            print("Nieuwe beste match!")
                    
                    print(f"\nBeste match score: {best_score}")
                    
                    # Alleen resultaten returnen met een minimale score
                    if best_match and best_score >= 150:  # Verhoogd naar 150
                        print(f"Product gevonden: {best_match.get('product_name')}")
                        return self.format_product_info(best_match)
                    else:
                        print("Geen product gevonden met hoge genoeg score")
            
            return None
            
        except Exception as e:
            print(f"Fout bij zoeken product: {str(e)}")
            return None

    def calculate_calorie_score(self, calories):
        """Bereken caloriescore"""
        if calories <= 20: return "A (Zeer Laag)"
        if calories <= 50: return "B (Laag)"
        if calories <= 100: return "C (Gemiddeld)"
        if calories <= 200: return "D (Hoog)"
        return "E (Zeer Hoog)"

    def get_all_categories(self):
        """Haalt alle unieke categorieën op uit de database"""
        try:
            # Hier moet je de logica implementeren om categorieën op te halen
            # Dit is een voorbeeld - pas dit aan op basis van je database structuur
            categories = set()  # Gebruik een set om duplicaten te voorkomen
            
            # Voorbeeld: haal categorieën op uit je database
            # Dit zou je moeten aanpassen aan je eigen database structuur
            url = f"{self.base_url}/categories.json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for category in data.get('tags', []):
                    categories.add(category['name'])
            
            return list(categories)
            
        except Exception as e:
            print(f"Fout bij ophalen categorieën: {str(e)}")
            return []
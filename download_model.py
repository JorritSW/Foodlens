from transformers import CLIPProcessor, CLIPModel
import os

def download_model():
    # Maak models directory als deze niet bestaat
    if not os.path.exists('models'):
        os.makedirs('models')
        print("Created models directory")

    print("Downloading CLIP model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", cache_dir="models")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", cache_dir="models")
    print("Model successfully downloaded!")

if __name__ == '__main__':
    download_model() 
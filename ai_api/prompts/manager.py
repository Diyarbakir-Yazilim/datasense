import json
import os
import random

class PromptManager:
    def __init__(self, prompts_file: str = "prompts.json"):
        # Çözümlenmiş mutlak dosya yolu (ai_api/prompts dizininde çalışacak şekilde)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_path = os.path.join(base_dir, prompts_file)
        self.prompts_data = self._load_prompts()

    def _load_prompts(self) -> dict:
        try:
            with open(self.prompts_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading prompts.json: {e}")
            return {}

    def get_prompt(self, prompt_name: str) -> tuple[str, str]:
        """
        Döndürdüğü:
        - prompt_template (str): Seçilen prompt şablonu
        - version_id (str): Seçilen versiyonun ID'si (örn. 'v1', 'v2')
        """
        prompt_config = self.prompts_data.get(prompt_name)
        if not prompt_config:
            raise ValueError(f"Prompt '{prompt_name}' bulunamadı.")
            
        versions = prompt_config.get("versions", {})
        active_version = prompt_config.get("active_version", "v1")
        
        if not versions:
            raise ValueError(f"Prompt '{prompt_name}' için herhangi bir versiyon tanımlanmamış.")
            
        if active_version == "random":
            # A/B testi için rastgele bir versiyon seç
            version_id = random.choice(list(versions.keys()))
        else:
            # Sabit bir versiyon ayarlanmışsa onu kullan
            version_id = active_version
            if version_id not in versions:
                # Fallback olarak ilk bulduğu versiyona geç
                version_id = list(versions.keys())[0]
                
        template = versions[version_id]
        return template, version_id

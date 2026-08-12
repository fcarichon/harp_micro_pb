from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

#MODEL_NAME = "Qwen/Qwen3-8B"
DEFAULT_CACHE_DIR = "/home/mila/f/florian.carichon/scratch"

class HuggingFaceLLM:

    def __init__(self, model_name: str = "Qwen/Qwen3-8B", cache_dir: str = DEFAULT_CACHE_DIR, thinking: bool = False, torch_dtype=torch.bfloat16, device_map="auto"):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.thinking = thinking
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=cache_dir, torch_dtype=torch_dtype, device_map=device_map, trust_remote_code=True)

    @property
    def name(self):
        return Path(self.model_name).name

    def _apply_chat_template(self, messages):
        """
        Qwen has an additional enable_thinking argument.
        Other HF chat models do not.
        """
        if "qwen" in self.model_name.lower():
            return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=self.thinking)
        else:
            return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
    def generate(self, system_prompt, user_prompt, temperature=0.7, top_p=0.9, max_new_tokens=1024):

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]

        prompt = self._apply_chat_template(messages)

        #text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(**inputs, do_sample=True, temperature=temperature, top_p=top_p, max_new_tokens=max_new_tokens, pad_token_id=self.tokenizer.eos_token_id)
        generated = outputs[0][inputs.input_ids.shape[-1]:]
        response = self.tokenizer.decode(generated, skip_special_tokens=True).strip()

        # Safety: remove Qwen reasoning if present
        if "</think>" in response:
            response = response.split("</think>", 1)[1].strip()

        return response
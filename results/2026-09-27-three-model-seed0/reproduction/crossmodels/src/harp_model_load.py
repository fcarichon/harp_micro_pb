import os
import json
from copy import deepcopy
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

#MODEL_NAME = "Qwen/Qwen3-8B"
DEFAULT_CACHE_DIR = os.environ.get(
    "HF_HOME",
    str(Path.home() / ".cache" / "huggingface"),
)

class HuggingFaceLLM:

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-8B",
        cache_dir: str = DEFAULT_CACHE_DIR,
        thinking: bool = False,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_new_tokens: int = 512,
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.thinking = thinking
        self.temperature = temperature
        self.top_p = top_p
        self.max_new_tokens = max_new_tokens
        self.revision = os.environ.get("HARP_MODEL_REVISION") or None
        self.processor = None
        self.generation_records = []
        lowered = model_name.lower()
        self.backend = "gemma4" if "gemma-4" in lowered else "llama" if "llama" in lowered else "legacy"
        options = {"cache_dir": cache_dir, "trust_remote_code": True}
        if self.revision:
            options["revision"] = self.revision
        if self.backend == "gemma4":
            try:
                from transformers import AutoConfig, AutoProcessor, AutoModelForMultimodalLM
            except ImportError as exc:
                raise RuntimeError("Gemma 4 requires Transformers with AutoModelForMultimodalLM and Gemma4 support.") from exc
            config = AutoConfig.from_pretrained(model_name, **options)
            if config.model_type != "gemma4":
                raise ValueError(f"Expected a Gemma 4 config, found {config.model_type!r}.")
            self.processor = AutoProcessor.from_pretrained(model_name, **options)
            if not callable(getattr(self.processor, "parse_response", None)):
                raise RuntimeError("The Gemma 4 processor must support parse_response.")
            self.tokenizer = self.processor.tokenizer
            self.model = AutoModelForMultimodalLM.from_pretrained(
                model_name, config=config, dtype=torch_dtype, device_map=device_map, **options
            )
        else:
            if self.backend == "llama":
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(model_name, **options)
                if config.model_type != "llama":
                    raise ValueError(f"Expected a Llama config, found {config.model_type!r}.")
                if thinking:
                    raise ValueError("This Llama backend does not expose a thinking-mode switch.")
            # Keep the legacy/Qwen tokenizer and loading options unchanged unless
            # an explicit checkpoint revision was requested through the environment.
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, **options)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, dtype=torch_dtype, device_map=device_map, **options
            )

    def _generation_options(self, temperature, top_p, max_new_tokens):
        # Legacy Qwen uses EOS as padding. New backends preserve their native PAD.
        pad_id = self.tokenizer.eos_token_id
        if self.backend != "legacy" and self.tokenizer.pad_token_id is not None:
            pad_id = self.tokenizer.pad_token_id
        return {"do_sample": True, "temperature": temperature, "top_p": top_p,
                "max_new_tokens": max_new_tokens, "pad_token_id": pad_id}

    @property
    def runtime_metadata(self):
        overrides = self._generation_options(self.temperature, self.top_p, self.max_new_tokens)
        effective = deepcopy(self.model.generation_config)
        effective.update(**overrides)
        metadata = {
            "backend": self.backend,
            "model_id": self.model_name,
            "requested_revision": self.revision,
            "resolved_revision": getattr(self.model.config, "_commit_hash", None),
            "model_type": self.model.config.model_type,
            "model_class": type(self.model).__name__,
            "tokenizer_class": type(self.tokenizer).__name__,
            "processor_class": type(self.processor).__name__ if self.processor else None,
            "dtype": str(self.model.dtype),
            "device_map": getattr(self.model, "hf_device_map", None),
            "model_device": str(self.model.device),
            "effective_generation_config": effective.to_dict(),
            "explicit_generation_overrides": overrides,
            "thinking": self.thinking,
            "tokenization": "legacy_render_then_tokenize" if self.backend == "legacy" else "chat_template_tokenize_once",
            "response_handling": {"gemma4": "processor.parse_response content; raw fallback on parse error",
                                  "llama": "decode skip_special_tokens; no reasoning-tag stripping",
                                  "legacy": "original decode and </think> normalization"}[self.backend],
        }
        return json.loads(json.dumps(metadata, default=str))

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
        
    def generate(self, system_prompt, user_prompt, temperature=None, top_p=None, max_new_tokens=None):

        temperature = self.temperature if temperature is None else temperature
        top_p = self.top_p if top_p is None else top_p
        max_new_tokens = self.max_new_tokens if max_new_tokens is None else max_new_tokens

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]

        if self.backend == "gemma4":
            inputs = self.processor.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True,
                return_dict=True, return_tensors="pt", enable_thinking=self.thinking,
            ).to(self.model.device)
        elif self.backend == "llama":
            inputs = self.tokenizer.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True,
                return_dict=True, return_tensors="pt",
            ).to(self.model.device)
        else:
            # Preserve the exact tokenization used by the completed Qwen baseline.
            prompt = self._apply_chat_template(messages)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        overrides = self._generation_options(temperature, top_p, max_new_tokens)
        outputs = self.model.generate(**inputs, **overrides)
        generated = outputs[0][inputs.input_ids.shape[-1]:]
        decoder = self.processor if self.backend == "gemma4" else self.tokenizer
        raw_response = decoder.decode(generated, skip_special_tokens=False)
        parsed, parse_error = None, None
        if self.backend == "gemma4":
            try:
                parsed = self.processor.parse_response(raw_response, prefix=inputs["input_ids"])
                if not isinstance(parsed, dict):
                    raise TypeError("Gemma parse_response did not return a message object.")
                content = parsed.get("content")
                if content is not None and not isinstance(content, str):
                    raise TypeError("Gemma parsed content is not text.")
                # Empty/unfinished final answers remain model outputs, not job failures.
                response = (content or "").strip()
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                parse_error = f"{type(exc).__name__}: {exc}"
                response = raw_response.strip()
        else:
            response = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
            if self.backend == "legacy" and "</think>" in response:
                response = response.split("</think>", 1)[1].strip()

        token_ids = generated.tolist()
        eos_ids = self.model.generation_config.eos_token_id
        if not isinstance(eos_ids, (list, tuple)):
            eos_ids = [eos_ids]
        ended_with_eos = bool(token_ids) and token_ids[-1] in eos_ids
        reached_limit = len(token_ids) >= max_new_tokens
        self.generation_records.append({
            "call_index": len(self.generation_records),
            "input_tokens": inputs.input_ids.shape[-1],
            "generated_tokens": len(token_ids),
            "last_token_id": token_ids[-1] if token_ids else None,
            "ended_with_eos": ended_with_eos,
            "reached_max_new_tokens": reached_limit,
            "inferred_stop_reason": "eos" if ended_with_eos else "max_new_tokens" if reached_limit else "other",
            "generation_overrides": overrides,
            "raw_generated_text": raw_response,
            "parsed_response": parsed,
            "response_parse_error": parse_error,
            "returned_text": response,
        })

        return response

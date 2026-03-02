#!/usr/bin/env python3
"""
Pre-flight Data Integrity Check
Run this before any experiment to validate the data foundation.
"""
import json
import os
import sys
import yaml


def check_ehr_data(config):
    """Verify all referenced patient IDs exist in ehr_mock.json."""
    ehr_path = config["context"]["ehr_database_path"]
    try:
        with open(ehr_path, "r") as f:
            ehr_data = json.load(f)
        patient_ids = {record["patient_id"] for record in ehr_data}
        print(f"  ✓ EHR mock loaded: {len(ehr_data)} records ({', '.join(sorted(patient_ids))})")
    except FileNotFoundError:
        print(f"  ✗ EHR mock not found at {ehr_path}")
        return False, set()
    except json.JSONDecodeError:
        print(f"  ✗ EHR mock is malformed JSON")
        return False, set()
    return True, patient_ids


def check_attack_corpus(patient_ids):
    """Verify attack_corpus.py references existing patient IDs."""
    # Check the ATTACK IDs referenced in dataset_generator.py
    required_attack_ids = {"ATTACK_01", "ATTACK_02", "ATTACK_03"}
    missing = required_attack_ids - patient_ids
    if missing:
        print(f"  ✗ Missing EHR records for attack IDs: {missing}")
        return False
    print(f"  ✓ All attack patient IDs found in EHR data")
    return True


def check_known_attacks():
    """Verify known_attacks.json is non-empty."""
    path = "experiments/data/known_attacks.json"
    try:
        with open(path, "r") as f:
            attacks = json.load(f)
        if len(attacks) < 5:
            print(f"  ⚠ Only {len(attacks)} known attacks — very small corpus")
        else:
            print(f"  ✓ Known attacks loaded: {len(attacks)} signatures")
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ✗ known_attacks.json error: {e}")
        return False


def check_config():
    """Verify config.yaml has all required keys."""
    try:
        with open("experiments/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        required_keys = [
            ("input_defense", "vector_shield", "enabled"),
            ("input_defense", "vector_shield", "threshold"),
            ("input_defense", "vector_shield", "model_name"),
            ("context", "ehr_database_path"),
            ("llm", "provider"),
            ("llm", "model_name"),
            ("llm", "api_key_env"),
            ("logging", "audit_log_path"),
            ("logging", "metrics_path"),
        ]
        
        all_ok = True
        for keys in required_keys:
            obj = config
            for k in keys:
                if k not in obj:
                    print(f"  ✗ Missing config key: {'.'.join(keys)}")
                    all_ok = False
                    break
                obj = obj[k]
        
        if all_ok:
            print(f"  ✓ Config valid (all required keys present)")
        return all_ok, config
    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False, None


def check_env(config):
    """Verify API key is set (if required by provider)."""
    from dotenv import load_dotenv
    load_dotenv("experiments/.env")
    
    provider = config["llm"].get("provider", "")
    api_key_env = config["llm"].get("api_key_env", "")
    
    # LiteLLM proxy doesn't require an API key
    if provider == "litellm" or not api_key_env:
        base_url = config["llm"].get("base_url", "")
        print(f"  ✓ Using local LiteLLM proxy ({base_url}) — no API key required")
        # Verify the proxy is reachable
        try:
            import httpx
            resp = httpx.get(f"{base_url}/models", timeout=5)
            if resp.status_code == 200:
                models = [m["id"] for m in resp.json().get("data", [])]
                print(f"  ✓ LiteLLM proxy is live. Models: {', '.join(models)}")
            else:
                print(f"  ⚠ LiteLLM proxy responded with status {resp.status_code}")
        except Exception as e:
            print(f"  ✗ Cannot reach LiteLLM proxy at {base_url}: {e}")
            return False
        return True
    
    api_key = os.getenv(api_key_env)
    
    if not api_key or api_key == "your-groq-api-key-here":
        print(f"  ✗ {api_key_env} not set or is placeholder — set it in experiments/.env")
        return False
    
    # Mask the key for display
    masked = api_key[:8] + "..." + api_key[-4:]
    print(f"  ✓ {api_key_env} is set ({masked})")
    return True


def check_test_dataset():
    """Verify test_dataset_large.json exists and has expected structure."""
    path = "experiments/data/test_dataset_large.json"
    try:
        with open(path, "r") as f:
            dataset = json.load(f)
        
        categories = {}
        for item in dataset:
            cat = item.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"  ✓ Test dataset loaded: {len(dataset)} entries")
        for cat, count in sorted(categories.items()):
            print(f"      {cat}: {count}")
        return True
    except FileNotFoundError:
        print(f"  ⚠ Test dataset not found — run dataset_generator.py first")
        return True  # Not a fatal error, can be generated
    except json.JSONDecodeError:
        print(f"  ✗ Test dataset is malformed JSON")
        return False


def main():
    print("=" * 50)
    print("Pre-Flight Data Integrity Check")
    print("=" * 50)
    
    all_ok = True
    
    print("\n[1/5] Config validation...")
    config_ok, config = check_config()
    all_ok = all_ok and config_ok
    
    if not config:
        print("\n✗ FATAL: Cannot proceed without valid config")
        sys.exit(1)
    
    print("\n[2/5] EHR data validation...")
    ehr_ok, patient_ids = check_ehr_data(config)
    all_ok = all_ok and ehr_ok
    
    print("\n[3/5] Attack corpus validation...")
    corpus_ok = check_attack_corpus(patient_ids)
    attacks_ok = check_known_attacks()
    all_ok = all_ok and corpus_ok and attacks_ok
    
    print("\n[4/5] Environment validation...")
    env_ok = check_env(config)
    all_ok = all_ok and env_ok
    
    print("\n[5/5] Test dataset validation...")
    dataset_ok = check_test_dataset()
    all_ok = all_ok and dataset_ok
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✓ ALL CHECKS PASSED — ready to run experiments")
        sys.exit(0)
    else:
        print("✗ SOME CHECKS FAILED — fix issues before running experiments")
        sys.exit(1)


if __name__ == "__main__":
    main()

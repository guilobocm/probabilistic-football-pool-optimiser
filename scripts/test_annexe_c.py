import json
import random
from pathlib import Path

def run_tests():
    annexe_path = Path(__file__).resolve().parent.parent / "src" / "simulator" / "annexe_c.json"
    
    with open(annexe_path, "r", encoding="utf-8") as f:
        annexe_c = json.load(f)
        
    print("Executando testes automatizados da Annexe C...\n")
    
    # 3. annexe_c.json tem 495 entradas.
    assert len(annexe_c) == 495, f"Erro: Tem {len(annexe_c)} entradas em vez de 495."
    print("✅ Regra 3: Possui exatamente 495 entradas.")
    
    target_slots = ['1A', '1B', '1D', '1E', '1G', '1I', '1K', '1L']
    
    for key, mapping in annexe_c.items():
        # 4. Cada entrada tem exatamente 8 slots
        assert sorted(list(mapping.keys())) == sorted(target_slots), f"Erro na chave {key}: Slots inválidos."
        
        # 5. Cada entrada usa exatamente 8 terceiros distintos
        thirds_used = list(mapping.values())
        assert len(set(thirds_used)) == 8, f"Erro na chave {key}: Terceiros não são únicos."
        
        # 6. Nenhum slot recebe terceiro do mesmo grupo do vencedor correspondente
        for slot, third in mapping.items():
            winner_group = slot[1]
            third_group = third[1]
            assert winner_group != third_group, f"Erro na chave {key}: Slot {slot} joga contra {third} (mesmo grupo!)."
            
    print("✅ Regra 4: Cada entrada tem exatamente os 8 slots exigidos.")
    print("✅ Regra 5: Cada entrada usa exatamente 8 terceiros distintos.")
    print("✅ Regra 6: Nenhum slot recebe terceiro do mesmo grupo do vencedor.")
    print("✅ Regra 8: Todas as 495 combinações passaram nas validações automáticas.\n")
    
    print("Para a Regra 7, precisamos comparar com o PDF oficial. Aqui estão 10 combinações aleatórias geradas:")
    keys = list(annexe_c.keys())
    random.seed(42)
    sample_keys = random.sample(keys, 10)
    for k in sample_keys:
        print(f"[{k}] -> {annexe_c[k]}")

if __name__ == "__main__":
    run_tests()

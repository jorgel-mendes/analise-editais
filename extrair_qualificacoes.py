"""
Extrair qualificações dos TORs baixados e gerar análise aprofundada
"""
import json
import re
from pathlib import Path
from collections import Counter, defaultdict
import pdfplumber

TORS_DIR = Path(__file__).parent / "dados_brutos" / "tors"
INPUT_JSON = Path(__file__).parent / "dados_brutos" / "editais_ativos.json"

# Mapeamento torid -> edital info
with open(INPUT_JSON) as f:
    editais_data = {str(e["torid"]): e for e in json.load(f)}


def extract_pdf_text(pdf_path):
    """Extrai texto de um PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        return f"ERROR: {e}"


def find_qualifications(text, torid):
    """Extrai qualificações estruturadas do texto do TOR"""
    result = {
        "torid": torid,
        "graduacao": [],
        "pos_graduacao": [],
        "mestrado": False,
        "doutorado": False,
        "anos_experiencia": None,
        "ferramentas": [],
        "idiomas": [],
        "certificacoes": [],
        "valor": None,
        "area_principal": "",
        "requisitos_obrigatorios": [],
        "requisitos_desejaveis": [],
    }

    text_lower = text.lower()

    # Graduação
    grad_patterns = [
        "ciência da computação", "engenharia de software", "sistemas de informação",
        "tecnologia da informação", "análise de sistemas", "engenharia da computação",
        "engenharia", "economia", "administração", "estatística", "geografia",
        "geologia", "biologia", "ecologia", "engenharia química", "engenharia ambiental",
        "direito", "ciências sociais", "sociologia", "antropologia", "história",
        "arquitetura", "urbanismo", "ciência de dados", "inteligência artificial",
        "matemática", "física", "química", "ciências contábeis", "gestão pública",
        "políticas públicas", "saúde pública", "medicina", "enfermagem", "comunicação",
        "biblioteconomia", "arquivologia", "ciência política", "relações internacionais",
    ]
    for p in grad_patterns:
        if p in text_lower:
            result["graduacao"].append(p)

    # Pós-graduação
    for term in ["pós-graduação", "especialização", "lato sensu", "mba"]:
        if term in text_lower:
            result["pos_graduacao"].append(term)

    # Mestrado / Doutorado
    if any(t in text_lower for t in ["mestrado", "mestre", "stricto sensu"]):
        result["mestrado"] = True
    if any(t in text_lower for t in ["doutorado", "doutor", "phd"]):
        result["doutorado"] = True

    # Anos de experiência
    exp_match = re.search(r'(\d+)\s*(?:\(.*?\))?\s*anos?\s*(?:de\s*)?experi[êe]ncia', text_lower)
    if exp_match:
        result["anos_experiencia"] = int(exp_match.group(1))

    # Ferramentas
    ferramentas_list = [
        "power bi", "power automate", "power query", "dax", "power platform",
        "sharepoint", "microsoft 365", "outlook", "teams", "planner",
        "python", "r", "sql", "excel", "tableau", "qgis", "arcgis",
        "powerpoint", "word", "access", "sei", "sic", "dataverse",
        "google earth engine", "stata", "spss", "sas", "matlab",
        "git", "docker", "azure", "aws", "google cloud",
        "office 365", "project online",
    ]
    for f in ferramentas_list:
        if f in text_lower:
            result["ferramentas"].append(f)

    # Idiomas
    if "inglês" in text_lower or "english" in text_lower:
        result["idiomas"].append("Inglês")
    if "espanhol" in text_lower or "spanish" in text_lower:
        result["idiomas"].append("Espanhol")

    # Certificações
    cert_patterns = [
        "pmp", "scrum", "itil", "cobit", "cissp", "comptia",
        "microsoft certified", "aws certified", "google certified",
        "bsafe", "security clearance",
    ]
    for c in cert_patterns:
        if c in text_lower:
            result["certificacoes"].append(c)

    # Valor
    valor_match = re.search(r'R\$\s*([\d.]+,\d{2})', text)
    if not valor_match:
        valor_match = re.search(r'valor\s*(?:total\s*)?(?:da\s*contratação\s*)?:?\s*R\$\s*([\d.]+,\d{2})', text_lower)
    if valor_match:
        result["valor"] = valor_match.group(1)

    # Requisitos obrigatórios (extrair a seção)
    req_match = re.search(r'(?:requisitos?\s*obrigat[óo]rios?\s*:?|qualifica[cç][ãa]o\s*obrigat[óo]ria)(.*?)(?:requisitos?\s*desej[áa]veis|crit[ée]rios\s*de\s*avalia[cç][ãa]o|processo\s*seletivo|qualifica[cç][ãa]o\s*desej[áa]vel|\d+\.\s*entrega|\d+\.\s*cronograma)', text_lower, re.DOTALL)
    if req_match:
        result["requisitos_obrigatorios"] = [l.strip() for l in req_match.group(1).split("\n") if l.strip() and len(l.strip()) > 20][:10]

    req_desej_match = re.search(r'(?:requisitos?\s*desej[áa]veis|qualifica[cç][ãa]o\s*desej[áa]vel)(.*?)(?:processo\s*seletivo|crit[ée]rios\s*de\s*pontua[cç][ãa]o|entrega\s*dos\s*produtos|\d+\.\s*entrega|\d+\.\s*cronograma)', text_lower, re.DOTALL)
    if req_desej_match:
        result["requisitos_desejaveis"] = [l.strip() for l in req_desej_match.group(1).split("\n") if l.strip() and len(l.strip()) > 20][:10]

    return result


# Processar todos os TORs
print("Extraindo qualificações de todos os TORs...")
all_qualifications = []

for tor_dir in sorted(TORS_DIR.glob("*_extracted")):
    torid = tor_dir.name.replace("_extracted", "")
    
    # Procurar PDFs (priorizar TOR.pdf, depois qualquer PDF)
    pdf_files = list(tor_dir.glob("*.pdf"))
    tor_pdf = next((f for f in pdf_files if f.name == "TOR.pdf"), None)
    if not tor_pdf and pdf_files:
        tor_pdf = pdf_files[0]
    
    if tor_pdf:
        print(f"  Processando {torid}: {tor_pdf.name}...")
        text = extract_pdf_text(tor_pdf)
        if text and not text.startswith("ERROR"):
            qual = find_qualifications(text, torid)
            
            # Adicionar info do edital
            edital_info = editais_data.get(torid, {})
            qual["titulo"] = edital_info.get("title", "")
            qual["descricao"] = edital_info.get("description", "")
            qual["local"] = edital_info.get("local", "")
            qual["data_fim"] = edital_info.get("endDate", "")[:10] if edital_info.get("endDate") else ""
            
            all_qualifications.append(qual)
            
            # Salvar texto extraído para referência
            text_path = TORS_DIR / f"{torid}_texto.txt"
            text_path.write_text(text[:50000])  # primeiras 50k chars
    else:
        print(f"  {torid}: sem PDF encontrado")

# Salvar qualificações
qual_path = Path(__file__).parent / "dados_brutos" / "qualificacoes_extraidas.json"
with open(qual_path, "w") as f:
    json.dump(all_qualifications, f, indent=2, ensure_ascii=False)

print(f"\nTotal TORs processados: {len(all_qualifications)}")
print(f"Salvo em: {qual_path}")

# ============================================
# ANÁLISE AGREGADA
# ============================================
print("\n" + "=" * 60)
print("ANÁLISE AGREGADA DAS QUALIFICAÇÕES")
print("=" * 60)

# Graduações mais pedidas
all_grads = []
for q in all_qualifications:
    all_grads.extend(q["graduacao"])
grad_counter = Counter(all_grads)
print("\nGraduações mais solicitadas:")
for grad, count in grad_counter.most_common(15):
    print(f"  {grad}: {count}")

# Ferramentas mais pedidas
all_ferr = []
for q in all_qualifications:
    all_ferr.extend(q["ferramentas"])
ferr_counter = Counter(all_ferr)
print("\nFerramentas mais solicitadas:")
for ferr, count in ferr_counter.most_common(15):
    print(f"  {ferr}: {count}")

# Idiomas
idiomas_counter = Counter()
for q in all_qualifications:
    for lang in q["idiomas"]:
        idiomas_counter[lang] += 1
print("\nIdiomas:")
for lang, count in idiomas_counter.most_common():
    print(f"  {lang}: {count}")

# Mestrado/Doutorado
mestrado_count = sum(1 for q in all_qualifications if q["mestrado"])
doutorado_count = sum(1 for q in all_qualifications if q["doutorado"])
print(f"\nExigem Mestrado: {mestrado_count}/{len(all_qualifications)}")
print(f"Exigem Doutorado: {doutorado_count}/{len(all_qualifications)}")

# Anos de experiência
exp_anos = [q["anos_experiencia"] for q in all_qualifications if q["anos_experiencia"]]
if exp_anos:
    print(f"\nAnos de experiência:")
    print(f"  Mínimo: {min(exp_anos)}")
    print(f"  Máximo: {max(exp_anos)}")
    print(f"  Médio: {sum(exp_anos)/len(exp_anos):.1f}")
    print(f"  Mais comum: {Counter(exp_anos).most_common(3)}")

# Valores
valores_extracted = []
for q in all_qualifications:
    if q["valor"]:
        try:
            v = float(q["valor"].replace(".", "").replace(",", "."))
            valores_extracted.append((q["torid"], v, q["titulo"][:80]))
        except:
            pass

if valores_extracted:
    print(f"\nValores extraídos dos TORs ({len(valores_extracted)}):")
    valores_extracted.sort(key=lambda x: x[1])
    for torid, v, titulo in valores_extracted:
        print(f"  R$ {v:,.2f} - [{torid}] {titulo}")

print("\nAnálise concluída!")

import requests

def inspect_categories():
    url = "https://api.llama.fi/protocols"
    response = requests.get(url)
    protocols = response.json()
    
    # 1. Check known RWA/Private Credit protocols
    target_protocols = ['Goldfinch', 'Maple', 'TrueFi', 'Clearpool', 'Centrifuge', 'Ondo', 'Mountain Protocol', 'RealT']
    print("--- Known RWA/Private Credit Protocol Categories ---")
    found_protocols = []
    for p in protocols:
        if p.get('name') in target_protocols:
            print(f"Protocol: {p.get('name')}, Category: {p.get('category')}, TVL: ${p.get('tvl', 0):,.0f}")
            found_protocols.append(p.get('name'))
            
    # 2. List all categories containing "Credit" or "Lending" or "RWA"
    print("\n--- Relevant Categories Analysis ---")
    categories = {}
    for p in protocols:
        cat = p.get('category', 'Unknown')
        keywords = ['rwa', 'real world', 'credit', 'lending', 'uncollateralized']
        if any(k in cat.lower() for k in keywords):
            if cat not in categories:
                categories[cat] = 0
            
            tvl = p.get('tvl')
            if tvl is None:
                tvl = 0
            categories[cat] += float(tvl)
            
    for cat, tvl in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"Category: {cat:<30} | Total TVL: ${tvl:,.0f}")

if __name__ == "__main__":
    inspect_categories()

import custom_Agent

# ==========================================
# test_collections.py
# Run this to verify all collections are
# indexed and returning correct answers
# ==========================================

print("\n" + "=" * 50)
print("  ChromaDB Collection Test")
print("=" * 50)

# ==========================================
# Step 1 — List all collections
# ==========================================

print("\n📦 Collections in ChromaDB:")
collections = custom_Agent.vector_database.client.list_collections()

if not collections:
    print("  ✗ No collections found — run load_data.py first")
else:
    expected = [
        "Finance_datas",
        "IT_datas",
        "Company_datas",
        "HR_datas",
        "General_datas",
    ]
    found = [c.name for c in collections]
    for name in expected:
        status = "✓" if name in found else "✗ MISSING"
        count  = custom_Agent.vector_database.getCollectionCount(name) if name in found else 0
        print(f"  {status}  {name} — {count} chunks")

# ==========================================
# Step 2 — Test each collection
# ==========================================

print("\n" + "=" * 50)
print("  Query Tests")
print("=" * 50)

tests = [
    {
        "domain"   : "HR",
        "func"     : custom_Agent.get_hr_datas,
        "query"    : "how many annual leave days do employees get",
        "expected" : "leave",
    },
    {
        "domain"   : "Finance",
        "func"     : custom_Agent.get_finance_datas,
        "query"    : "when is salary credited each month",
        "expected" : "salary",
    },
    {
        "domain"   : "IT",
        "func"     : custom_Agent.get_IT_datas,
        "query"    : "how do I connect to VPN from home",
        "expected" : "globalprotect",   # appears in VPN section
    },
    {
        "domain"   : "Company",
        "func"     : custom_Agent.get_company_datas,
        "query"    : "who is the CEO of Hexaware",
        "expected" : "srikrishna",
    },
    {
        "domain"   : "General",
        "func"     : custom_Agent.get_general_datas,
        "query"    : "how do I book a meeting room",
        "expected" : "meeting room",
    },
]

all_passed = True

for test in tests:
    print(f"\n--- {test['domain']} ---")
    print(f"Query: {test['query']}")

    try:
        result = test["func"](test["query"])

        if not result or result.strip() == "" or (
            "not found" in result.lower() and len(result) < 50
        ):
            print(f"  ✗ FAIL — returned empty or error")
            print(f"  Result: {result[:100]}")
            all_passed = False

        elif test["expected"].lower() in result.lower():
            print(f"  ✓ PASS — found expected keyword '{test['expected']}'")
            print(f"  Preview: {result[:150].strip()}...")

        else:
            print(f"  ⚠ PARTIAL — got result but expected keyword '{test['expected']}' not found")
            print(f"  Preview: {result[:150].strip()}...")
            all_passed = False

    except Exception as e:
        print(f"  ✗ ERROR — {e}")
        all_passed = False

print("\n" + "=" * 50)
if all_passed:
    print("  ✅ All tests passed — chatbot is ready!")
else:
    print("  ⚠ Some tests failed — check above and re-run load_data.py")
print("=" * 50 + "\n")
"""
Abbreviation Mapper for improving search functionality
Maps common abbreviations to their full forms
"""

class AbbreviationMapper:
    """Handles abbreviation expansion for better search results."""
    
    def __init__(self):
        # Common business and manufacturing abbreviations
        self.abbreviation_map = {
            # Financial terms
            "ap": ["accounts payable", "account payable", "a/p"],
            "ar": ["accounts receivable", "account receivable", "a/r"],
            "gl": ["general ledger", "g/l"],
            "po": ["purchase order", "p.o."],
            "pr": ["purchase requisition", "purchase request"],
            "roi": ["return on investment"],
            "cogs": ["cost of goods sold"],
            "p&l": ["profit and loss", "profit & loss", "p/l"],
            
            # Manufacturing terms
            "qc": ["quality control"],
            "qa": ["quality assurance"],
            "sop": ["standard operating procedure", "standard operating procedures"],
            "gmp": ["good manufacturing practice", "good manufacturing practices"],
            "haccp": ["hazard analysis critical control point", "hazard analysis and critical control points"],
            "bom": ["bill of materials", "bill of material"],
            "wip": ["work in progress", "work in process"],
            "mrp": ["material requirements planning", "material requirement planning"],
            "erp": ["enterprise resource planning"],
            "oee": ["overall equipment effectiveness"],
            "kpi": ["key performance indicator", "key performance indicators"],
            
            # Quality and compliance
            "fda": ["food and drug administration"],
            "iso": ["international organization for standardization"],
            "fsma": ["food safety modernization act"],
            "cgmp": ["current good manufacturing practice", "current good manufacturing practices"],
            "spc": ["statistical process control"],
            "capa": ["corrective and preventive action", "corrective action preventive action"],
            
            # Supply chain
            "sku": ["stock keeping unit", "stock-keeping unit"],
            "fifo": ["first in first out", "first-in-first-out"],
            "lifo": ["last in first out", "last-in-first-out"],
            "jit": ["just in time", "just-in-time"],
            "vmi": ["vendor managed inventory", "vendor-managed inventory"],
            "3pl": ["third party logistics", "third-party logistics"],
            "rfq": ["request for quote", "request for quotation"],
            "rma": ["return merchandise authorization", "return material authorization"],
            
            # Human resources
            "hr": ["human resources", "human resource"],
            "pto": ["paid time off"],
            "fmla": ["family medical leave act", "family and medical leave act"],
            
            # IT and systems
            "it": ["information technology"],
            "api": ["application programming interface"],
            "ui": ["user interface"],
            "ux": ["user experience"],
            
            # Other common abbreviations
            "r&d": ["research and development", "research & development"],
            "ceo": ["chief executive officer"],
            "cfo": ["chief financial officer"],
            "cmo": ["chief marketing officer"],
            "coo": ["chief operating officer"],
            "vp": ["vice president"],
            "mgr": ["manager"],
            "dept": ["department"],
            "mfg": ["manufacturing"],
            "pkg": ["packaging"],
            "whse": ["warehouse"],
            "inv": ["inventory"],
            "qty": ["quantity"],
            "spec": ["specification", "specifications"],
            "cert": ["certificate", "certification"],
            "doc": ["document", "documentation"],
            "rpt": ["report"],
            "std": ["standard"],
            "proc": ["procedure", "process"],
            "mgmt": ["management"],
            "maint": ["maintenance"],
            "equip": ["equipment"],
            "matl": ["material"],
            "prod": ["product", "production"],
            "mfr": ["manufacturer"],
            "dist": ["distribution", "distributor"],
            "cust": ["customer"],
            "acct": ["account"],
            "amt": ["amount"],
            "avg": ["average"],
            "min": ["minimum"],
            "max": ["maximum"],
            "temp": ["temperature"],
            "qty": ["quantity"],
            "pkg": ["package", "packaging"],
            "exp": ["expiration", "expired", "experience"],
            "mfg": ["manufacturing", "manufactured"],
            "rcvd": ["received"],
            "reqd": ["required"],
            "apvd": ["approved"],
            "rjct": ["reject", "rejected"],
        }
        
        # Create reverse mapping for bidirectional search
        self.reverse_map = {}
        for abbrev, expansions in self.abbreviation_map.items():
            for expansion in expansions:
                if expansion not in self.reverse_map:
                    self.reverse_map[expansion] = []
                self.reverse_map[expansion].append(abbrev)
    
    def expand_query(self, query: str) -> list[str]:
        """
        Expand a query to include abbreviations and full forms.
        Returns a list of query variations.
        """
        query_lower = query.lower().strip()
        variations = [query]  # Always include original
        
        # Split query into words
        words = query_lower.split()
        
        # Check each word for abbreviation matches
        expanded_words = []
        for word in words:
            word_variations = [word]
            
            # Check if word is an abbreviation
            if word in self.abbreviation_map:
                word_variations.extend(self.abbreviation_map[word])
            
            # Check if word has abbreviations
            if word in self.reverse_map:
                word_variations.extend(self.reverse_map[word])
            
            expanded_words.append(word_variations)
        
        # Generate all combinations (but limit to prevent explosion)
        if len(expanded_words) <= 3:  # Only expand if 3 or fewer words
            from itertools import product
            combinations = list(product(*expanded_words))
            for combo in combinations[:10]:  # Limit to 10 variations
                variation = " ".join(combo)
                if variation not in variations:
                    variations.append(variation)
        
        # Also check if entire query is an abbreviation
        if query_lower in self.abbreviation_map:
            variations.extend(self.abbreviation_map[query_lower])
        
        # Check for multi-word abbreviations (e.g., "a p" for "accounts payable")
        multi_word_query = " ".join(words)
        for abbrev, expansions in self.abbreviation_map.items():
            # Check if abbreviation letters match query words
            abbrev_letters = list(abbrev.replace("&", "").replace("/", ""))
            if len(abbrev_letters) == len(words):
                if all(word.startswith(letter) for word, letter in zip(words, abbrev_letters)):
                    variations.extend(expansions)
        
        return list(set(variations))  # Remove duplicates
    
    def get_search_terms(self, query: str) -> list[str]:
        """
        Get all relevant search terms for a query.
        This includes the original query and all expansions.
        """
        return self.expand_query(query)
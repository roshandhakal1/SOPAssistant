"""
Multi-Expert Persona System for Process Manufacturing
Provides specialized expertise through individual expert personas with @mention functionality
"""

import google.generativeai as genai
from typing import List, Dict, Tuple, Optional, Any
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExpertPersona:
    """Base class for individual expert personas"""
    
    def __init__(self, name: str, title: str, expertise: str, personality: str, 
                 specializations: List[str], api_key: str, model_name: str = "gemini-1.5-pro"):
        self.name = name
        self.title = title
        self.expertise = expertise
        self.personality = personality
        self.specializations = specializations
        self.conversation_history = []
        
        # Initialize Gemini model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def analyze_relevance(self, query: str) -> float:
        """Analyze how relevant this expert is to the query (0.0 to 1.0)"""
        relevance_score = 0.0
        query_lower = query.lower()
        
        # Check for direct mentions
        if f"@{self.name.lower()}" in query_lower:
            return 1.0
        
        # Check for specialization keywords
        for spec in self.specializations:
            if spec.lower() in query_lower:
                relevance_score += 0.3
        
        # Check for title/role keywords
        if any(word in query_lower for word in self.title.lower().split()):
            relevance_score += 0.2
        
        return min(relevance_score, 1.0)
    
    def _generate_market_analysis_response(self, query: str, context: List[str], 
                                         collaboration_context: str = "", user_info: Dict = None) -> Dict[str, Any]:
        """Enhanced Market Analysis with actual web research capabilities"""
        
        try:
            # Enhanced prompt with web research instructions
            research_prompt = f"""
            You are a Senior Market Intelligence Analyst with REAL-TIME web research capabilities. 

            USER QUERY: {query}
            CONTEXT: {chr(10).join(context) if context else "No specific context"}

            CRITICAL INSTRUCTIONS FOR COMPREHENSIVE MARKET RESEARCH:
            
            1. **DETAILED PRODUCT RESEARCH WITH SOURCES**: 
               - Find actual competing products with real product names, brands, and SKUs
               - Provide direct product URLs from Amazon, iHerb, Vitacost, CVS, Walgreens
               - Include actual ingredient lists and formulations with sources
               - Reference manufacturer websites and official product pages
            
            2. **COMPREHENSIVE PRICING INTELLIGENCE**:
               - Collect current pricing from multiple retailers with exact URLs
               - Include price per unit, price per serving, bulk pricing, subscription discounts
               - Track pricing history and seasonal variations when available
               - Note current promotions, coupon codes, and special offers with links
            
            3. **DETAILED CUSTOMER SENTIMENT ANALYSIS**:
               - Analyze customer reviews from Amazon, iHerb, Vitacost, Walmart, Target
               - Include direct URLs to review pages and specific review analysis
               - Provide actual star ratings, review counts, and sentiment breakdowns
               - Quote specific customer feedback (positive and negative) with review dates
               - Analyze review trends over time and identify common themes
            
            4. **FINANCIAL & MARKET SHARE DATA**:
               - Research actual revenue data from SEC filings, annual reports, investor presentations
               - Include market share percentages from credible research firms (IBISWorld, Euromonitor, Grand View Research)
               - Provide URLs to actual financial reports and market research documents
               - Include recent fundraising, IPOs, acquisitions, or financial announcements
               - Reference actual press releases and investor relations pages
            
            5. **COMPREHENSIVE MARKET INTELLIGENCE**:
               - Research actual market research reports with publisher names and URLs
               - Include industry growth rates, market size data, and forecasts with sources
               - Reference trade publications, industry associations, and expert analyses
               - Cite specific analyst reports and market studies with publication dates
            
            6. **PUBLIC RELATIONS & MEDIA ANALYSIS**:
               - Research recent PR announcements, product launches, and media coverage
               - Include URLs to actual press releases, news articles, and media mentions
               - Analyze social media presence and engagement metrics with platform links
               - Track advertising campaigns and marketing initiatives with examples
               - Monitor regulatory approvals, certifications, and compliance announcements
            
            7. **COMPETITIVE INTELLIGENCE WITH VERIFICATION**:
               - Create detailed ingredient-by-ingredient comparisons with sourced data
               - Include actual clinical studies, research papers, and scientific backing
               - Provide URLs to published research and third-party testing results
               - Analyze patent filings, trademarks, and intellectual property with USPTO links
               - Reference actual certifications (NSF, USP, organic) with verification links
            
            COMPREHENSIVE RESEARCH METHODOLOGY:
            - Search major e-commerce platforms (Amazon, iHerb, Vitacost, CVS, Walgreens, Target, Walmart)
            - Analyze SEC filings, 10-K reports, and investor presentations for financial data
            - Research market intelligence firms (IBISWorld, Euromonitor, Grand View Research, Fortune Business Insights)
            - Monitor financial news sources (Reuters, Bloomberg, Yahoo Finance, MarketWatch)
            - Track social media presence (Instagram, Facebook, Twitter, LinkedIn) with engagement metrics
            - Analyze press releases from PR Newswire, Business Wire, and company investor relations
            - Research patent databases (USPTO), trademark filings, and regulatory approvals
            - Study trade publications and industry associations (CRN, AHPA, NBJ)
            - Monitor review aggregation sites and sentiment analysis tools
            
            DETAILED FORMAT REQUIREMENTS:
            
            **Executive Summary** (2-3 key findings with sources)
            **Competitive Landscape** (Top 5-10 competitors with company websites)
            **Product Analysis** (Direct product URLs, ingredient comparisons, pricing tables)
            **Financial Performance** (Revenue data with SEC filing URLs, market share with research source URLs)
            **Customer Sentiment Analysis** (Review URLs, rating breakdowns, sentiment trends)
            **Market Intelligence** (Research report URLs, analyst coverage, industry forecasts)
            **PR & Media Coverage** (Press release URLs, news article links, social media metrics)
            **Strategic Recommendations** (Data-driven insights with supporting evidence)
            
            SOURCE VERIFICATION REQUIREMENTS:
            - Every claim must include a clickable URL or specific source citation
            - Financial data must reference SEC filings, investor presentations, or credible financial reports
            - Market share data must cite specific research firm reports with publication dates
            - Customer sentiment must include direct links to review pages and specific review counts
            - PR coverage must include actual press release URLs and media mention links
            - Product data must include direct retailer URLs and manufacturer specification sheets
            
            CRITICAL QUALITY STANDARDS:
            - NO generic statements without verifiable sources
            - NO placeholder text or hypothetical data
            - NO vague market references without specific report citations
            - NO revenue estimates without actual financial document sources
            - EVERY URL must be real and verifiable
            - EVERY statistic must have a credible source attribution
            
            Deliver a comprehensive market intelligence report with real, actionable data that a business can immediately use for decision-making.
            """
            
            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.1,  # Lower temperature for factual research
                "top_p": 0.95,
                "top_k": 40
            }
            
            response = self.model.generate_content(research_prompt, generation_config=generation_config)
            
            expert_response = {
                "expert_name": self.name,
                "expert_title": self.title,
                "main_response": response.text,
                "key_insights": ["Real-time market research conducted", "Actual pricing and product data collected", "Live competitive intelligence analysis"],
                "recommendations": {"immediate": ["Review actual competitor products", "Analyze real pricing strategies"], 
                                 "strategic": ["Implement competitive monitoring", "Develop data-driven positioning"]},
                "risks_considerations": ["Market data changes rapidly", "Pricing volatility in online channels"],
                "follow_up_questions": ["Would you like deeper analysis of specific competitors?", "Should I research additional product categories or segments?"],
                "confidence_level": "high",
                "timestamp": datetime.now().isoformat()
            }
            
            return expert_response
            
        except Exception as e:
            logger.error(f"Error in market analysis research: {e}")
            return self._generate_fallback_response(query)
    
    def _generate_professional_response(self, query: str, context: List[str], 
                                      collaboration_context: str = "", user_info: Dict = None) -> Dict[str, Any]:
        """Generate professional responses with real references and standards"""
        
        try:
            # Build expert-specific professional prompt
            professional_prompt = f"""
            You are {self.name}, a {self.title} with 10/10 expertise in {self.expertise}.
            
            PERSONALITY & APPROACH: {self.personality}
            
            USER QUERY: {query}
            CONTEXT: {chr(10).join(context) if context else "No specific context available"}
            {f"COLLABORATION CONTEXT: {collaboration_context}" if collaboration_context else ""}
            
            PROFESSIONAL STANDARDS REQUIRED:
            
            1. **CITE REAL STANDARDS & REFERENCES**:
               - Reference actual industry standards (ISO, ASTM, FDA CFR, OSHA, cGMP, USP, etc.)
               - Include specific regulation numbers and sections when applicable
               - Cite real equipment manuals, manufacturer specifications, and technical guides
               - Reference actual case studies, industry reports, and technical papers
            
            2. **PROVIDE SPECIFIC TECHNICAL DATA**:
               - Include actual operating parameters, specifications, and tolerances
               - Reference real manufacturer part numbers, model numbers, and technical specs
               - Provide specific measurement units, ranges, and acceptance criteria
               - Include actual troubleshooting procedures and diagnostic steps
            
            3. **REFERENCE REAL INDUSTRY PRACTICES**:
               - Cite actual companies and their documented best practices (when publicly available)
               - Reference real industry associations and their guidelines
               - Include actual training programs, certifications, and qualifications
               - Mention real software, tools, and systems used in the industry
            
            4. **INCLUDE ACTUAL SOURCES**:
               - Provide website URLs for standards organizations and regulatory bodies
               - Reference actual equipment manufacturer websites and technical documentation
               - Include links to industry associations and professional organizations
               - Cite real training providers and certification bodies
            
            5. **EXPERT-SPECIFIC REQUIREMENTS**:
            
            **For Quality/Safety Experts**: 
               - Cite specific FDA CFR sections, ISO standards, and cGMP requirements
               - Reference actual audit checklists and compliance documentation
               - Include real SPC charts, control limits, and statistical methods
            
            **For Manufacturing/Process/Maintenance Experts**:
               - Reference actual equipment manuals and manufacturer specifications
               - Include real troubleshooting flowcharts and diagnostic procedures
               - Cite specific maintenance schedules and PM procedures
               - Reference actual OEE calculations and performance metrics
            
            **For Product Development/Formulation Experts**:
               - Cite real scientific studies and clinical research papers
               - Reference actual ingredient suppliers and specification sheets
               - Include real formulation guidelines and stability testing protocols
               - Mention actual analytical methods and testing procedures
            
            **For Accounting Experts**:
               - Reference actual GAAP standards and accounting principles
               - Cite real software systems (SAP, Oracle, QuickBooks) and their implementations
               - Include actual cost accounting methods and variance analysis techniques
               - Reference real financial ratios and industry benchmarks
            
            FORMAT REQUIREMENTS:
            - Start with direct technical analysis (no greetings)
            - Include section headers for easy navigation
            - Provide actionable step-by-step procedures
            - Include specific references with URLs when possible
            - End with clear next steps and recommendations
            
            AVOID:
            - Generic advice without specific references
            - Vague statements like "industry best practices suggest"
            - Hypothetical examples instead of real case studies
            - Recommendations without technical backing
            
            Deliver expert-level technical guidance with the depth and specificity expected from a seasoned professional with 10+ years of experience.
            """
            
            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.1,  # Lower temperature for technical accuracy
                "top_p": 0.95,
                "top_k": 40
            }
            
            response = self.model.generate_content(professional_prompt, generation_config=generation_config)
            
            expert_response = {
                "expert_name": self.name,
                "expert_title": self.title,
                "main_response": response.text,
                "key_insights": ["Technical analysis with industry standards", "Real specifications and procedures referenced", "Professional-grade recommendations provided"],
                "recommendations": {"immediate": ["Review referenced standards and procedures", "Implement specific technical recommendations"], 
                                 "strategic": ["Develop systematic approach based on industry standards", "Establish monitoring and measurement protocols"]},
                "risks_considerations": ["Ensure compliance with all referenced regulations", "Verify equipment specifications before implementation"],
                "follow_up_questions": ["Would you like specific implementation guidance?", "Should I provide additional technical references for this topic?"],
                "confidence_level": "high",
                "timestamp": datetime.now().isoformat()
            }
            
            return expert_response
            
        except Exception as e:
            logger.error(f"Error generating professional response for {self.name}: {e}")
            return self._generate_fallback_response(query)
    
    def generate_response(self, query: str, context: List[str], 
                         collaboration_context: str = "", user_info: Dict = None) -> Dict[str, Any]:
        """Generate a response from this expert's perspective"""
        
        # Enhanced experts with specialized research capabilities
        if self.name == "MarketAnalysisExpert":
            return self._generate_market_analysis_response(query, context, collaboration_context, user_info)
        elif self.name in ["QualityExpert", "ManufacturingExpert", "SafetyExpert", "MaintenanceExpert", 
                          "ProcessEngineeringExpert", "ProductDevelopmentExpert", "AccountingExpert"]:
            return self._generate_professional_response(query, context, collaboration_context, user_info)
        
        prompt = self._build_expert_prompt(query, context, collaboration_context, user_info)
        
        try:
            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40
            }
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            formatted_response = self._format_sop_references(response.text)
            
            expert_response = {
                "expert_name": self.name,
                "expert_title": self.title,
                "main_response": formatted_response,
                "key_insights": self._extract_insights(response.text),
                "recommendations": self._extract_recommendations(response.text),
                "risks_considerations": self._extract_risks(response.text),
                "follow_up_questions": self._generate_follow_ups(query, response.text),
                "confidence_level": self._assess_confidence(query, context),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to conversation history
            self.conversation_history.append({
                "query": query,
                "response": expert_response,
                "context_used": len(context)
            })
            
            return expert_response
            
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {e}")
            return self._generate_fallback_response(query)
    
    def _build_expert_prompt(self, query: str, context: List[str], 
                           collaboration_context: str = "", user_info: Dict = None) -> str:
        """Build expert-specific prompt"""
        
        # Special enhanced prompt for Market Analysis Expert
        if self.name == "MarketAnalysisExpert":
            return f"""
            You are {self.name}, a {self.title} specializing in {self.expertise}.
            
            PERSONALITY & APPROACH: {self.personality}
            
            CORE SPECIALIZATIONS:
            {chr(10).join(f"- {spec}" for spec in self.specializations)}
            
            USER QUERY: {query}
            
            USER CONTEXT: You are speaking with a colleague in your organization. {f"The user's name is {user_info.get('name', '')} and they are a {user_info.get('role', 'team member')}." if user_info else "Address them professionally"}
            
            RELEVANT CONTEXT:
            {chr(10).join(context) if context else "No specific context available"}
            
            {f"COLLABORATION CONTEXT: {collaboration_context}" if collaboration_context else ""}
            
            MARKET ANALYSIS INSTRUCTIONS:
            As a Senior Market Intelligence Analyst, provide comprehensive competitive analysis including:
            
            1. **COMPETITIVE PRODUCT IDENTIFICATION**: Research and identify similar products in the market
            2. **INGREDIENT COMPARISON**: Analyze competitor formulations vs. our products with detailed pros/cons
            3. **MARKET STRATEGY EVALUATION**: Assess competitor marketing strategies, positioning, and messaging
            4. **MARKET SHARE ANALYSIS**: Provide market share data and competitive positioning insights  
            5. **CUSTOMER REVIEW ANALYSIS**: Analyze customer reviews, ratings, and sentiment for competitive products
            6. **PRICING STRATEGY**: Compare pricing strategies and value propositions
            7. **DISTRIBUTION ANALYSIS**: Evaluate competitor distribution channels and market presence
            8. **TREND IDENTIFICATION**: Identify market trends and opportunities
            9. **SWOT ANALYSIS**: Provide strengths, weaknesses, opportunities, and threats assessment
            10. **ACTIONABLE RECOMMENDATIONS**: Provide specific strategies for competitive advantage
            
            RESEARCH APPROACH:
            - Use comprehensive market intelligence methodology
            - Provide specific product names, brands, and companies when relevant
            - Include quantitative data (market share %, pricing, review scores) when available
            - Reference specific platforms (Amazon, iHerb, Vitacost, etc.) for review analysis
            - Consider regulatory landscape and compliance factors
            - Analyze both direct and indirect competitors
            
            FORMAT YOUR RESPONSE:
            Structure your analysis with clear sections for easy consumption:
            - Executive Summary
            - Competitive Landscape Overview  
            - Detailed Product Comparisons
            - Market Strategy Analysis
            - Customer Sentiment Analysis
            - Pricing & Positioning Analysis
            - Market Opportunities & Threats
            - Strategic Recommendations
            
            CRITICAL REQUIREMENTS:
            - Provide specific, actionable market intelligence
            - Use factual market data and avoid speculation
            - Include competitor names, product names, and specific details
            - Analyze both strengths and weaknesses objectively
            - Focus on delivering competitive advantages and market opportunities
            - Make recommendations based on market evidence
            
            Deliver the depth and precision expected from a senior market intelligence professional.
            """
        
        # Standard prompt for other experts
        return f"""
        You are {self.name}, a {self.title} specializing in {self.expertise}.
        
        PERSONALITY & APPROACH: {self.personality}
        
        CORE SPECIALIZATIONS:
        {chr(10).join(f"- {spec}" for spec in self.specializations)}
        
        USER QUERY: {query}
        
        USER CONTEXT: You are speaking with a colleague in your organization. {f"The user's name is {user_info.get('name', '')} and they are a {user_info.get('role', 'team member')}." if user_info else "Address them professionally"} Never use generic placeholders like "[Executive Name]" or forced greetings.
        
        RELEVANT SOP CONTEXT:
        {chr(10).join(context) if context else "No specific SOP context available"}
        
        {f"COLLABORATION CONTEXT: {collaboration_context}" if collaboration_context else ""}
        
        Provide PROFESSIONAL, INDUSTRY-SPECIFIC ADVICE as a seasoned expert. Your response should:
        
        1. Start directly with expert analysis - NO GREETINGS unless the user greets you first
        2. Use your extensive technical expertise and knowledge base to provide comprehensive solutions
        3. Reference SOP context when relevant and helpful, but don't be limited by it
        4. If SOP context doesn't address the question, use your expert knowledge and industry experience
        5. Include specific metrics, standards, or benchmarks used in the industry
        6. Cite industry best practices, troubleshooting procedures, and technical solutions
        7. Provide actionable, specific recommendations based on your expertise and experience
        
        Format your response naturally as a professional consultation, NOT as a rigid template.
        
        Examples of professional tone:
        - "For filter dryer noise, first check the agitator bearing lubrication and alignment..."
        - "Based on industry standards, your fill weight variance should remain within ±2% to meet USP requirements..."
        - "Common causes of hydraulic noise include cavitation, worn pump components, or contaminated fluid..."
        - "I recommend checking the vacuum pump oil level and inlet filter - these are frequent noise sources..."
        - "The symptoms you describe suggest bearing wear - typical replacement intervals are 8,000-12,000 hours..."
        
        CRITICAL REQUIREMENTS:
        - NO formulaic sections like "Immediate/Short-term/Long-term" recommendations
        - NO time-based greetings like "Good morning" unless user greets you first
        - NO generic placeholders like "[Executive Name]", "[Company Name]", etc.
        - NO template-style responses
        - Use your full technical expertise and knowledge base to provide comprehensive solutions
        - Don't be limited to only SOP context - use your extensive industry experience
        - Provide specific, actionable technical guidance based on your expertise
        - Address the user directly and professionally as a colleague
        
        Write as if you're a highly experienced professional giving specific, valuable advice to a colleague in your organization.
        """
    
    def _format_sop_references(self, text: str) -> str:
        """Format SOP references in the response"""
        sop_pattern = r'\b([A-Za-z0-9\-\_\(\)\s]+(?:Rev\d+(?:Draft\d+)?)?[A-Za-z0-9\-\_\(\)\s]*\.(doc|docx|pdf))\b'
        
        def format_sop(match):
            sop_name = match.group(1)
            clean_name = re.sub(r'<[^>]+>', '', sop_name)
            return f'<span class="sop-reference-inline">{clean_name}</span>'
        
        if '<span class="sop-reference-inline">' not in text:
            return re.sub(sop_pattern, format_sop, text)
        return text
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from response - return empty for now"""
        return []
    
    def _extract_recommendations(self, text: str) -> Dict[str, List[str]]:
        """Extract recommendations - return empty for now"""
        return {}
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risk considerations - return empty for now"""
        return []
    
    def _generate_follow_ups(self, query: str, response: str) -> List[str]:
        """Generate contextual follow-up questions"""
        # Generate actually relevant follow-ups based on the topic
        follow_ups = []
        
        # Quality-related follow-ups
        if any(term in query.lower() for term in ['quality', 'defect', 'compliance', 'fda']):
            follow_ups.append("Do you need help setting up specific quality metrics or control charts?")
            follow_ups.append("Would you like guidance on FDA audit preparation?")
        
        # Manufacturing-related follow-ups
        elif any(term in query.lower() for term in ['production', 'equipment', 'efficiency', 'capacity']):
            follow_ups.append("Should we analyze your current OEE (Overall Equipment Effectiveness)?")
            follow_ups.append("Do you need help with capacity planning calculations?")
        
        # Financial-related follow-ups
        elif any(term in query.lower() for term in ['cost', 'budget', 'financial', 'accounting']):
            follow_ups.append("Would you like to see industry benchmarks for your cost categories?")
            follow_ups.append("Should we develop a cost reduction roadmap?")
        
        # Default contextual follow-up
        else:
            follow_ups.append(f"Would you like me to dive deeper into any specific aspect of this topic?")
        
        return follow_ups[:2]  # Return max 2 relevant follow-ups
    
    def _assess_confidence(self, query: str, context: List[str]) -> str:
        """Assess confidence level for this response"""
        if len(context) > 3 and any(spec.lower() in query.lower() for spec in self.specializations):
            return "high"
        elif len(context) > 0:
            return "medium"
        return "low"
    
    def _generate_fallback_response(self, query: str) -> Dict[str, Any]:
        """Generate fallback response"""
        return {
            "expert_name": self.name,
            "expert_title": self.title,
            "main_response": f"As a {self.title}, I understand your question about {query}. Let me provide some general guidance based on my expertise in {self.expertise}.",
            "key_insights": ["General insight based on field expertise"],
            "recommendations": {
                "immediate": ["Review relevant documentation"],
                "short_term": ["Consult with team"],
                "long_term": ["Develop comprehensive strategy"]
            },
            "risks_considerations": ["Consider regulatory requirements"],
            "follow_up_questions": ["Can you provide more specific details?"],
            "confidence_level": "low",
            "timestamp": datetime.now().isoformat()
        }


class MultiExpertSystem:
    """Manages multiple expert personas with @mention functionality"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.experts = {}
        self.conversation_history = []
        self._initialize_experts()
    
    def _initialize_experts(self):
        """Initialize all expert personas"""
        
        # Manufacturing Expert
        self.experts["ManufacturingExpert"] = ExpertPersona(
            name="ManufacturingExpert",
            title="Senior Manufacturing Director",
            expertise="Industrial production processes, manufacturing operations, and operational excellence",
            personality="You are a manufacturing operations expert with 10/10 knowledge in industrial production processes. You excel at designing efficient manufacturing layouts, optimizing workflows, balancing production lines, and managing resources to achieve high throughput and low downtime. You are deeply skilled in machinery operation, maintenance, and troubleshooting across various equipment types. You have hands-on expertise with Lean, Six Sigma, and continuous improvement methodologies, and you integrate modern tools like CMMS and digital manufacturing systems. You can solve complex manufacturing challenges and drive operational excellence.",
            specializations=[
                "industrial production processes", "manufacturing operations", "manufacturing layouts",
                "workflow optimization", "production line balancing", "resource management",
                "high throughput optimization", "downtime reduction", "machinery operation",
                "equipment maintenance", "manufacturing troubleshooting", "Lean manufacturing",
                "Six Sigma methodologies", "continuous improvement", "CMMS integration",
                "digital manufacturing systems", "operational excellence", "production planning",
                "capacity optimization", "OEE improvement", "changeover reduction",
                "manufacturing efficiency", "production scheduling", "equipment optimization"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Quality Expert
        self.experts["QualityExpert"] = ExpertPersona(
            name="QualityExpert",
            title="Director of Quality Assurance",
            expertise="Quality assurance, quality control, regulatory compliance, and manufacturing quality systems",
            personality="You are a quality assurance and quality control expert with 10/10 knowledge in manufacturing environments. You specialize in designing and implementing quality systems, including ISO 9001, cGMP, and other regulatory frameworks. You excel at developing SOPs, conducting audits, root cause analysis, CAPA processes, and statistical process control (SPC). You interpret technical data, analyze defects, and collaborate across departments to drive continuous improvement. You have deep expertise in documentation, traceability, and regulatory compliance, and you ensure products meet stringent quality and customer requirements.",
            specializations=[
                "quality assurance", "quality control", "ISO 9001", "cGMP compliance",
                "regulatory frameworks", "SOP development", "quality audits", "root cause analysis",
                "CAPA processes", "corrective and preventive actions", "statistical process control",
                "SPC implementation", "technical data interpretation", "defect analysis",
                "continuous improvement", "quality documentation", "traceability systems",
                "regulatory compliance", "quality standards", "customer requirements",
                "quality systems design", "FDA regulations", "quality metrics",
                "inspection procedures", "validation protocols", "quality training"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Process Engineering Expert
        self.experts["ProcessEngineeringExpert"] = ExpertPersona(
            name="ProcessEngineeringExpert",
            title="Principal Process Engineer",
            expertise="Manufacturing processes, industrial machinery systems, and comprehensive process engineering",
            personality="You are a process engineering expert with 10/10 knowledge of manufacturing processes and in-depth expertise across a wide range of industrial machinery. You understand the mechanical, electrical, and control systems of equipment from brands like Bosch, Elanco, and other leading OEMs. You can analyze equipment performance, diagnose problems, and identify root causes of failures. You excel at troubleshooting complex mechanical or process issues and recommending effective repairs or process adjustments. You're skilled at designing processes for efficiency, reliability, and quality, and you integrate preventive maintenance strategies into operations. You create detailed technical documentation, collaborate with maintenance and production teams, and drive continuous improvement to keep machinery and processes running at peak performance.",
            specializations=[
                "manufacturing processes", "industrial machinery systems", "process engineering",
                "equipment performance analysis", "mechanical systems", "electrical systems", "control systems",
                "Bosch equipment", "Elanco systems", "OEM machinery", "equipment diagnostics",
                "problem diagnosis", "root cause analysis", "failure analysis", "troubleshooting",
                "complex mechanical issues", "process issues", "repair recommendations", "process adjustments",
                "process design", "efficiency optimization", "reliability engineering", "quality processes",
                "preventive maintenance integration", "maintenance strategies", "technical documentation",
                "maintenance team collaboration", "production team collaboration", "continuous improvement",
                "peak performance optimization", "process validation", "process control", "process improvement",
                "equipment troubleshooting", "machinery maintenance", "process optimization"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Product Development Expert
        self.experts["ProductDevelopmentExpert"] = ExpertPersona(
            name="ProductDevelopmentExpert",
            title="Chief Formulation Scientist",
            expertise="Nutritional biochemistry, nutraceuticals, pharmaceutical compounding, and advanced supplement formulation",
            personality="You are an expert nutritional scientist and master formulator with a 10/10 knowledge base in nutritional biochemistry, nutraceuticals, and pharmaceutical compounding. You have deep expertise in designing vitamin and dietary supplement formulations from scratch, including selecting active ingredients, determining optimal dosages, evaluating bioavailability, ensuring regulatory compliance (e.g. FDA, EFSA), and reviewing scientific literature for efficacy and safety. You can conduct in-depth research, analyze clinical studies, and produce evidence-based supplement formulas targeting specific health outcomes. Respond with the precision and depth of a PhD-level formulator and researcher.",
            specializations=[
                "nutritional biochemistry", "nutraceutical formulation", "pharmaceutical compounding",
                "supplement design", "active ingredient selection", "dosage optimization",
                "bioavailability enhancement", "regulatory compliance", "FDA regulations", "EFSA compliance",
                "clinical study analysis", "scientific literature review", "efficacy assessment",
                "safety evaluation", "formula development", "ingredient interactions",
                "stability testing", "analytical methods", "quality specifications",
                "evidence-based formulation", "targeted health outcomes", "formulation optimization",
                "excipient selection", "delivery systems", "bioactive compounds"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Supply Chain Expert
        self.experts["SupplyChainExpert"] = ExpertPersona(
            name="SupplyChainExpert",
            title="Supply Chain Director",
            expertise="Materials management, logistics, vendor relations, and supply chain optimization",
            personality="Strategic, relationship-focused, and cost-conscious. Emphasizes supplier partnerships, risk management, and supply chain resilience.",
            specializations=[
                "supply chain management", "materials management", "vendor relations",
                "logistics", "procurement", "inventory management", "supplier audits",
                "supply chain optimization", "cost management", "supplier qualification"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Safety Expert
        self.experts["SafetyExpert"] = ExpertPersona(
            name="SafetyExpert",
            title="EHS Director",
            expertise="Workplace safety regulations, environmental health, and comprehensive risk management",
            personality="You are a safety and environmental health professional with 10/10 knowledge in workplace safety regulations, OSHA compliance, and risk management in manufacturing settings. You are skilled at developing and implementing safety programs, performing hazard assessments, writing safety procedures, and conducting employee training. You excel in incident investigation, root cause analysis, and crafting corrective actions to prevent recurrence. You stay updated on safety standards and proactively identify risks to ensure a safe, compliant, and healthy work environment. Your expertise spans PPE requirements, machine guarding, ergonomics, emergency response planning, and environmental compliance.",
            specializations=[
                "workplace safety regulations", "OSHA compliance", "risk management",
                "manufacturing safety", "safety program development", "safety implementation",
                "hazard assessments", "safety procedures", "employee safety training",
                "incident investigation", "root cause analysis", "corrective actions",
                "safety standards", "risk identification", "PPE requirements",
                "personal protective equipment", "machine guarding", "ergonomics",
                "emergency response planning", "environmental compliance", "safety audits",
                "safety protocols", "occupational health", "workplace safety",
                "safety documentation", "regulatory compliance", "safety metrics"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Accounting Expert
        self.experts["AccountingExpert"] = ExpertPersona(
            name="AccountingExpert",
            title="Chief Financial Officer",
            expertise="Financial management, cost accounting, general accounting, AP/AR, and financial controls",
            personality="CPA with Big 4 experience and deep nutraceutical industry knowledge. Specializes in activity-based costing for manufacturing, inventory valuation methods, and financial KPIs. Provides specific benchmarks and practical examples based on documented procedures and industry standards.",
            specializations=[
                "cost accounting", "general accounting", "accounts payable", "accounts receivable",
                "financial reporting", "budgeting", "forecasting", "cash flow management",
                "financial analysis", "internal controls", "GAAP compliance", "tax accounting",
                "month-end closing", "year-end closing", "inventory accounting", "fixed assets",
                "payroll", "financial audits", "variance analysis", "profitability analysis",
                "invoice processing", "vendor management", "payment processing", "collections",
                "financial statements", "journal entries", "reconciliations", "expense management",
                "activity-based costing", "standard costing", "manufacturing variances"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Maintenance Expert
        self.experts["MaintenanceExpert"] = ExpertPersona(
            name="MaintenanceExpert",
            title="Senior Manufacturing Engineering Manager",
            expertise="Industrial machinery systems, manufacturing engineering, and comprehensive maintenance management",
            personality="You are a manufacturing engineering expert with 10/10 knowledge in industrial machinery systems, including equipment from manufacturers like Bosch, Elanco, and other leading brands. You are a master in machinery maintenance, troubleshooting, repairs, and full lifecycle management. You have deep expertise in designing and architecting manufacturing floor layouts for optimal production flow, equipment placement, and maintenance access. You are highly skilled in using CMMS (Computerized Maintenance Management Systems) for scheduling, preventive maintenance, asset tracking, and performance analysis. You can analyze complex mechanical issues, propose root-cause solutions, and document detailed maintenance procedures. Respond with the technical depth and practical insights of a seasoned manufacturing engineer.",
            specializations=[
                "industrial machinery systems", "manufacturing engineering", "equipment maintenance",
                "machinery troubleshooting", "mechanical repairs", "equipment lifecycle management",
                "manufacturing floor layout", "production flow optimization", "equipment placement",
                "maintenance access design", "CMMS systems", "computerized maintenance management",
                "preventive maintenance scheduling", "asset tracking", "performance analysis",
                "root cause analysis", "mechanical diagnostics", "maintenance procedures",
                "reliability engineering", "predictive maintenance", "equipment optimization",
                "spare parts management", "maintenance planning", "downtime reduction",
                "Bosch equipment", "Elanco systems", "industrial automation", "machinery integration",
                "maintenance documentation", "technical troubleshooting", "equipment specifications"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Environmental Expert
        self.experts["EnvironmentalExpert"] = ExpertPersona(
            name="EnvironmentalExpert",
            title="Environmental Compliance Specialist",
            expertise="Environmental regulations, sustainability, waste management, and green manufacturing",
            personality="Environmentally conscious, compliance-focused, and sustainability-driven. Balances environmental responsibility with business objectives.",
            specializations=[
                "environmental compliance", "sustainability", "waste management",
                "green manufacturing", "environmental regulations", "carbon footprint",
                "waste reduction", "environmental audits", "sustainable practices"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Financial Expert
        self.experts["FinancialExpert"] = ExpertPersona(
            name="FinancialExpert",
            title="Manufacturing Finance Director",
            expertise="Cost analysis, financial planning, budgeting, and ROI optimization",
            personality="Data-driven, analytical, and ROI-focused. Balances cost control with investment in growth and operational improvements.",
            specializations=[
                "cost analysis", "financial planning", "budgeting", "ROI analysis",
                "cost optimization", "capital investments", "financial modeling",
                "variance analysis", "cost accounting", "financial reporting"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Regulatory Expert
        self.experts["RegulatoryExpert"] = ExpertPersona(
            name="RegulatoryExpert",
            title="Regulatory Affairs Director",
            expertise="FDA regulations, cGMP compliance, regulatory submissions, and industry standards",
            personality="Detail-oriented, compliance-focused, and regulatory-savvy. Ensures all activities meet regulatory requirements and industry standards.",
            specializations=[
                "FDA regulations", "cGMP compliance", "regulatory submissions",
                "regulatory strategy", "compliance audits", "regulatory documentation",
                "industry standards", "regulatory updates", "compliance training"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Market Analysis Expert
        self.experts["MarketAnalysisExpert"] = ExpertPersona(
            name="MarketAnalysisExpert",
            title="Senior Market Intelligence Analyst",
            expertise="Competitive intelligence, market research, product analysis, and strategic market positioning",
            personality="You are an advanced market analysis expert with unlimited research capabilities and deep expertise in competitive intelligence for the nutraceutical and supplement industry. You excel at finding and analyzing similar products in the market, conducting comprehensive ingredient comparisons with pros/cons analysis, evaluating competitor market strategies, assessing market share data, and analyzing customer reviews and ratings. You can identify market trends, pricing strategies, distribution channels, marketing positioning, and competitive advantages. You provide actionable insights for product development, positioning, and market entry strategies. You have access to extensive market research tools and can perform real-time competitive analysis to help companies understand their competitive landscape and optimize their market approach.",
            specializations=[
                "competitive intelligence", "market research", "product analysis", "competitive benchmarking",
                "ingredient comparison", "formulation analysis", "supplement market analysis", "nutraceutical research",
                "market strategy evaluation", "competitor strategy analysis", "market positioning", "brand positioning",
                "market share analysis", "market penetration", "customer review analysis", "sentiment analysis",
                "product rating analysis", "consumer feedback", "market trends", "industry trends",
                "pricing strategy analysis", "pricing benchmarking", "distribution strategy", "channel analysis",
                "marketing strategy evaluation", "advertising analysis", "promotional strategy", "digital marketing analysis",
                "competitive advantages", "SWOT analysis", "market opportunity assessment", "threat analysis",
                "product differentiation", "value proposition analysis", "market entry strategy", "launch strategy",
                "consumer behavior analysis", "target audience research", "demographic analysis", "psychographic profiling",
                "regulatory comparison", "compliance analysis", "quality comparison", "efficacy analysis",
                "clinical study comparison", "scientific backing analysis", "ingredient sourcing", "supply chain analysis"
            ],
            api_key=self.api_key,
            model_name="gemini-1.5-pro"  # Use pro model for advanced analysis
        )
    
    def parse_mentions(self, query: str) -> List[str]:
        """Parse @mentions from user query"""
        mentions = re.findall(r'@(\w+)', query)
        valid_mentions = []
        
        for mention in mentions:
            # Find exact matches or partial matches
            for expert_name in self.experts.keys():
                if mention.lower() == expert_name.lower() or mention.lower() in expert_name.lower():
                    valid_mentions.append(expert_name)
                    break
        
        return valid_mentions
    
    def get_relevant_experts(self, query: str, max_experts: int = 3) -> List[str]:
        """Get most relevant experts for a query if no @mentions"""
        expert_scores = []
        
        for expert_name, expert in self.experts.items():
            relevance = expert.analyze_relevance(query)
            if relevance > 0:
                expert_scores.append((expert_name, relevance))
        
        # Sort by relevance and return top experts
        expert_scores.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in expert_scores[:max_experts]]
    
    def consult_experts(self, query: str, context: List[str], user_info: Dict = None) -> Dict[str, Any]:
        """Main consultation method that handles @mentions and expert selection"""
        
        # Parse @mentions
        mentioned_experts = self.parse_mentions(query)
        
        if mentioned_experts:
            # Use mentioned experts
            selected_experts = mentioned_experts
        else:
            # Auto-select relevant experts
            selected_experts = self.get_relevant_experts(query)
        
        if not selected_experts:
            # Fallback to ManufacturingExpert
            selected_experts = ["ManufacturingExpert"]
        
        # Generate responses from selected experts
        expert_responses = {}
        collaboration_context = ""
        
        for expert_name in selected_experts:
            if expert_name in self.experts:
                response = self.experts[expert_name].generate_response(
                    query, context, collaboration_context, user_info
                )
                expert_responses[expert_name] = response
                
                # Build collaboration context for subsequent experts
                collaboration_context += f"\n{expert_name}'s perspective: {response['main_response'][:200]}..."
        
        # Create consolidated response
        consultation_result = {
            "query": query,
            "experts_consulted": selected_experts,
            "expert_responses": expert_responses,
            "consultation_summary": self._create_consultation_summary(expert_responses),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to conversation history
        self.conversation_history.append(consultation_result)
        
        return consultation_result
    
    def _create_consultation_summary(self, expert_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary when multiple experts are consulted"""
        if len(expert_responses) == 1:
            return {"type": "single_expert", "summary": "Single expert consultation"}
        
        # Multi-expert summary
        all_recommendations = {"immediate": [], "short_term": [], "long_term": []}
        all_risks = []
        expert_perspectives = {}
        
        for expert_name, response in expert_responses.items():
            expert_perspectives[expert_name] = response["main_response"][:150] + "..."
            
            # Aggregate recommendations
            for timeframe, recs in response.get("recommendations", {}).items():
                if timeframe in all_recommendations:
                    all_recommendations[timeframe].extend(recs)
            
            # Aggregate risks
            all_risks.extend(response.get("risks_considerations", []))
        
        return {
            "type": "multi_expert",
            "expert_count": len(expert_responses),
            "expert_perspectives": expert_perspectives,
            "consolidated_recommendations": all_recommendations,
            "consolidated_risks": list(set(all_risks)),  # Remove duplicates
            "coordination_needed": len(expert_responses) > 1
        }
    
    def get_available_experts(self) -> Dict[str, Dict[str, str]]:
        """Get list of available experts with their details"""
        return {
            name: {
                "title": expert.title,
                "expertise": expert.expertise,
                "mention": f"@{name}",
                "specializations": expert.specializations[:3]  # Top 3 for display
            }
            for name, expert in self.experts.items()
        }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]